"""
GovChat-NL: herkenning van persoonsnamen.

Gebruikt het lokale Nederlandse spaCy-model (nl_core_news_md) voor
named-entity recognition. Het model draait volledig op de eigen server.
Daarnaast:
- een aanspreekvorm ("mevrouw", "dhr.") gevolgd door woorden met een
  hoofdletter geldt altijd als naam;
- een door spaCy gevonden naam wordt naar links uitgebreid met tussenvoegsels
  en voornamen ("Fatima el Amrani" in plaats van alleen "Amrani");
- spaCy krijgt de tekst per zin. Het model draait zonder zinsherkenning en
  plakt anders soms twee zinnen aan elkaar tot één organisatienaam, waardoor
  een persoon in de tweede zin gemist wordt.
"""

import logging
import re
import threading

from open_webui.utils.pii.recognizers import Finding

log = logging.getLogger(__name__)

SPACY_MODEL = 'nl_core_news_md'

_nlp = None
_nlp_failed = False
_lock = threading.Lock()

TITLES = {
    'mevrouw',
    'mevr',
    'mw',
    'meneer',
    'mijnheer',
    'dhr',
    'heer',
    'mr',
    'mrs',
    'ms',
    'dr',
    'drs',
    'ir',
    'ing',
    'prof',
    'juffrouw',
    'juf',
    'meester',
    'zuster',
    'broeder',
    'familie',
    'fam',
}
PARTICLES = {
    'van',
    'de',
    'der',
    'den',
    'het',
    "'t",
    'te',
    'ter',
    'ten',
    'op',
    'in',
    'el',
    'al',
    'bin',
    'ben',
    'da',
    'di',
    'du',
    'la',
    'le',
    'von',
    'zu',
    'vd',
    'v.d.',
}

# Afkortingen van wetten en organisaties die spaCy soms als naam ziet
NOT_NAMES = {
    'woo',
    'wob',
    'wmo',
    'awb',
    'wabo',
    'wro',
    'wkb',
    'wbp',
    'uavg',
    'avg',
    'ggd',
    'ggz',
    'uwv',
    'duo',
    'cbs',
    'ind',
    'rvo',
    'rws',
    'kvk',
    'cjib',
    'ipo',
    'vng',
    'unie',
    'excel',
    'teams',
    'outlook',
    'word',
}

_WORD = r"[A-ZÀ-Ý][\w'’-]+"
_PARTICLE = r'(?:' + '|'.join(re.escape(p) for p in sorted(PARTICLES, key=len, reverse=True)) + r')'
# Alleen de aanspreekvorm is hoofdletterongevoelig; de naam zelf moet met hoofdletters
TITLE_NAME_RE = re.compile(
    r'\b(?i:' + '|'.join(sorted(TITLES, key=len, reverse=True)) + r')\.?\s+'
    rf'((?:{_WORD}|[A-Z]\.)(?:\s+(?:{_PARTICLE}\s+)*(?:{_WORD}|[A-Z]\.))*)'
)


def get_nlp():
    """Laadt het spaCy-model één keer; None als het niet beschikbaar is."""
    global _nlp, _nlp_failed
    if _nlp is not None or _nlp_failed:
        return _nlp
    with _lock:
        if _nlp is None and not _nlp_failed:
            try:
                import spacy

                _nlp = spacy.load(
                    SPACY_MODEL,
                    exclude=['parser', 'lemmatizer', 'morphologizer', 'tagger', 'attribute_ruler', 'senter'],
                )
                log.info('PII-filter: spaCy-model %s geladen', SPACY_MODEL)
            except Exception as e:
                _nlp_failed = True
                log.warning(
                    'PII-filter: spaCy-model %s niet beschikbaar, namen worden niet herkend: %s', SPACY_MODEL, e
                )
    return _nlp


def _is_capitalized(token_text: str) -> bool:
    # Woord met hoofdletter ("Fatima") of voorletter ("P.")
    return (token_text[:1].isupper() and not token_text.isupper()) or bool(re.fullmatch(r'[A-Z]\.', token_text))


def _extend_left(doc, start: int) -> int:
    """Breid een naam naar links uit met tussenvoegsels en voornamen."""
    i = start - 1
    while i >= 0:
        tok = doc[i]
        lower = tok.text.lower().rstrip('.')
        if lower in TITLES:
            break
        if tok.text.lower() in PARTICLES:
            i -= 1
            continue
        if _is_capitalized(tok.text):
            prev = doc[i - 1] if i > 0 else None
            sentence_start = prev is None or prev.text in {'.', '!', '?', ':', '\n'} or prev.is_space
            preceded_by_title = prev is not None and prev.text.lower().rstrip('.') in TITLES
            if sentence_start and not preceded_by_title:
                break
            i -= 1
            continue
        break
    # Begin nooit met een los tussenvoegsel
    j = i + 1
    while j < start and doc[j].text.lower() in PARTICLES and not doc[j].text[:1].isupper():
        j += 1
    return j


# Afkortingen waarna een punt geen zinseinde is
ABBREVIATIONS = {'bijv', 'bv', 'evt', 'ca', 'nr', 'tel', 'zgn', 'resp', 'jl', 'st', 'mgr', 'ds'}
_BREAK_RE = re.compile(r'([.!?])\s+|\n+')


def _sentences(text: str):
    """Knip de tekst in zinnen en regels, met de beginpositie van elk stuk."""
    start = 0
    for m in _BREAK_RE.finditer(text):
        if m.group(1):
            before = re.search(r'(\S+)$', text[start : m.start()])
            word = before.group(1).lower() if before else ''
            # Geen zinseinde na een voorletter (J.M.), aanspreekvorm (dhr.) of afkorting (bijv.)
            if len(word) <= 1 or '.' in word or word in TITLES or word in ABBREVIATIONS:
                continue
        end = m.start() + (1 if m.group(1) else 0)
        if text[start:end].strip():
            yield start, text[start:end]
        start = m.end()
    if text[start:].strip():
        yield start, text[start:]


def find_names(text: str) -> list[Finding]:
    findings = []

    for m in TITLE_NAME_RE.finditer(text):
        findings.append(Finding('naam', m.start(1), m.end(1), m.group(1), priority=30))

    nlp = get_nlp()
    if nlp is not None:
        pieces = list(_sentences(text))
        for (offset, _), doc in zip(pieces, nlp.pipe(piece for _, piece in pieces)):
            findings += _names_in_doc(doc, offset)

    return findings


def _names_in_doc(doc, offset: int) -> list[Finding]:
    """Persoonsnamen uit één door spaCy verwerkt stuk tekst."""
    findings = []
    for ent in doc.ents:
        if ent.label_ != 'PERSON':
            continue
        start_tok = _extend_left(doc, ent.start)
        span = doc[start_tok : ent.end]
        value = span.text.strip(' .,:;\'"')
        # Afkortingen (BSN, IBAN, AVG) en woorden met cijfers zijn geen namen
        if (
            len(value) < 2
            or not any(c.isupper() for c in value)
            or value.isupper()
            or any(c.isdigit() for c in value)
            or value.lower() in NOT_NAMES
        ):
            continue
        start = offset + span.start_char + span.text.find(value)
        findings.append(Finding('naam', start, start + len(value), value, priority=30))

    return findings
