"""
GovChat-NL: instellingen van het persoonsgegevensfilter bepalen en de modus
"Altijd filteren" op de server afdwingen: in berichten, in de tekst van
bestanden en kennisbanken die als context meegaan, en in de resultaten van
de ingebouwde bestandstools.

Volgorde: de beheerder zet het filter aan of uit (pii.enable). Staat het aan,
dan geldt de modus van de agent (model meta 'pii_filter'), anders de
standaardmodus van de beheerder. "Altijd filteren" (mask) van de agent of
van de beheerder is bindend: een chat kan die niet uitzetten.
"""

import asyncio
import json
import logging
from typing import Any

from open_webui.utils.pii.detector import CATEGORIES, MODES, detect_and_mask, detect_long, mask

# Ingebouwde tools die tekst uit bestanden of kennisbanken teruggeven
FILE_TOOL_NAMES = {
    'view_file',
    'view_knowledge_file',
    'query_knowledge_files',
    'query_knowledge_bases',
    'query_chat_files',
    'grep_chat_files',
    'grep_knowledge_files',
}

log = logging.getLogger(__name__)


async def get_pii_config() -> dict:
    # Hier pas importeren: zo blijft de detector zonder database te testen
    from open_webui.models.config import Config

    values = await Config.get_many('pii.enable', 'pii.default_mode', 'pii.categories')
    categories = values.get('pii.categories')
    return {
        'enable': bool(values.get('pii.enable')),
        'default_mode': values.get('pii.default_mode') if values.get('pii.default_mode') in MODES else 'warn',
        'categories': [c for c in categories if c in CATEGORIES] if isinstance(categories, list) else list(CATEGORIES),
    }


def get_model_pii_mode(model: dict | None) -> str | None:
    mode = ((model or {}).get('info') or {}).get('meta', {}).get('pii_filter')
    return mode if mode in MODES else None


async def is_mask_enforced(model: dict | None, config: dict | None = None) -> bool:
    config = config or await get_pii_config()
    if not config['enable']:
        return False
    agent_mode = get_model_pii_mode(model)
    return agent_mode == 'mask' or (agent_mode is None and config['default_mode'] == 'mask')


def _mask_message(message: dict, categories: list[str]) -> int:
    content = message.get('content')
    count = 0
    if isinstance(content, str):
        masked, replacements = detect_and_mask(content, categories)
        message['content'] = masked
        count += len(replacements)
    elif isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get('type') == 'text' and isinstance(part.get('text'), str):
                masked, replacements = detect_and_mask(part['text'], categories)
                part['text'] = masked
                count += len(replacements)
    return count


async def enforce_pii_mask(messages: list[dict], model: dict | None) -> list[dict]:
    """Maskeer alle gebruikersberichten als de modus 'Altijd filteren' bindend is."""
    config = await get_pii_config()
    if not await is_mask_enforced(model, config):
        return messages

    def run():
        return sum(_mask_message(m, config['categories']) for m in messages if m.get('role') == 'user')

    count = await asyncio.to_thread(run)
    if count:
        log.info('PII-filter: %d persoonsgegevens op de server gemaskeerd', count)
    return messages


def mask_text(text: str, categories: list[str]) -> tuple[str, int]:
    masked, replacements = mask(text, detect_long(text, categories))
    return masked, len(replacements)


async def mask_sources(sources: list[dict], categories: list[str]) -> list[dict]:
    """Maskeer de tekst van bestanden en kennisbanken die als context meegaan."""

    def run():
        count = 0
        for source in sources:
            documents = source.get('document')
            if not isinstance(documents, list):
                continue
            for idx, doc in enumerate(documents):
                if isinstance(doc, str) and doc.strip():
                    documents[idx], n = mask_text(doc, categories)
                    count += n
        return count

    count = await asyncio.to_thread(run)
    if count:
        log.info('PII-filter: %d persoonsgegevens in bestandscontext gemaskeerd', count)
    return sources


def _mask_value(value: Any, categories: list[str]) -> tuple[Any, int]:
    if isinstance(value, str):
        return mask_text(value, categories) if value.strip() else (value, 0)
    if isinstance(value, list):
        count = 0
        for idx, item in enumerate(value):
            value[idx], n = _mask_value(item, categories)
            count += n
        return value, count
    if isinstance(value, dict):
        count = 0
        for key, item in value.items():
            value[key], n = _mask_value(item, categories)
            count += n
        return value, count
    return value, 0


async def mask_tool_result(tool_result: Any, categories: list[str]) -> Any:
    """
    Maskeer het resultaat van een bestandstool. JSON wordt per tekstveld
    gemaskeerd, zodat de structuur intact blijft.
    """

    def run():
        if isinstance(tool_result, str):
            try:
                parsed = json.loads(tool_result)
            except (TypeError, ValueError):
                parsed = None
            if isinstance(parsed, (dict, list)):
                masked, count = _mask_value(parsed, categories)
                return json.dumps(masked, ensure_ascii=False), count
        return _mask_value(tool_result, categories)

    masked, count = await asyncio.to_thread(run)
    if count:
        log.info('PII-filter: %d persoonsgegevens in toolresultaat gemaskeerd', count)
    return masked
