import asyncio  # Voor het parallel uitvoeren van taken
import re  # Voor reguliere expressies (patroonherkenning in tekst)
from typing import List, Dict, Any, Optional  # Type hints voor betere code documentatie

from fastapi import APIRouter, Depends, HTTPException, Request, status  # FastAPI componenten

# Importeer authenticatie en chat functies
from open_webui.utils.auth import get_verified_user
from open_webui.utils.chat import generate_chat_completion as chat_completion

router = APIRouter()  # Maak een nieuwe router voor deze endpoints

# Woordenlijsten met termen die niet vereenvoudigd moeten worden
WORD_LISTS = {
    "algemeen": [
        "DigiD", 
        "MijnOverheid", 
        # ... andere overheidsspecifieke termen
    ],
    "medisch": [
        "pancreaskopcarcinoom",
        "kanker-19",
        # ... andere medische termen
    ]
}

# Combineer alle woordenlijsten tot één standaardlijst van woorden die behouden moeten blijven
DEFAULT_PRESERVED_WORDS = WORD_LISTS["algemeen"] + WORD_LISTS["medisch"]

@router.get("/word-lists")
async def get_word_lists():
    """
    API-endpoint: Geeft alle beschikbare woordenlijsten terug.
    Deze worden in de frontend gebruikt om gebruikers te laten kiezen welke woorden behouden moeten blijven.
    """
    return {"word_lists": WORD_LISTS}

@router.get("/default-words")
async def get_default_preserved_words():
    """
    API-endpoint: Geeft de standaard bewaarde woorden terug.
    Deze worden in de frontend gebruikt als startpunt.
    """
    return {"default_preserved_words": DEFAULT_PRESERVED_WORDS}

