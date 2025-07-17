# GovChat-NL: Specifieke Environment-variabelen

Als organisatie kun je GovChat-NL eenvoudig aanpassen aan de eigen wensen en uitstraling. Dat doe je met ‘environment-variabelen’: instellingen waarmee je bepaalt hoe de chatbot eruitziet en wat gebruikers kunnen. 
Deze variabelen stel je in voordat je de applicatie start, meestal in een configuratiebestand of via de beheeromgeving. 

Hieronder vind je een overzicht van alle specifieke environment-variabelen voor GovChat-NL, met uitleg over wat ze doen en hoe je ze gebruikt. 
Zo kun je GovChat-NL beter laten aansluiten bij de behoefte van jouw organisatie.

---

## EMPTY_CHAT_WELCOME_MESSAGE

- **Type:** `str`
- **Default:** "welkom bij GovChat-NL"
- **Beschrijving:**  
  Deze variabele bepaalt het standaard welkomstbericht wanneer een nieuwe, lege chat gestart wordt.  
  Het bericht wordt als volgt getoond:
    - Gebruiker met voornaam:  
      `Hallo <voornaam>, <EMPTY_CHAT_WELCOME_MESSAGE>`
    - Gebruiker zonder voornaam:  
      `Hallo, <EMPTY_CHAT_WELCOME_MESSAGE>`
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---

## LOGIN_SCREEN_SUBTITLE

- **Type:** `str`
- **Default:** None
- **Beschrijving:**  
  Hiermee kun je een aangepaste subtitel toevoegen aan het inlogscherm (bijvoorbeeld toelichting of slogan).  
  Indien niet ingesteld of gelijk aan `None`, wordt er geen subtitel getoond.
- **Voorbeeld instelling:**  
  `LOGIN_SCREEN_SUBTITLE="Jouw kennisassistent voor de Provincie Limburg"`
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---

## ENABLE_CONTROLS_BUTTON

- **Type:** `bool`
- **Default:** False
- **Beschrijving:**  
  Toon of verberg een extra bedieningsknop in de gebruikersinterface. Bij `True` ontstaat er een knoppenbalk voor snelle acties.
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---

## SHOW_CHANGE_PASSWORD

- **Type:** `bool`
- **Default:** False
- **Beschrijving:**  
  Maakt wijzigen van het wachtwoord door gebruikers direct via de interface mogelijk. Bij `True` verschijnt deze optie in het profiel- of instellingenmenu.
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---

## ALLOW_USERNAME_EDIT

- **Type:** `bool`
- **Default:** False
- **Beschrijving:**  
  Bij activeren (`True`) mogen gebruikers hun gebruikersnaam zelf aanpassen via hun profiel.
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---

## SHOW_ABOUT_TAB

- **Type:** `bool`
- **Default:** False
- **Beschrijving:**  
  Toon het tabblad “Over” in het hoofdmenu met uitleg over de applicatie.
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---

## SHOW_OVERVIEW_IN_DROPDOWN

- **Type:** `bool`
- **Default:** False
- **Beschrijving:**  
  Voegt een overzichstpagina toe aan het dropdownmenu voor snellere navigatie.
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---

## SHOW_WIDESCREEN_MODE

- **Type:** `bool`
- **Default:** False
- **Beschrijving:**  
  Schakelt een breedbeeldmodus in wanneer geactiveerd (`True`). Handig voor grote schermen.
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---

## SHOW_ARCHIVED_CHATS

- **Type:** `bool`
- **Default:** False
- **Beschrijving:**  
  Geeft gebruikers toegang tot gearchiveerde chatgesprekken via het menu. Maakt terugzoeken van oude chats eenvoudiger.
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---

## VERSIMPELAAR

- **Type:** `bool`
- **Default:** True
- **Beschrijving:**  
  Bepaalt of de Versimpelaar-app (voor vereenvoudiging naar B1/B2-niveau) zichtbaar is in de App Launcher.  
  Bij instellen op `False` wordt deze app standaard verborgen voor gebruikers.
- **Voorbeeld instelling:**  
  `VERSIMPELAAR=True  # Versimpelaar zichtbaar`
- **Persistentie:** Wordt geladen tijdens opstarten van GovChat-NL.

---