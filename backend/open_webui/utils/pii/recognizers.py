"""
GovChat-NL: herkenners voor persoonsgegevens.

Elke herkenner krijgt de volledige tekst en geeft een lijst Finding-objecten
terug. Waar mogelijk wordt een treffer gecontroleerd (11-proef, mod-97, Luhn,
geldige datum) of is context nodig (bijv. "geboren" voor een geboortedatum),
om valse treffers te beperken.
"""

import ipaddress
import re
from dataclasses import dataclass, field
from datetime import date

# Hoe ver (in tekens) vóór een treffer naar contextwoorden gezocht wordt
CONTEXT_WINDOW = 60


@dataclass
class Finding:
    category: str
    start: int
    end: int
    text: str
    # False = alleen waarschuwen (bijv. bijzondere persoonsgegevens), niet maskeren
    maskable: bool = True
    # Hogere prioriteit wint bij overlap
    priority: int = 0
    detail: str | None = None
    extra: dict = field(default_factory=dict)


def _context_before(text: str, start: int, window: int = CONTEXT_WINDOW) -> str:
    return text[max(0, start - window) : start].lower()


def _has_context(text: str, start: int, pattern: re.Pattern) -> bool:
    return bool(pattern.search(_context_before(text, start)))


def _digits(s: str) -> str:
    return re.sub(r'\D', '', s)


####################################
# BSN (11-proef)
####################################

BSN_RE = re.compile(r'(?<![\d.\-/])(\d{3}[ .]?\d{3}[ .]?\d{3}|\d{9})(?![\d\-/])(?!\.\d)')


def is_valid_bsn(value: str) -> bool:
    digits = _digits(value)
    if len(digits) != 9 or digits == '0' * 9:
        return False
    total = sum(int(d) * w for d, w in zip(digits[:8], range(9, 1, -1))) - int(digits[8])
    return total % 11 == 0


def find_bsn(text: str) -> list[Finding]:
    return [
        Finding('bsn', m.start(1), m.end(1), m.group(1), priority=80)
        for m in BSN_RE.finditer(text)
        if is_valid_bsn(m.group(1))
    ]


####################################
# IBAN (mod-97)
####################################

# Lengte van de IBAN per land (gangbare landen in Europa)
IBAN_LENGTHS = {
    'AD': 24,
    'AT': 20,
    'BE': 16,
    'BG': 22,
    'CH': 21,
    'CY': 28,
    'CZ': 24,
    'DE': 22,
    'DK': 18,
    'EE': 20,
    'ES': 24,
    'FI': 18,
    'FR': 27,
    'GB': 22,
    'GI': 23,
    'GR': 27,
    'HR': 21,
    'HU': 28,
    'IE': 22,
    'IS': 26,
    'IT': 27,
    'LI': 21,
    'LT': 20,
    'LU': 20,
    'LV': 21,
    'MC': 27,
    'MT': 31,
    'NL': 18,
    'NO': 15,
    'PL': 28,
    'PT': 25,
    'RO': 24,
    'SE': 24,
    'SI': 19,
    'SK': 24,
    'SM': 27,
    'TR': 26,
    'VA': 22,
}

IBAN_START_RE = re.compile(r'(?<![A-Za-z0-9])([A-Za-z]{2})(\d{2})')
IBAN_LOOSE_RE = re.compile(r'(?<![A-Za-z0-9])([A-Za-z]{2})\s?\d{2}\s?[A-Za-z]{4}(?:\s?\d){7,12}(?![A-Za-z0-9])')


def is_valid_iban(value: str) -> bool:
    iban = re.sub(r'\s', '', value).upper()
    expected = IBAN_LENGTHS.get(iban[:2])
    if not expected or len(iban) != expected or not iban.isalnum():
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = ''.join(str(int(c, 36)) for c in rearranged)
    return int(numeric) % 97 == 1


def find_iban(text: str) -> list[Finding]:
    findings = []
    for m in IBAN_START_RE.finditer(text):
        expected = IBAN_LENGTHS.get(m.group(1).upper())
        if not expected:
            continue
        # Verzamel tekens vanaf de landcode; enkele spaties mogen ertussen staan
        collected, pos = 0, m.start()
        while pos < len(text) and collected < expected:
            ch = text[pos]
            if ch.isalnum():
                collected += 1
            elif ch == ' ' and collected > 0 and pos + 1 < len(text) and text[pos + 1].isalnum():
                pass
            else:
                break
            pos += 1
        if collected != expected:
            continue
        # Direct na de IBAN mag geen letter of cijfer volgen
        if pos < len(text) and text[pos].isalnum():
            continue
        candidate = text[m.start() : pos]
        if is_valid_iban(candidate):
            findings.append(Finding('iban', m.start(), pos, candidate, priority=100))

    # Ook IBAN's met een tikfout (verkeerde lengte of controlegetal) zijn nog
    # steeds bankrekeningnummers. Herken alles met de vorm van een IBAN met
    # bankcode: landcode, 2 cijfers, 4 letters en 7 tot 12 cijfers.
    for m in IBAN_LOOSE_RE.finditer(text):
        if m.group(1).upper() in IBAN_LENGTHS and not any(f.start <= m.start() < f.end for f in findings):
            findings.append(Finding('iban', m.start(), m.end(), m.group(0), priority=99))
    return findings


