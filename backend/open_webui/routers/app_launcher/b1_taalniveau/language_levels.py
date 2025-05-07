LANGUAGE_LEVELS = {
    "B1": {
        "description": (
            "Het B1-niveau kenmerkt zich door duidelijk en eenvoudig taalgebruik, "
            "geschikt voor een breed publiek met basisvaardigheden in de taal."
        ),
        "guidelines": (
            "- Gebruik korte zinnen en vermijd lange, complexe zinsconstructies.\n"
            "- Vervang moeilijke woorden door meer gangbare alternatieven.\n"
            "- Leg technische termen en (ambtelijk) jargon uit in eenvoudige bewoordingen.\n"
            "- Gebruik actieve zinsconstructies waar mogelijk.\n"
            "- Vermijd passieve zinnen en ingewikkelde grammaticale constructies.\n"
            "- Gebruik concrete voorbeelden om abstracte concepten te verduidelijken."
        ),
        "examples": (
            "- Betreffende -> Over\n"
            "- Creëren -> Maken\n"
            "- Prioriteit -> Wat eerst moet, voorrang\n"
            "- Relevant -> Belangrijk (voor dit onderwerp)\n"
            "- Verstrekken -> Geven"
        ),
        "source_example_level": "C1",
    },
    "B2": {
        "description": (
            "Het B2-niveau kenmerkt zich door helder en gedetailleerd taalgebruik, "
            "geschikt voor een publiek met gevorderde taalvaardigheden. "
            "De tekst moet toegankelijk zijn zonder overmatig gebruik van complexe termen, "
            "gericht op lezers die bekend zijn met de basisprincipes van de taal en in staat zijn om zowel "
            "praktische als theoretische onderwerpen te begrijpen."
        ),
        "guidelines": (
            "- Gebruik korte tot middelmatige zinnen en vermijd extreme complexiteit, maar behoud enige diepgang in de formulering.\n"
            "- Vervang zeer complexe woorden door alternatieven die nauwkeurig zijn maar minder specialistisch.\n"
            "- Leg technische termen en ambtelijk jargon duidelijk uit, waarbij je enige mate van detail behoudt om de nauwkeurigheid te waarborgen.\n"
            "- Gebruik actieve zinsconstructies waar mogelijk, maar passieve zinnen kunnen gebruikt worden als dit de tekst logischer maakt.\n"
            "- Beperk ingewikkelde grammaticale constructies, maar behoud een zekere variatie in de zinsopbouw.\n"
            "- Gebruik passende en concrete voorbeelden om abstracte of lastigere concepten uit te leggen, zodat de lezer een context heeft om de informatie te begrijpen."
        ),
        "examples": (
            "- Betreffende -> Met betrekking tot, Over\n"
            "- Creëren -> Maken, ontwikkelen\n"
            "- Prioriteit -> Belangrijkste punt, voorrang\n"
            "- Relevant -> Van toepassing, belangrijk\n"
            "- Verstrekken -> Geven, aanbieden"
        ),
        "source_example_level": "C2",
    },
    # Voeg eventueel meer niveaus toe!
}

DEFAULT_LANGUAGE_LEVEL = "B1"

def get_level_data(level_key: str):
    key = str(level_key or DEFAULT_LANGUAGE_LEVEL).upper()
    return LANGUAGE_LEVELS.get(key, LANGUAGE_LEVELS[DEFAULT_LANGUAGE_LEVEL])