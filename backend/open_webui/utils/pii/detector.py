"""
GovChat-NL: detectie en maskering van persoonsgegevens.

detect() geeft treffers terug zonder overlap. mask() vervangt geselecteerde
treffers door labels zoals [BSN] of [NAAM 1]. Dezelfde waarde krijgt in een
bericht steeds hetzelfde label, zodat het taalmodel de tekst nog begrijpt.
"""

import re

from open_webui.utils.pii.names import find_names
from open_webui.utils.pii.recognizers import RECOGNIZERS, Finding

# Categorieën zoals de beheerder ze aan- en uitzet
CATEGORIES = [
    'bsn',
    'iban',
    'geboortedatum',
    'naam',
    'email',
    'telefoon',
    'adres',
    'id_document',
    'kenteken',
    'creditcard',
    'ip_adres',
    'bijzonder',
]

# Sommige herkenners leveren treffers met een eigen, specifiekere categorie
CATEGORY_GROUP = {
    'postcode': 'adres',
    'rijbewijs': 'id_document',
    'v_nummer': 'id_document',
}

LABELS = {
    'bsn': 'BSN',
    'iban': 'IBAN',
    'geboortedatum': 'GEBOORTEDATUM',
    'naam': 'NAAM',
    'email': 'E-MAIL',
    'telefoon': 'TELEFOON',
    'adres': 'ADRES',
    'postcode': 'POSTCODE',
    'id_document': 'DOCUMENTNUMMER',
    'rijbewijs': 'RIJBEWIJSNUMMER',
    'v_nummer': 'V-NUMMER',
    'kenteken': 'KENTEKEN',
    'creditcard': 'CREDITCARD',
    'ip_adres': 'IP-ADRES',
}

MODES = ['off', 'warn', 'mask']

# Labels die we zelf invoegen worden nooit opnieuw herkend
_LABEL_RE = re.compile(r'\[(?:' + '|'.join(re.escape(v) for v in set(LABELS.values())) + r')(?: \d+)?\]')


def _resolve_overlaps(findings: list[Finding]) -> list[Finding]:
    """Houd per overlappend stuk tekst de treffer met de hoogste prioriteit (daarna de langste)."""
    maskable = sorted(
        (f for f in findings if f.maskable),
        key=lambda f: (-f.priority, -(f.end - f.start), f.start),
    )
    kept: list[Finding] = []
    for f in maskable:
        if all(f.end <= k.start or f.start >= k.end for k in kept):
            kept.append(f)

    # Waarschuwingen (bijzondere persoonsgegevens) alleen buiten maskeerbare treffers
    warnings = [f for f in findings if not f.maskable and all(f.end <= k.start or f.start >= k.end for k in kept)]
    seen = set()
    unique_warnings = []
    for f in sorted(warnings, key=lambda f: f.start):
        if (f.start, f.end) not in seen:
            seen.add((f.start, f.end))
            unique_warnings.append(f)

    return sorted(kept + unique_warnings, key=lambda f: f.start)


def detect(text: str, categories: list[str] | None = None) -> list[Finding]:
    enabled = set(categories if categories is not None else CATEGORIES)
    findings: list[Finding] = []

    for key, recognizer in RECOGNIZERS.items():
        if key in enabled:
            findings += recognizer(text)
    if 'naam' in enabled:
        findings += find_names(text)

    # Treffers binnen al ingevoegde labels negeren
    label_spans = [(m.start(), m.end()) for m in _LABEL_RE.finditer(text)]
    findings = [
        f
        for f in findings
        if CATEGORY_GROUP.get(f.category, f.category) in enabled
        and not any(f.start < e and f.end > s for s, e in label_spans)
    ]
    return _resolve_overlaps(findings)


# Lange teksten (bijv. een PDF) in stukken controleren, zodat spaCy niet vastloopt
CHUNK_SIZE = 20_000


def detect_long(text: str, categories: list[str] | None = None, chunk_size: int = CHUNK_SIZE) -> list[Finding]:
    """Zoals detect(), maar knipt lange teksten op alinea- of regelgrenzen."""
    if len(text) <= chunk_size:
        return detect(text, categories)

    findings: list[Finding] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Liefst bij een witregel of regeleinde knippen, anders bij een spatie
            for sep in ('\n\n', '\n', ' '):
                cut = text.rfind(sep, start + chunk_size // 2, end)
                if cut != -1:
                    end = cut + len(sep)
                    break
        for f in detect(text[start:end], categories):
            f.start += start
            f.end += start
            findings.append(f)
        start = end
    return findings


def _normalize(value: str) -> str:
    return re.sub(r'[\s.\-]', '', value).lower()


def mask(text: str, findings: list[Finding]) -> tuple[str, list[dict]]:
    """
    Vervang de maskeerbare treffers door labels. Geeft de nieuwe tekst terug
    en een lijst van vervangingen (zonder de originele waarde).
    """
    findings = sorted((f for f in findings if f.maskable), key=lambda f: f.start)

    # Nummering per categorie: namen altijd genummerd, andere categorieën
    # alleen als er meer dan één verschillende waarde is
    distinct: dict[str, list[str]] = {}
    for f in findings:
        values = distinct.setdefault(f.category, [])
        norm = _normalize(f.text)
        if norm not in values:
            values.append(norm)

    def label_for(f: Finding) -> str:
        base = LABELS.get(f.category, f.category.upper())
        values = distinct[f.category]
        if f.category == 'naam' or len(values) > 1:
            return f'[{base} {values.index(_normalize(f.text)) + 1}]'
        return f'[{base}]'

    parts, replacements, pos = [], [], 0
    for f in findings:
        if f.start < pos:
            continue
        label = label_for(f)
        parts.append(text[pos : f.start])
        parts.append(label)
        replacements.append({'category': f.category, 'label': label})
        pos = f.end
    parts.append(text[pos:])
    return ''.join(parts), replacements


def detect_and_mask(text: str, categories: list[str] | None = None) -> tuple[str, list[dict]]:
    return mask(text, detect(text, categories))


def segments(text: str, findings: list[Finding]) -> list[dict]:
    """
    Knip de tekst in stukken voor weergave in de pop-up. Zo hoeft de frontend
    niet met tekenposities te rekenen (Python- en JavaScript-posities verschillen
    bij emoji).
    """
    out, pos = [], 0
    for idx, f in enumerate(findings):
        if f.start < pos:
            continue
        if f.start > pos:
            out.append({'text': text[pos : f.start]})
        out.append({'text': text[f.start : f.end], 'finding': idx})
        pos = f.end
    if pos < len(text):
        out.append({'text': text[pos:]})
    return out