@router.post("")
async def translate_to_b1(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),  # Controleer of gebruiker is ingelogd
):
    """
    Hoofdfunctie: Vertaalt tekst naar B1- of B2-taalniveau.
    
    Werking:
    1. Splitst de tekst in paragrafen
    2. Genereert voor elke paragraaf 3 verschillende versies (met verschillende 'temperaturen')
    3. Selecteert de beste versie voor elke paragraaf
    4. Combineert alles weer tot één tekst
    
    Dit gebeurt allemaal parallel voor snelheid.
    """
    # Haal gegevens uit het verzoek
    input_text = form_data.get("text", "")  # De te vertalen tekst
    preserved_words = form_data.get("preserved_words", [])  # Woorden die niet vertaald mogen worden
    excluded_default_words = form_data.get("excluded_default_words", [])  # Standaardwoorden die WEL vertaald mogen worden
    model_id = form_data.get("model", None)  # Welk AI-model gebruiken we?
    language_level = form_data.get("language_level", "B1")  # B1 of B2 taalniveau
    
    # Voeg standaardwoorden toe aan de lijst van te behouden woorden, tenzij expliciet uitgesloten
    for word in DEFAULT_PRESERVED_WORDS:
        if word not in excluded_default_words and word not in preserved_words:
            preserved_words.append(word)
    
    # Controleer of er tekst is opgegeven
    if not input_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geen tekst opgegeven om te vertalen",
        )
    
    # Maak de juiste instructies (system prompt) voor het gekozen taalniveau
    if language_level == "B1":
        system_prompt = """Je taak is om onderstaande tekst zorgvuldig te analyseren en vervolgens te herschrijven naar helder, begrijpelijk Nederlands op taalniveau B1...
        # ... uitgebreide instructies voor B1-niveau ...
        """
    else:  # B2 taalniveau
        system_prompt = """Je taak is om onderstaande tekst zorgvuldig te analyseren en vervolgens te herschrijven naar helder, begrijpelijk Duits op taalniveau B2...
        # ... uitgebreide instructies voor B2-niveau ...
        """

    # Voeg instructies toe over woorden die niet vereenvoudigd mogen worden
    if preserved_words:
        system_prompt += f" De volgende woorden/termen mag je NIET vereenvoudigen of veranderen, gebruik ze exact zoals ze zijn: {', '.join(preserved_words)}."
    
    # Verschillende temperatuurwaarden voor variatie in de gegenereerde tekst
    # - Lage temperatuur (0.5): Meer voorspelbaar, conservatiever
    # - Middelhoge temperatuur (0.75): Balans tussen creativiteit en voorspelbaarheid
    # - Hoge temperatuur (1.0): Meer creativiteit en variatie
    temperatures = [0.5, 0.75, 1]
    
    # Functie om tekst op te splitsen in paragrafen die niet te groot zijn
    def split_into_paragraphs(text, max_tokens=1500):
        """
        Splitst tekst in paragrafen die niet groter zijn dan max_tokens.
        Dit is nodig omdat AI-modellen een limiet hebben aan hoeveel tekst ze kunnen verwerken.
        """
        # Eerst splitsen op dubbele newlines (paragrafen)
        paragraphs = text.split("\n\n")
        
        # Resultaatlijst voor paragrafen die binnen token limiet vallen
        result_paragraphs = []
        current_paragraph = ""
        
        for paragraph in paragraphs:
            # Schatting van tokens (ongeveer 4 tekens per token)
            estimated_tokens = len(paragraph) / 4
            
            # Als een enkele paragraaf te groot is, splits deze op zinnen
            if estimated_tokens > max_tokens:
                sentences = paragraph.replace(". ", ".|").replace("! ", "!|").replace("? ", "?|").split("|")
                current_sentence_group = ""
                
                for sentence in sentences:
                    if not sentence:
                        continue
                    
                    # Schat tokens voor huidige zinsgroep + nieuwe zin
                    estimated_group_tokens = (len(current_sentence_group) + len(sentence)) / 4
                    
                    # Als toevoegen van deze zin te groot wordt, sla huidige groep op en begin nieuwe
                    if estimated_group_tokens > max_tokens and current_sentence_group:
                        result_paragraphs.append(current_sentence_group)
                        current_sentence_group = sentence
                    else:
                        # Voeg zin toe aan huidige groep
                        if current_sentence_group:
                            current_sentence_group += " " + sentence
                        else:
                            current_sentence_group = sentence
                
                # Voeg laatste zinsgroep toe als die bestaat
                if current_sentence_group:
                    result_paragraphs.append(current_sentence_group)
            else:
                # Als huidige paragraaf + nieuwe paragraaf te groot wordt
                estimated_combined_tokens = (len(current_paragraph) + len(paragraph)) / 4
                
                if estimated_combined_tokens > max_tokens and current_paragraph:
                    result_paragraphs.append(current_paragraph)
                    current_paragraph = paragraph
                else:
                    # Voeg paragraaf toe aan huidige paragraaf
                    if current_paragraph:
                        current_paragraph += "\n\n" + paragraph
                    else:
                        current_paragraph = paragraph
        
        # Voeg laatste paragraaf toe als die bestaat
        if current_paragraph:
            result_paragraphs.append(current_paragraph)
            
        return result_paragraphs
    
    # Functie om één versie van een paragraaf te genereren met een specifieke temperatuur
    async def generate_paragraph_version(paragraph_index, paragraph, temp_index, temperature):
        """
        Genereert één versie van een paragraaf met een specifieke temperatuurwaarde.
        
        Parameters:
        - paragraph_index: Index van de paragraaf (om resultaten later te ordenen)
        - paragraph: De tekst van de paragraaf
        - temp_index: Index van de temperatuurwaarde (0, 1 of 2)
        - temperature: De temperatuurwaarde zelf (0.5, 0.75 of 1.0)
        
        Returns:
        Een dictionary met de gegenereerde tekst en metadata
        """
        # Maak een verzoek voor het AI-model
        chat_request = {
            "model": model_id,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt  # Instructies voor het model
                },
                {
                    "role": "user",
                    "content": f"Vertaal de volgende tekst naar {language_level}-taalniveau. Behoud de structuur en opmaak zoals alinea's en opsommingen:\n\n{paragraph}"
                }
            ],
            "temperature": temperature  # Hoe creatief mag het model zijn?
        }
        
        # Stuur verzoek naar het AI-model
        response = await chat_completion(request, form_data=chat_request, user=user)
        
        # Haal de gegenereerde tekst uit de response
        generated_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Geef resultaat terug met metadata
        return {
            "paragraph_index": paragraph_index,  # Om later te sorteren
            "temp_index": temp_index,            # Welke temperatuur is gebruikt
            "text": generated_text,              # De gegenereerde tekst
            "temperature": temperature           # De exacte temperatuurwaarde
        }
    
    # Functie om de beste versie van een paragraaf te selecteren uit de 3 gegenereerde versies
    async def select_best_version(paragraph_index, paragraph, versions):
        """
        Laat het AI-model zelf bepalen welke van de 3 gegenereerde versies het beste is.
        
        Parameters:
        - paragraph_index: Index van de paragraaf
        - paragraph: Originele tekst van de paragraaf
        - versions: Lijst met 3 gegenereerde versies
        
        Returns:
        Een dictionary met de geselecteerde beste versie en metadata
        """
        # Maak een verzoek voor het AI-model om de beste versie te kiezen
        selection_request = {
            "model": model_id,
            "messages": [
                {
                    "role": "system",
                    "content": f'''Je taak is om onderstaande tekst zorgvuldig te analyseren en vervolgens te herschrijven naar helder, begrijpelijk Nederlands op taalniveau {language_level}. Hierbij is het essentieel dat je de informatie zo letterlijk en nauwkeurig mogelijk weergeeft en de structuur en betekenis van de originele tekst behoudt, zonder belangrijke informatie weg te laten.

Je ontvangt de originele paragraaf, samen met enkele varianten van deze tekst in eenvoudigere taal ({language_level}). Het is jouw taak om tot een definitieve {language_level}-versie te komen.'''
                },
                {
                    "role": "user",
                    "content": f"Hier is de originele paragraaf:\n\"{paragraph}\"\n\nHier zijn drie versies vertaald naar {language_level}-niveau:\n\nVersie 1 (temperature {versions[0]['temperature']}):\n{versions[0]['text']}\n\nVersie 2 (temperature {versions[1]['temperature']}):\n{versions[1]['text']}\n\nVersie 3 (temperature {versions[2]['temperature']}):\n{versions[2]['text']}\n\nSelecteer de beste versie en geef alleen het nummer (1, 2 of 3) van de beste versie terug, zonder uitleg."
                }
            ],
            "temperature": 0.1  # Lage temperatuur voor consistente beoordeling
        }
        
        # Stuur verzoek naar het AI-model
        selection_response = await chat_completion(request, form_data=selection_request, user=user)
        selection_text = selection_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Bepaal welke versie is gekozen (1, 2 of 3)
        selected_version = 0  # Standaard eerste versie
        for i in range(1, 4):
            if str(i) in selection_text:
                selected_version = i - 1  # Aanpassen naar 0-gebaseerde index (0, 1, 2)
                break
        
        # Geef resultaat terug met metadata
        return {
            "paragraph_index": paragraph_index,
            "original": paragraph,                             # Originele tekst
            "translated": versions[selected_version]["text"],  # Geselecteerde vertaling
            "selected_version": selected_version + 1,          # Welke versie (1, 2 of 3)
            "temperature": versions[selected_version]["temperature"]  # Gebruikte temperatuur
        }
    
    try:
        # STAP 1: Split de input tekst in paragrafen
        paragraphs = split_into_paragraphs(input_text)
        
        # STAP 2: Genereer alle versies voor alle paragrafen GELIJKTIJDIG
        # Maak een lijst met alle taken die uitgevoerd moeten worden
        all_generation_tasks = []
        for p_idx, paragraph in enumerate(paragraphs):
            for t_idx, temp in enumerate(temperatures):
                # Voor elke paragraaf maken we 3 taken (één voor elke temperatuur)
                all_generation_tasks.append(generate_paragraph_version(p_idx, paragraph, t_idx, temp))
        
        # Voer alle taken parallel uit
        all_generated_versions = await asyncio.gather(*all_generation_tasks)
        
        # STAP 3: Organiseer de gegenereerde versies per paragraaf
        paragraph_versions = {}
        for version in all_generated_versions:
            p_idx = version["paragraph_index"]
            if p_idx not in paragraph_versions:
                paragraph_versions[p_idx] = [None, None, None]  # Placeholder voor 3 versies
            paragraph_versions[p_idx][version["temp_index"]] = version
        
        # STAP 4: Selecteer de beste versie voor elke paragraaf GELIJKTIJDIG
        selection_tasks = []
        for p_idx, paragraph in enumerate(paragraphs):
            versions = paragraph_versions[p_idx]
            selection_tasks.append(select_best_version(p_idx, paragraph, versions))
        
        # Voer alle selectietaken parallel uit
        all_selections = await asyncio.gather(*selection_tasks)
        
        # STAP 5: Sorteer de resultaten op paragraaf index om de originele volgorde te behouden
        all_selections.sort(key=lambda x: x["paragraph_index"])
        
        # STAP 6: Haal de vertaalde tekst uit de speciale markeringen (<<< en >>>)
        import re

        # Functie om tekst tussen markeringen te extraheren
        def extract_content(text):
            """
            Haalt de tekst tussen <<< en >>> markeringen.
            Als er geen markeringen zijn, wordt de originele tekst teruggegeven.
            """
            pattern = r'<<<(.*?)>>>'
            match = re.search(pattern, text, re.DOTALL)  # re.DOTALL zorgt dat ook newlines worden meegenomen
            if match:
                return match.group(1).strip()  # Haal de tekst tussen markeringen op en verwijder witruimte
            return text  # Geef originele tekst terug als er geen markeringen zijn

        # Pas de extractie toe op alle geselecteerde vertalingen
        for result in all_selections:
            result["translated"] = extract_content(result["translated"])

        # STAP 7: Zorg ervoor dat de bewaarde woorden (preserved words) niet zijn vertaald
        all_selections = enforce_preserved_words(all_selections, preserved_words)

        # STAP 8: Combineer alle paragrafen weer tot één tekst
        combined_text = "\n\n".join([result["translated"] for result in all_selections])
        
        # STAP 9: Bereid de uiteindelijke response voor in het juiste formaat
        final_response = {
            "choices": [
                {
                    "message": {
                        "content": combined_text,  # De uiteindelijke vertaalde tekst
                        "role": "assistant"
                    },
                    "index": 0,
                    "finish_reason": "stop"
                }
            ],
            "model": model_id,
            "object": "chat.completion",
            "usage": {
                "completion_tokens": 0,  # Deze waarden worden niet berekend
                "prompt_tokens": 0,
                "total_tokens": 0
            },
            "meta": {
                "paragraph_count": len(all_selections),  # Aantal paragrafen
                "paragraph_details": [
                    {
                        "selected_version": result["selected_version"],  # Welke versie is gekozen (1, 2 of 3)
                        "temperature": result["temperature"]  # Met welke temperatuur
                    } for result in all_selections
                ]
            }
        }
        
        # Stuur het resultaat terug
        return final_response
    
    except Exception as e:
        # Als er iets misgaat, geef een duidelijke foutmelding
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

def enforce_preserved_words(translations: List[Dict[str, Any]], preserved_words: List[str]) -> List[Dict[str, Any]]:
    """
    Zorgt ervoor dat de opgegeven woorden (preserved_words) niet worden vertaald.
    
    Werking:
    Voor elk woord in de preserved_words lijst, zoekt deze functie naar dat woord in de vertaalde tekst
    en vervangt eventuele vertalingen door het originele woord.
    
    Parameters:
    - translations: Lijst met vertaalde paragrafen
    - preserved_words: Lijst met woorden die niet vertaald mogen worden
    
    Returns:
    De bijgewerkte lijst met vertalingen waarin de preserved_words behouden zijn
    """
    for translation in translations:
        for word in preserved_words:
            # Gebruik regex om woorden exact te matchen en te vervangen
            # \b zorgt ervoor dat alleen hele woorden worden gematcht (niet delen van woorden)
            # re.IGNORECASE zorgt ervoor dat hoofdletters niet uitmaken
            translation["translated"] = re.sub(
                rf"\b{re.escape(word)}\b", word, translation["translated"], flags=re.IGNORECASE
            )
    return translations