####################################
# Geboortedatum (alleen met context)
####################################

MONTHS = {
    'januari': 1,
    'jan': 1,
    'februari': 2,
    'feb': 2,
    'maart': 3,
    'mrt': 3,
    'mar': 3,
    'april': 4,
    'apr': 4,
    'mei': 5,
    'juni': 6,
    'jun': 6,
    'juli': 7,
    'jul': 7,
    'augustus': 8,
    'aug': 8,
    'september': 9,
    'sep': 9,
    'sept': 9,
    'oktober': 10,
    'okt': 10,
    'oct': 10,
    'november': 11,
    'nov': 11,
    'december': 12,
    'dec': 12,
}
_MONTH_NAMES = '|'.join(sorted(MONTHS, key=len, reverse=True))

DATE_NUMERIC_RE = re.compile(r'(?<!\d)(\d{1,2})([-/.])(\d{1,2})\2(\d{4}|\d{2})(?!\d)')
DATE_ISO_RE = re.compile(r'(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)')
DATE_WORDS_RE = re.compile(rf'(?<!\d)(\d{{1,2}})\s+({_MONTH_NAMES})\.?\s+(\d{{4}})(?!\d)', re.IGNORECASE)

BIRTH_CONTEXT_RE = re.compile(r'geboren|\bgeb\.|geboorte|\bdob\b|date of birth|\bjarig|verjaardag|\bleeftijd')


def _valid_date(day: int, month: int, year: int) -> bool:
    if year < 100:
        year += 1900 if year > date.today().year % 100 else 2000
    if not 1900 <= year <= date.today().year:
        return False
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def find_birthdate(text: str) -> list[Finding]:
    candidates = []
    for m in DATE_NUMERIC_RE.finditer(text):
        candidates.append((m, int(m.group(1)), int(m.group(3)), int(m.group(4))))
    for m in DATE_ISO_RE.finditer(text):
        candidates.append((m, int(m.group(3)), int(m.group(2)), int(m.group(1))))
    for m in DATE_WORDS_RE.finditer(text):
        candidates.append((m, int(m.group(1)), MONTHS[m.group(2).lower()], int(m.group(3))))

    return [
        Finding('geboortedatum', m.start(), m.end(), m.group(0), priority=60)
        for m, day, month, year in candidates
        if _valid_date(day, month, year) and _has_context(text, m.start(), BIRTH_CONTEXT_RE)
    ]


####################################
# E-mailadres
####################################

EMAIL_RE = re.compile(r'(?<![\w.+-])[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}')


def find_email(text: str) -> list[Finding]:
    return [Finding('email', m.start(), m.end(), m.group(0), priority=95) for m in EMAIL_RE.finditer(text)]


####################################
# Telefoonnummer
####################################

PHONE_NL_RE = re.compile(r'(?<![\w+])(?:\+31|0031|0)(?:[\s.\-()]*\d){9}(?!\d)')
PHONE_INTL_RE = re.compile(r'(?<![\w+])\+(?!31)\d{1,3}(?:[\s.\-()]*\d){6,12}(?!\d)')


def find_phone(text: str) -> list[Finding]:
    findings = []
    for m in PHONE_NL_RE.finditer(text):
        digits = _digits(m.group(0))
        national = digits[2:] if digits.startswith('31') else digits[4:] if digits.startswith('0031') else digits[1:]
        if len(national) == 9 and national[0] != '0':
            findings.append(Finding('telefoon', m.start(), m.end(), m.group(0), priority=70))
    for m in PHONE_INTL_RE.finditer(text):
        findings.append(Finding('telefoon', m.start(), m.end(), m.group(0), priority=70))
    return findings


####################################
# Adres: postcode en straat + huisnummer
####################################

# Hoofdletters met optionele spatie, of kleine letters zonder spatie. Zo geeft
# "in 2024 en" geen treffer.
POSTCODE_RE = re.compile(r'(?<![\w])[1-9]\d{3}(?: ?(?!SA|SD|SS)[A-Z]{2}|(?!sa|sd|ss)[a-z]{2})(?![\w])')

