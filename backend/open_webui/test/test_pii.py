"""
GovChat-NL: tests voor het persoonsgegevensfilter.

Draaien vanuit backend/:  pytest open_webui/test/test_pii.py
"""

import asyncio

import pytest

from open_webui.utils.pii import detect, detect_and_mask, detect_long, mask, segments
from open_webui.utils.pii import enforcement
from open_webui.utils.pii.recognizers import is_valid_bsn, is_valid_iban, is_valid_luhn


def found(text, category=None, categories=None):
    return [f.text for f in detect(text, categories) if category is None or f.category == category]


####################################
# Controles
####################################


@pytest.mark.parametrize('value', ['111222333', '123456782', '111.222.333', '111 222 333'])
def test_valid_bsn(value):
    assert is_valid_bsn(value)


@pytest.mark.parametrize('value', ['123456789', '000000000', '12345678', '1234567890'])
def test_invalid_bsn(value):
    assert not is_valid_bsn(value)


@pytest.mark.parametrize(
    'value',
    [
        'NL91ABNA0417164300',
        'NL91 ABNA 0417 1643 00',
        'nl91abna0417164300',
        'DE89370400440532013000',
        'BE68539007547034',
    ],
)
def test_valid_iban(value):
    assert is_valid_iban(value)


@pytest.mark.parametrize('value', ['NL91ABNA0417164301', 'NL91ABNA041716430', 'XX91ABNA0417164300'])
def test_invalid_iban(value):
    assert not is_valid_iban(value)


@pytest.mark.parametrize('value', ['4111111111111111', '5500 0000 0000 0004', '4111-1111-1111-1111'])
def test_valid_luhn(value):
    assert is_valid_luhn(value)


def test_invalid_luhn():
    assert not is_valid_luhn('4111111111111112')


####################################
# Herkenning per categorie
####################################


class TestBsn:
    def test_found(self):
        assert found('Mijn BSN is 111222333.', 'bsn') == ['111222333']
        assert found('BSN: 111.222.333', 'bsn') == ['111.222.333']

    def test_invalid_checksum_ignored(self):
        assert found('Ordernummer 123456789', 'bsn') == []

    def test_part_of_longer_number_ignored(self):
        assert found('Het budget is 1112223330 euro', 'bsn') == []
        assert found('Telefoon 0611122233', 'bsn') == []


class TestIban:
    def test_found_with_and_without_spaces(self):
        assert found('IBAN NL91ABNA0417164300', 'iban') == ['NL91ABNA0417164300']
        assert found('op NL91 ABNA 0417 1643 00 graag', 'iban') == ['NL91 ABNA 0417 1643 00']

    def test_followed_by_word(self):
        assert found('NL91 ABNA 0417 1643 00 is mijn rekening', 'iban') == ['NL91 ABNA 0417 1643 00']

    def test_foreign(self):
        assert found('Duitse rekening DE89 3704 0044 0532 0130 00.', 'iban') == ['DE89 3704 0044 0532 0130 00']

    def test_typo_still_found(self):
        # Een cijfer te weinig of een fout controlegetal: nog steeds een rekeningnummer
        assert found('NL13INGB000883023', 'iban') == ['NL13INGB000883023']
        assert found('rekening NL91ABNA0417164301', 'iban') == ['NL91ABNA0417164301']
        assert found('NL13 INGB 0008 8302 3', 'iban') == ['NL13 INGB 0008 8302 3']

    def test_not_iban_like(self):
        assert found('Code AB12 en project NL2024', 'iban') == []


class TestBirthdate:
    @pytest.mark.parametrize(
        'text,expected',
        [
            ('Hij is geboren op 12-03-1985.', '12-03-1985'),
            ('geb. 1/2/1970', '1/2/1970'),
            ('Geboortedatum: 1985-03-12', '1985-03-12'),
            ('geboren 12 maart 1985 in Utrecht', '12 maart 1985'),
            ('geboren op 3 mrt. 1999', '3 mrt. 1999'),
        ],
    )
    def test_found_with_context(self, text, expected):
        assert found(text, 'geboortedatum') == [expected]

    def test_without_context_ignored(self):
        assert found('De deadline is 12-03-2025 en het overleg op 1 april 2026.', 'geboortedatum') == []

    def test_invalid_date_ignored(self):
        assert found('geboren op 31-02-1985', 'geboortedatum') == []

    def test_future_date_ignored(self):
        assert found('geboren op 12-03-2999', 'geboortedatum') == []


