# Thema-aanpassingen

GovChat-NL biedt de mogelijkheid om de chatbot volledig aan te passen aan de huisstijl en communicatiebehoeften van een overheidsorganisatie. De belangrijkste aanpassingen kunnen eenvoudig worden doorgevoerd via environment-variabelen. Het doel is om deze variabelen in de toekomst te integreren in het admin-paneel, zodat aanpassingen nog toegankelijker worden voor beheerders.

---

## GovChat-NL-specifieke environment-variabelen

GovChat-NL bouwt voort op de sterke basis van OpenWebUI, maar introduceert enkele extra environment-variabelen die specifiek zijn ontworpen om aan te sluiten bij de behoeften van overheidsorganisaties. Deze variabelen maken het mogelijk om het uiterlijk en gedrag van de chatbot te personaliseren. Hieronder vind je een overzicht van de extra beschikbare variabele:

### `EMPTY_CHAT_WELCOME_MESSAGE` (Default: `"welkom bij GovChat-NL"`)

De variabele `EMPTY_CHAT_WELCOME_MESSAGE` wordt gebruikt voor het instellen van een standaardbegroeting wanneer een nieuwe (lege) chat wordt gestart. De begroetingszin is opgebouwd volgens het volgende format:

```plaintext
Hallo <voornaam>, <EMPTY_CHAT_WELCOME_MESSAGE>
```

Als de voornaam niet beschikbaar is, zal de gebruiker alleen het welkomstbericht zien, zonder voornaam:

```plaintext
Hallo, <EMPTY_CHAT_WELCOME_MESSAGE>
```

### `LOGIN_SCREEN_SUBTITLE` (Default: `None`)
De variabele `LOGIN_SCREEN_SUBTITLE` biedt de mogelijkheid om een aangepaste subtitel weer te geven op het inlogscherm van de chatbot. Deze subtitel kan worden gebruikt om extra uitleg of een slogan toe te voegen die aansluit bij de communicatiebehoefte van de organisatie. 

Als de variabele niet wordt ingesteld (of als deze expliciet `None` is), zal er geen subtitel worden weergegeven.

Voorbeeldinstelling:
```plaintext
LOGIN_SCREEN_SUBTITLE="Jouw kennisassistent voor de Provincie Limburg"
```