STREET_SUFFIXES = (
    'straat|laan|weg|plein|singel|gracht|kade|dijk|steeg|hof|park|dreef|pad|baan|'
    'kanaal|markt|wal|ring|plantsoen|erf|veld|hoven|burgwal|boulevard|allee|haven|polder'
)
STREET_RE = re.compile(
    rf'(?<![\w])(?:[A-Z][\w\'-]*\s){{0,3}}[A-Z][\w\'-]*(?:{STREET_SUFFIXES})\s\d{{1,5}}(?:\s?[a-zA-Z](?![\w]))?(?:-\d{{1,4}})?'
)


def find_address(text: str) -> list[Finding]:
    findings = [Finding('postcode', m.start(), m.end(), m.group(0), priority=50) for m in POSTCODE_RE.finditer(text)]
    findings += [Finding('adres', m.start(), m.end(), m.group(0), priority=55) for m in STREET_RE.finditer(text)]
    return findings


####################################
# Identiteitsdocument, rijbewijs, V-nummer (alleen met context)
####################################

ID_DOC_RE = re.compile(r'(?<![\w])[A-NP-Z]{2}[A-NP-Z0-9]{6}\d(?![\w])')
ID_DOC_CONTEXT_RE = re.compile(r'paspoort|identiteitskaart|id-kaart|id kaart|\bid\b|documentnummer|legitimatie')

TEN_DIGITS_RE = re.compile(r'(?<![\d])\d{10}(?![\d])')
DRIVING_LICENSE_CONTEXT_RE = re.compile(r'rijbewijs')
V_NUMBER_CONTEXT_RE = re.compile(r'v-nummer|v nummer|vnummer|vreemdelingennummer')


def find_id_documents(text: str) -> list[Finding]:
    findings = [
        Finding('id_document', m.start(), m.end(), m.group(0), priority=85)
        for m in ID_DOC_RE.finditer(text)
        if _has_context(text, m.start(), ID_DOC_CONTEXT_RE)
    ]
    for m in TEN_DIGITS_RE.finditer(text):
        if _has_context(text, m.start(), DRIVING_LICENSE_CONTEXT_RE):
            findings.append(Finding('rijbewijs', m.start(), m.end(), m.group(0), priority=85))
        elif _has_context(text, m.start(), V_NUMBER_CONTEXT_RE):
            findings.append(Finding('v_nummer', m.start(), m.end(), m.group(0), priority=85))
    return findings


####################################
# Kenteken (Nederlandse sidecodes)
####################################

_SIDECODES = [
    (r'[A-Z]{2}', r'\d{2}', r'\d{2}'),
    (r'\d{2}', r'\d{2}', r'[A-Z]{2}'),
    (r'\d{2}', r'[A-Z]{2}', r'\d{2}'),
    (r'[A-Z]{2}', r'\d{2}', r'[A-Z]{2}'),
    (r'[A-Z]{2}', r'[A-Z]{2}', r'\d{2}'),
    (r'\d{2}', r'[A-Z]{2}', r'[A-Z]{2}'),
    (r'\d{2}', r'[A-Z]{3}', r'\d'),
    (r'\d', r'[A-Z]{3}', r'\d{2}'),
    (r'[A-Z]{2}', r'\d{3}', r'[A-Z]'),
    (r'[A-Z]', r'\d{3}', r'[A-Z]{2}'),
    (r'[A-Z]{3}', r'\d{2}', r'[A-Z]'),
    (r'[A-Z]', r'\d{2}', r'[A-Z]{3}'),
    (r'\d', r'[A-Z]{2}', r'\d{3}'),
    (r'\d{3}', r'[A-Z]{2}', r'\d'),
]
KENTEKEN_HYPHEN_RE = re.compile(r'(?<![\w-])(?:' + '|'.join(f'{a}-{b}-{c}' for a, b, c in _SIDECODES) + r')(?![\w-])')
KENTEKEN_PLAIN_RE = re.compile(r'(?<![\w-])(?:' + '|'.join(f'{a}{b}{c}' for a, b, c in _SIDECODES) + r')(?![\w-])')
KENTEKEN_CONTEXT_RE = re.compile(r'kenteken|nummerplaat|auto|voertuig')


def find_license_plate(text: str) -> list[Finding]:
    findings = [
        Finding('kenteken', m.start(), m.end(), m.group(0), priority=65) for m in KENTEKEN_HYPHEN_RE.finditer(text)
    ]
    findings += [
        Finding('kenteken', m.start(), m.end(), m.group(0), priority=65)
        for m in KENTEKEN_PLAIN_RE.finditer(text)
        # Zonder streepjes alleen met context, en niet als het alleen cijfers zijn
        if _has_context(text, m.start(), KENTEKEN_CONTEXT_RE) and re.search(r'[A-Z]', m.group(0))
    ]
    return findings