class TestContact:
    def test_email(self):
        assert found('Mail naar jan.de.vries@gemeente.nl of info@example.com', 'email') == [
            'jan.de.vries@gemeente.nl',
            'info@example.com',
        ]

    @pytest.mark.parametrize(
        'value', ['06-12345678', '0612345678', '+31 6 12345678', '020-1234567', '0031 20 123 4567', '+32 470 12 34 56']
    )
    def test_phone(self, value):
        assert found(f'Bel {value} graag', 'telefoon') == [value]

    @pytest.mark.parametrize('value', ['0612345', '1234567890'])
    def test_not_phone(self, value):
        assert found(f'Nummer {value}', 'telefoon') == []


class TestAddress:
    def test_postcode(self):
        assert found('Adres: 3511 AB Utrecht', 'postcode') == ['3511 AB']
        assert found('postcode 3511ab', 'postcode') == ['3511ab']

    def test_year_followed_by_word_not_postcode(self):
        assert found('In 2024 en 2025 is het budget gelijk', 'postcode') == []

    def test_excluded_letter_combinations(self):
        assert found('1234 SS', 'postcode') == []

    def test_street(self):
        assert found('Ze woont op de Kerkstraat 12a in Utrecht', 'adres') == ['Kerkstraat 12a']
        assert found('Van Speijkstraat 4', 'adres') == ['Van Speijkstraat 4']


class TestDocuments:
    def test_passport_with_context(self):
        assert found('Paspoortnummer XR1234567', 'id_document') == ['XR1234567']

    def test_passport_without_context_ignored(self):
        assert found('Code XR1234567 in het systeem', 'id_document') == []

    def test_driving_license_and_v_number(self):
        assert found('rijbewijsnummer 1234567890', 'rijbewijs') == ['1234567890']
        assert found('V-nummer: 1234567890', 'v_nummer') == ['1234567890']


class TestOther:
    @pytest.mark.parametrize('value', ['AB-123-C', '12-ABC-3', 'XX-99-YY'])
    def test_license_plate(self, value):
        assert found(f'Kenteken {value}', 'kenteken') == [value]

    def test_not_license_plate(self):
        assert found('Na COVID-19 en 12-03-85', 'kenteken') == []

    def test_creditcard(self):
        assert found('Kaart 4111 1111 1111 1111', 'creditcard') == ['4111 1111 1111 1111']
        assert found('Kaart 4111 1111 1111 1112', 'creditcard') == []

    def test_ip(self):
        assert found('Server 192.168.1.10 en 2001:db8::1', 'ip_adres') == ['192.168.1.10', '2001:db8::1']

    @pytest.mark.parametrize('text', ['Om 12:30:45 begint het', 'Adres 999.1.1.1', 'versie 1.2.3'])
    def test_not_ip(self, text):
        assert found(text, 'ip_adres') == []


class TestNames:
    def test_spacy_names(self):
        names = found('Gisteren sprak ik met Jan de Vries en Sanne Bakker over de begroting.', 'naam')
        assert 'Jan de Vries' in names
        assert 'Sanne Bakker' in names

    def test_title_and_particle(self):
        assert 'Fatima el Amrani' in found('Mevrouw Fatima el Amrani belde vanochtend.', 'naam')
        assert 'P. Jansen' in found('Graag terugbellen naar dhr. P. Jansen.', 'naam')

    def test_acronyms_not_names(self):
        assert found('Het BSN en de IBAN staan in de AVG-registratie.', 'naam') == []

    def test_law_acronyms_not_names(self):
        assert found('Hoe verwerk ik een Woo-verzoek volgens de Woo en de Awb?', 'naam') == []

    def test_sentence_start_not_merged(self):
        names = found('Gisteren belde Pieter over de offerte.', 'naam')
        assert 'Gisteren' not in ' '.join(names)


class TestSpecialCategories:
    def test_warn_only(self):
        findings = [f for f in detect('Ze heeft een burn-out en is lid van de vakbond.') if f.category == 'bijzonder']
        assert {f.detail for f in findings} == {'gezondheid', 'vakbond'}
        assert all(not f.maskable for f in findings)

    def test_not_masked(self):
        masked, _ = detect_and_mask('Hij heeft diabetes.')
        assert masked == 'Hij heeft diabetes.'


