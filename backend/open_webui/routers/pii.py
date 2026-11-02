"""
GovChat-NL: API voor het persoonsgegevensfilter.

- POST /detect: treffers in een tekst (voor de pop-up)
- POST /mask:   tekst met gemaskeerde treffers (behalve de uitgevinkte)
- POST /files/{id}/detect: treffers in de tekst van een geüpload bestand
- POST /files/{id}/mask:   tekst van het bestand blijvend maskeren en opnieuw indexeren
- GET/POST /config: instellingen voor de beheerder
"""

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from open_webui.constants import ERROR_MESSAGES
from open_webui.internal.db import get_async_session
from open_webui.models.config import Config
from open_webui.models.files import Files
from open_webui.utils.access_control.files import has_access_to_file
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.pii import CATEGORIES, LABELS, MODES, detect, detect_long, mask, segments
from open_webui.utils.pii.enforcement import get_pii_config

log = logging.getLogger(__name__)

router = APIRouter()

# Maximale tekstlengte die gecontroleerd wordt (voorkomt dat heel lange plaktekst de server ophoudt)
MAX_TEXT_LENGTH = 100_000


class TextForm(BaseModel):
    text: str = Field(max_length=MAX_TEXT_LENGTH)


class MaskForm(TextForm):
    # Indexen (uit /detect) van treffers die de gebruiker heeft uitgevinkt
    exclude: list[int] = []


class FileMaskForm(BaseModel):
    exclude: list[int] = []


class PiiConfigForm(BaseModel):
    ENABLE_PII_FILTER: bool
    PII_FILTER_DEFAULT_MODE: str
    PII_FILTER_CATEGORIES: list[str]


def _serialize(findings) -> list[dict]:
    return [
        {
            'index': idx,
            'category': f.category,
            'label': LABELS.get(f.category),
            'text': f.text,
            'maskable': f.maskable,
            'detail': f.detail,
        }
        for idx, f in enumerate(findings)
    ]


@router.post('/detect')
async def detect_pii(form_data: TextForm, user=Depends(get_verified_user)):
    config = await get_pii_config()
    if not config['enable'] or not form_data.text.strip():
        return {'enabled': config['enable'], 'findings': [], 'segments': [{'text': form_data.text}]}

    findings = await asyncio.to_thread(detect, form_data.text, config['categories'])
    return {
        'enabled': True,
        'findings': _serialize(findings),
        'segments': segments(form_data.text, findings),
    }


@router.post('/mask')
async def mask_pii(form_data: MaskForm, user=Depends(get_verified_user)):
    config = await get_pii_config()
    if not config['enable']:
        return {'text': form_data.text, 'replacements': []}

    findings = await asyncio.to_thread(detect, form_data.text, config['categories'])
    excluded = set(form_data.exclude)
    selected = [f for idx, f in enumerate(findings) if idx not in excluded]
    text, replacements = mask(form_data.text, selected)
    return {'text': text, 'replacements': replacements}


# Bestanden: tekens rond een treffer die de pop-up laat zien
CONTEXT_CHARS = 40
# Bij grote bestanden tonen we niet alle treffers in de pop-up
MAX_FILE_FINDINGS = 200


def _with_context(text: str, findings) -> list[dict]:
    out = _serialize(findings)
    for item, f in zip(out, findings):
        item['before'] = text[max(0, f.start - CONTEXT_CHARS) : f.start].lstrip()
        item['after'] = text[f.end : f.end + CONTEXT_CHARS].rstrip()
    return out


async def _get_file_content(id: str, user, permission: str, db: AsyncSession):
    file = await Files.get_file_by_id(id, db=db)
    if not file or not (
        file.user_id == user.id or user.role == 'admin' or await has_access_to_file(id, permission, user, db=db)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ERROR_MESSAGES.NOT_FOUND)
    return file, (file.data or {}).get('content') or ''


@router.post('/files/{id}/detect')
async def detect_pii_in_file(id: str, user=Depends(get_verified_user), db: AsyncSession = Depends(get_async_session)):
    config = await get_pii_config()
    file, content = await _get_file_content(id, user, 'read', db)
    masked_before = bool((file.meta or {}).get('pii_masked'))
    if not config['enable'] or not content.strip():
        return {'enabled': config['enable'], 'findings': [], 'total': 0, 'masked': masked_before}

    findings = await asyncio.to_thread(detect_long, content, config['categories'])
    return {
        'enabled': True,
        'findings': _with_context(content, findings[:MAX_FILE_FINDINGS]),
        'total': len(findings),
        'masked': masked_before,
    }


@router.post('/files/{id}/mask')
async def mask_pii_in_file(
    request: Request,
    id: str,
    form_data: FileMaskForm,
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Vervang de persoonsgegevens in de tekst van het bestand. De gemaskeerde
    tekst wordt opnieuw geïndexeerd, zodat chat, kennisbanken en tools alleen
    nog de gefilterde versie zien. Het originele bestand zelf blijft bewaard.
    """
    # Hier pas importeren: de bestandsrouter laadt veel (vectordatabase, audio)
    from open_webui.routers.files import ContentForm, update_file_data_content_by_id

    config = await get_pii_config()
    _, content = await _get_file_content(id, user, 'write', db)
    if not config['enable'] or not content.strip():
        return {'replacements': 0, 'content': content}

    findings = await asyncio.to_thread(detect_long, content, config['categories'])
    excluded = set(form_data.exclude)
    selected = [f for idx, f in enumerate(findings) if idx not in excluded]
    masked, replacements = mask(content, selected)
    if replacements:
        await update_file_data_content_by_id(request, id, ContentForm(content=masked), user=user, db=db)
    await Files.update_file_metadata_by_id(id, {'pii_masked': True}, db=db)
    log.info('PII-filter: %d persoonsgegevens in bestand %s gemaskeerd', len(replacements), id)
    # De frontend zet de tekst terug in het bestand van de chat: bij 'volledige context'
    # stuurt die de tekst zelf mee
    return {'replacements': len(replacements), 'content': masked}


@router.get('/config')
async def get_config(user=Depends(get_admin_user)):
    config = await get_pii_config()
    return {
        'ENABLE_PII_FILTER': config['enable'],
        'PII_FILTER_DEFAULT_MODE': config['default_mode'],
        'PII_FILTER_CATEGORIES': config['categories'],
        'AVAILABLE_CATEGORIES': CATEGORIES,
    }


@router.post('/config')
async def set_config(form_data: PiiConfigForm, user=Depends(get_admin_user)):
    await Config.upsert(
        {
            'pii.enable': form_data.ENABLE_PII_FILTER,
            'pii.default_mode': form_data.PII_FILTER_DEFAULT_MODE
            if form_data.PII_FILTER_DEFAULT_MODE in MODES
            else 'warn',
            'pii.categories': [c for c in form_data.PII_FILTER_CATEGORIES if c in CATEGORIES],
        }
    )
    return await get_config(user)
