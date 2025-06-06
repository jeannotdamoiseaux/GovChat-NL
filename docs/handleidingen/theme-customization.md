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

### `ENABLE_CALL` (Default: `False`)
Met de variabele `ENABLE_CALL` kun je de belfunctie in de chatinterface activeren.  
Standaard staat deze optie uitgeschakeld, omdat het voeren van een spraakgesprek alleen goed ondersteund wordt door specifieke AI-modellen en niet altijd relevant of duidelijk is voor alle gebruikers. Wanneer je `ENABLE_CALL=True` instelt in de omgeving, verschijnt de call-knop in de chatinterface. Gebruikers kunnen dan direct een spraakconversatie met het gekozen model starten.

Voorbeeldinstelling:
```plaintext
ENABLE_CALL=True
```

### `ENABLE_MULTIPLE_MODELS` (Default: `False`)
Met `ENABLE_MULTIPLE_MODELS` geef je gebruikers de mogelijkheid om in één chatgesprek meerdere AI-modellen tegelijk te selecteren en te gebruiken.  
Wanneer deze optie is ingeschakeld (`ENABLE_MULTIPLE_MODELS=True`), kunnen er binnen één gesprek verschillende modellen tegelijkertijd worden bevraagd.
Standaard staat deze functie uit om de interface eenvoudig te houden.

Voorbeeldinstelling:
```plaintext
ENABLE_MULTIPLE_MODELS=True
```

### `ENABLE_CONTROLS_BUTTON` (Default: `False`)
Deze optie maakt een extra besturingsknop ("controls button") zichtbaar in de chatinterface, waarmee aanvullende instellingen of actiemogelijkheden toegankelijk kunnen worden gemaakt voor de gebruiker.  
Standaard is deze extra knop verborgen gehouden om de interface zo overzichtelijk en gebruiksvriendelijk mogelijk te houden. Zet je `ENABLE_CONTROLS_BUTTON=True`, dan verschijnt deze controls-knop.

Voorbeeldinstelling:
```plaintext
ENABLE_CONTROLS_BUTTON=True
```