####################################
# Overlap, categorieën en maskeren
####################################


def test_email_wins_over_name():
    findings = detect('Mail jan.devries@example.nl vandaag')
    assert [f.category for f in findings] == ['email']


def test_disabled_category():
    assert found('BSN 111222333 en IBAN NL91ABNA0417164300', categories=['iban']) == ['NL91ABNA0417164300']


def test_no_false_positives_in_policy_text():
    text = (
        'In 2024 en 2025 heeft de provincie Gelderland 1.250.000 euro subsidie verstrekt. '
        'De Provinciale Staten besluiten op 12-03-2026 over het voorstel van Gedeputeerde Staten.'
    )
    assert [f for f in detect(text) if f.maskable and f.category != 'naam'] == []


def test_mask_labels_and_numbering():
    text = 'Jan de Vries mailde Sanne Bakker. Jan de Vries heeft IBAN NL91ABNA0417164300 en DE89370400440532013000.'
    masked, replacements = detect_and_mask(text)
    assert masked == '[NAAM 1] mailde [NAAM 2]. [NAAM 1] heeft IBAN [IBAN 1] en [IBAN 2].'
    assert len(replacements) == 5
    # De vervangingen bevatten nooit de originele waarde
    assert all('Jan' not in str(r) and 'NL91' not in str(r) for r in replacements)


def test_mask_single_value_without_number():
    masked, _ = detect_and_mask('BSN 111222333, nogmaals: 111.222.333')
    assert masked == 'BSN [BSN], nogmaals: [BSN]'


def test_mask_respects_selection():
    text = 'BSN 111222333 en IBAN NL91ABNA0417164300'
    findings = detect(text)
    masked, _ = mask(text, [f for f in findings if f.category == 'iban'])
    assert masked == 'BSN 111222333 en IBAN [IBAN]'


def test_masked_text_is_stable():
    masked, _ = detect_and_mask('Mevrouw Fatima el Amrani, BSN 111222333, tel 06-12345678.')
    again, replacements = detect_and_mask(masked)
    assert again == masked
    assert replacements == []


def test_segments_cover_text_with_emoji():
    text = 'Hoi 😀 BSN 111222333 klaar'
    findings = detect(text)
    segs = segments(text, findings)
    assert ''.join(s['text'] for s in segs) == text
    assert [s['text'] for s in segs if 'finding' in s] == ['111222333']


def test_multiline_and_unicode():
    text = 'Naam: Zoë Çelik\nBSN: 111222333\n\nIBAN: NL91ABNA0417164300 ✅'
    masked, _ = detect_and_mask(text)
    assert '111222333' not in masked and 'NL91' not in masked
    assert masked.endswith('✅')


####################################
# Server-side afdwinging
####################################


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture
def pii_config(monkeypatch):
    state = {'enable': True, 'default_mode': 'warn', 'categories': None}

    async def fake_get_pii_config():
        from open_webui.utils.pii import CATEGORIES

        return {**state, 'categories': state['categories'] or list(CATEGORIES)}

    monkeypatch.setattr(enforcement, 'get_pii_config', fake_get_pii_config)
    return state


def model_with(mode=None):
    return {'id': 'm', 'info': {'meta': {'pii_filter': mode} if mode else {}}}


@pytest.mark.parametrize(
    'enable,default_mode,agent_mode,expected',
    [
        (False, 'mask', 'mask', False),
        (True, 'warn', None, False),
        (True, 'mask', None, True),
        (True, 'warn', 'mask', True),
        (True, 'mask', 'warn', False),
        (True, 'mask', 'off', False),
    ],
)
def test_is_mask_enforced(pii_config, enable, default_mode, agent_mode, expected):
    pii_config.update(enable=enable, default_mode=default_mode)
    assert run(enforcement.is_mask_enforced(model_with(agent_mode))) is expected


def test_enforce_masks_user_messages_only(pii_config):
    messages = [
        {'role': 'system', 'content': 'BSN 111222333 hoort hier niet maar is systeemtekst'},
        {'role': 'user', 'content': 'Mijn BSN is 111222333'},
        {'role': 'assistant', 'content': 'Dank je'},
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': 'IBAN NL91ABNA0417164300'},
                {'type': 'image_url', 'image_url': {'url': 'x'}},
            ],
        },
    ]
    result = run(enforcement.enforce_pii_mask(messages, model_with('mask')))
    assert result[0]['content'].startswith('BSN 111222333')
    assert result[1]['content'] == 'Mijn BSN is [BSN]'
    assert result[3]['content'][0]['text'] == 'IBAN [IBAN]'
    assert result[3]['content'][1]['type'] == 'image_url'