####################################
# Creditcard (Luhn)
####################################

CREDITCARD_RE = re.compile(r'(?<![\d])[3-6]\d{3}(?:[ -]?\d){9,15}(?![\d])')


def is_valid_luhn(value: str) -> bool:
    digits = _digits(value)
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def find_creditcard(text: str) -> list[Finding]:
    return [
        Finding('creditcard', m.start(), m.end(), m.group(0), priority=90)
        for m in CREDITCARD_RE.finditer(text)
        if is_valid_luhn(m.group(0))
    ]


####################################
# IP-adres
####################################

IPV4_RE = re.compile(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.]|\.\d)')
IPV6_RE = re.compile(r'(?<![\w:])(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}(?![\w:])')


def find_ip(text: str) -> list[Finding]:
    findings = []
    for m in IPV4_RE.finditer(text):
        try:
            ipaddress.IPv4Address(m.group(0))
            findings.append(Finding('ip_adres', m.start(), m.end(), m.group(0), priority=40))
        except ValueError:
            pass
    for m in IPV6_RE.finditer(text):
        value = m.group(0)
        # Tijden als 12:30:45 zijn ook geldige hex-groepen; eis een letter, '::' of veel groepen
        if not (re.search(r'[a-fA-F]', value) or '::' in value or value.count(':') >= 4):
            continue
        try:
            ipaddress.IPv6Address(value)
            findings.append(Finding('ip_adres', m.start(), m.end(), value, priority=40))
        except ValueError:
            pass
    return findings


####################################
# Bijzondere persoonsgegevens (AVG art. 9 en 10): alleen waarschuwen
####################################

SPECIAL_CATEGORY_TERMS = {
    'gezondheid': [
        'diagnose',
        'ziekte',
        'kanker',
        'diabetes',
        'depressie',
        'depressief',
        'burn-out',
        'burnout',
        'zwanger',
        'zwangerschap',
        'medicatie',
        'medicijnen',
        'psychiater',
        'psycholoog',
        'ggz',
        'hiv',
        'aids',
        'verslaving',
        'verslaafd',
        'handicap',
        'chronisch ziek',
        'arbeidsongeschikt',
        'ziekmelding',
        'ziek gemeld',
        'ziekenhuisopname',
        'opgenomen in het ziekenhuis',
        'autisme',
        'adhd',
    ],
    'religie': [
        'moslim',
        'christen',
        'christelijk',
        'joods',
        'jood',
        'katholiek',
        'protestants',
        'hindoe',
        'boeddhist',
        'islamitisch',
        'moskee',
        'synagoge',
        'geloofsovertuiging',
        'religieuze overtuiging',
    ],
    'afkomst': ['etnische afkomst', 'etniciteit', 'huidskleur', 'ras '],
    'politiek': ['politieke voorkeur', 'politieke overtuiging', 'lid van de partij', 'partijlid', 'stemt op'],
    'vakbond': ['vakbond', 'vakbondslid', 'fnv-lid', 'cnv-lid'],
    'seksuele_geaardheid': [
        'seksuele geaardheid',
        'homoseksueel',
        'homo',
        'lesbisch',
        'lesbienne',
        'biseksueel',
        'transgender',
    ],
    'strafrechtelijk': [
        'strafblad',
        'veroordeeld',
        'veroordeling',
        'gedetineerd',
        'detentie',
        'gevangenis',
        'proces-verbaal',
        'verdachte',
        'strafrechtelijk',
    ],
}
SPECIAL_CATEGORY_RES = {
    sub: re.compile(r'(?<![\w-])(?:' + '|'.join(re.escape(t.strip()) for t in terms) + r')(?![\w-])', re.IGNORECASE)
    for sub, terms in SPECIAL_CATEGORY_TERMS.items()
}


def find_special_categories(text: str) -> list[Finding]:
    findings = []
    for sub, regex in SPECIAL_CATEGORY_RES.items():
        for m in regex.finditer(text):
            findings.append(
                Finding('bijzonder', m.start(), m.end(), m.group(0), maskable=False, priority=0, detail=sub)
            )
    return findings


RECOGNIZERS = {
    'bsn': find_bsn,
    'iban': find_iban,
    'geboortedatum': find_birthdate,
    'email': find_email,
    'telefoon': find_phone,
    'adres': find_address,
    'id_document': find_id_documents,
    'kenteken': find_license_plate,
    'creditcard': find_creditcard,
    'ip_adres': find_ip,
    'bijzonder': find_special_categories,
}