def test_enforce_noop_in_warn_mode(pii_config):
    messages = [{'role': 'user', 'content': 'Mijn BSN is 111222333'}]
    assert run(enforcement.enforce_pii_mask(messages, model_with('warn')))[0]['content'] == 'Mijn BSN is 111222333'


####################################
# Bestanden en kennisbanken
####################################


def test_detect_long_matches_detect_and_shifts_positions():
    alinea = 'Dit is een alinea zonder bijzonderheden over beleid en uitvoering.\n\n'
    text = alinea * 40 + 'Mijn BSN is 111222333 en mijn IBAN is NL91ABNA0417164300.\n\n' + alinea * 40
    findings = detect_long(text, chunk_size=1000)
    assert {f.category for f in findings} == {'bsn', 'iban'}
    for f in findings:
        assert text[f.start : f.end] == f.text
    assert [f.text for f in findings] == [f.text for f in detect(text)]


def test_detect_long_masks_across_chunks():
    text = ('Geachte heer, het BSN is 111222333.\n' + 'Vul tekst aan. ' * 80 + '\n') * 5
    masked, replacements = mask(text, detect_long(text, chunk_size=500))
    assert '111222333' not in masked
    assert len(replacements) == 5


def test_mask_sources_masks_documents(pii_config):
    sources = [
        {
            'source': {'id': 'f1', 'name': 'brief.pdf'},
            'document': ['Contact: jan.jansen@example.nl', 'BSN 111222333'],
            'metadata': [{'file_id': 'f1'}, {'file_id': 'f1'}],
        },
        {'source': {'id': 'x'}, 'document': None},
    ]
    result = run(enforcement.mask_sources(sources, ['email', 'bsn']))
    assert result[0]['document'] == ['Contact: [E-MAIL]', 'BSN [BSN]']
    assert result[0]['source']['name'] == 'brief.pdf'
    assert result[1]['document'] is None


def test_mask_tool_result_keeps_json_structure():
    import json

    raw = json.dumps(
        [{'file_id': 'f1', 'content': 'IBAN NL91ABNA0417164300\nVolgende regel', 'score': 0.8}],
        ensure_ascii=False,
    )
    masked = json.loads(run(enforcement.mask_tool_result(raw, ['iban'])))
    assert masked == [{'file_id': 'f1', 'content': 'IBAN [IBAN]\nVolgende regel', 'score': 0.8}]


def test_mask_tool_result_plain_text_and_dict():
    assert run(enforcement.mask_tool_result('BSN 111222333', ['bsn'])) == 'BSN [BSN]'
    assert run(enforcement.mask_tool_result({'text': 'BSN 111222333'}, ['bsn'])) == {'text': 'BSN [BSN]'}


def test_file_tool_names_cover_citation_tools():
    # Vangt nieuwe bestandstools na een update van Open WebUI; de middleware heeft wel instellingen nodig
    try:
        from open_webui.utils.middleware import CITATION_TOOL_NAMES
    except (SystemExit, Exception):
        pytest.skip('middleware niet te laden zonder WEBUI_SECRET_KEY')

    file_tools = set(CITATION_TOOL_NAMES) - {'fetch_url'}
    assert file_tools <= enforcement.FILE_TOOL_NAMES


def test_name_after_previous_sentence_is_found():
    # spaCy plakte deze twee zinnen eerder aan elkaar tot één organisatienaam
    text = (
        'Het college van burgemeester en wethouders stelt voor om de subsidieregeling te verlengen. '
        'Wethouder Pieter de Boer is portefeuillehouder.'
    )
    assert 'Pieter de Boer' in found(text, 'naam')


def test_sentence_split_keeps_initials_and_titles_together():
    from open_webui.utils.pii.names import _sentences

    pieces = [p for _, p in _sentences('Getekend door J.M. Jansen. Dhr. Visser kwam ook, bijv. Piet.\nVolgende regel')]
    assert pieces == ['Getekend door J.M. Jansen.', 'Dhr. Visser kwam ook, bijv. Piet.', 'Volgende regel']
    assert 'J.M. Jansen' in found('Getekend door de secretaris-directeur J.M. Jansen.', 'naam')
