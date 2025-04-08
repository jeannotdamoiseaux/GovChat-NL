import asyncio
import re
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from open_webui.utils.auth import get_verified_user
from open_webui.utils.chat import generate_chat_completion as chat_completion

router = APIRouter()

# Verschillende woordenlijsten
WORD_LISTS = {
    "algemeen": [
        "DigiD", 
        "MijnOverheid", 
        "BSN", 
        "Burgerservicenummer",
        "WOZ", 
        "IBAN", 
        "BIC", 
        "KvK", 
        "BTW", 
        "BRP", 
        "UWV", 
        "SVB", 
        "DUO", 
        "CAK", 
        "CJIB"
    ],
    "medisch": [
        "pancreaskopcarcinoom",
        "kanker-19",
        "diabetes",
        "hypertensie",
        "cholesterol",
        "antibiotica",
        "vaccin",
        "immuniteit",
        "diagnose",
        "symptomen",
        "medicatie"
    ]
}

# Standaard uitgesloten woorden - deze worden standaard behouden
DEFAULT_PRESERVED_WORDS = WORD_LISTS["algemeen"] + WORD_LISTS["medisch"]

@router.get("/word-lists")
async def get_word_lists():
    """
    Endpoint om alle beschikbare woordenlijsten op te halen.
    Deze worden gebruikt in de frontend.
    """
    return {"word_lists": WORD_LISTS}

@router.get("/default-words")
async def get_default_preserved_words():
    """
    Endpoint om de standaard uitgesloten woorden op te halen.
    Deze worden gebruikt in de frontend.
    """
    return {"default_preserved_words": DEFAULT_PRESERVED_WORDS}


@router.post("")
async def translate_to_b1(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
    max_words_per_chunk: Optional[int] = 15000,
    max_tokens_per_paragraph: Optional[int] = 3000,
    batch_size: Optional[int] = 50,
):
    """
    Endpoint voor het vertalen van tekst naar B1- of B2-taalniveau.
    Verwerkt tekst in blokken van maximaal 15.000 woorden, verdeelt grote teksten in paragrafen,
    genereert drie versies per paragraaf gelijktijdig met verschillende temperatuurwaarden
    en selecteert de beste versie voor elke paragraaf.
    Alle generaties en vergelijkingen worden parallel uitgevoerd.
    
    Parameters:
    - max_words_per_chunk: Maximum aantal woorden per chunk (None voor geen chunking)
    - max_tokens_per_paragraph: Maximum aantal tokens per paragraaf (None voor geen paragraaf-splitsing)
    - batch_size: Aantal paragrafen dat parallel verwerkt wordt (None voor onbeperkt)
    """
    # Haal de benodigde gegevens uit de request
    input_text = form_data.get("text", "")
    preserved_words = form_data.get("preserved_words", [])  # Dit bevat nu zowel toegevoegde als niet-verwijderde standaardwoorden
    excluded_default_words = form_data.get("excluded_default_words", [])  # Woorden uit de standaardlijst die de gebruiker wil uitsluiten
    model_id = form_data.get("model", None)
    language_level = form_data.get("language_level", "B1")  # Standaard B1 als niet gespecificeerd
    
    # Nieuwe parameters voor chunking en parallelle verwerking
    max_words_per_chunk = form_data.get("max_words_per_chunk", 15000)  # Standaard 15000 woorden per chunk
    max_tokens_per_paragraph = form_data.get("max_tokens_per_paragraph", 1500)  # Standaard 1500 tokens per paragraaf
    batch_size = form_data.get("batch_size", 20)  # Standaard 5 paragrafen parallel
    
    # Voeg standaard woorden toe die niet zijn uitgesloten door de gebruiker
    for word in DEFAULT_PRESERVED_WORDS:
        if word not in excluded_default_words and word not in preserved_words:
            preserved_words.append(word)
    
    if not input_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geen tekst opgegeven om te vertalen",
        )
    
    # Maak de system prompt voor het gekozen taalniveau
    if language_level == "B1":
        system_prompt = """Je taak is om onderstaande tekst zorgvuldig te analyseren en vervolgens te herschrijven naar helder, begrijpelijk Nederlands op taalniveau B1. Hierbij is het essentieel dat je de informatie zo letterlijk en nauwkeurig mogelijk weergeeft en de structuur en betekenis van de originele tekst behoudt, zonder belangrijke informatie weg te laten.

Houd je hierbij aan onderstaande richtlijnen:
-Gebruik korte en actieve zinnen.
-Vervang moeilijke woorden door eenvoudige, dagelijkse alternatieven.
-Vermijd technische termen en ambtelijke taal; als dit niet kan, leg deze dan uit met eenvoudige woorden of verduidelijk ze met een kort voorbeeld.
-Vermijd passieve en ingewikkelde grammaticale structuren.
-Maak abstracte begrippen concreet met duidelijke voorbeelden.

Gebruik als hulpmiddel onderstaande voorbeelden van woorden en hun eenvoudiger B1-alternatieven:
-Betreffende → Over
-Creëren → Ontwerpen, maken, vormen
-Prioriteit → Voorrang, voorkeur
-Relevant → Belangrijk
-Verstrekken → Geven

Controleer tot slot grondig of de vereenvoudigde versie een accurate weergave is van de oorspronkelijke inhoud.

Plaats jouw definitieve herschreven tekst altijd tussen <<< en >>> tekens. Als blijkt dat de tekst al volledig aan B1-niveau voldoet en niet verbeterd kan worden, neem deze dan letterlijk tussen <<< en >>> tekens over (bijvoorbeeld <<< Artikel 3.2 >>>)."""
    else:  # B2 taalniveau
        system_prompt = """Je taak is om onderstaande tekst zorgvuldig te analyseren en vervolgens te herschrijven naar helder, begrijpelijk Duits op taalniveau B2. Hierbij is het essentieel dat je de informatie zo letterlijk en nauwkeurig mogelijk weergeeft en de structuur en betekenis van de originele tekst behoudt, zonder belangrijke informatie weg te laten.

Houd je hierbij aan onderstaande richtlijnen voor B2-niveau:
-Gebruik duidelijke zinnen van gemiddelde lengte.
-Complexe zinnen mogen, maar zorg dat ze logisch opgebouwd zijn.
-Vaktermen mogen gebruikt worden als ze uitgelegd worden.
-Gebruik een mix van actieve en passieve zinnen waar passend.
-Abstracte begrippen zijn toegestaan maar moeten duidelijk zijn uit de context.

B2-niveau is iets complexer dan B1 en geschikt voor mensen met een redelijk goede taalvaardigheid. Je mag dus iets complexere woorden en zinsstructuren gebruiken dan bij B1, maar de tekst moet nog steeds toegankelijk blijven.

Controleer tot slot grondig of de herschreven versie een accurate weergave is van de oorspronkelijke inhoud.

Plaats jouw definitieve herschreven tekst altijd tussen <<< en >>> tekens. Als blijkt dat de tekst al volledig aan B2-niveau voldoet en niet verbeterd kan worden, neem deze dan letterlijk tussen <<< en >>> tekens over."""

    # Voeg instructies toe over woorden die niet vereenvoudigd moeten worden
    if preserved_words:
        system_prompt += f" De volgende woorden/termen mag je NIET vereenvoudigen of veranderen, gebruik ze exact zoals ze zijn: {', '.join(preserved_words)}."
    
    # Definieer verschillende temperatuurwaarden voor variatie
    temperatures = [0.5, 0.75, 1]
    
    # Functie om tekst op te splitsen in paragrafen
    def split_into_paragraphs(text, max_tokens=max_tokens_per_paragraph):
        # Als max_tokens None is, geef de hele tekst terug als één paragraaf
        if max_tokens is None:
            return [text]
            
        # Eerst splitsen op dubbele newlines (paragrafen)
        paragraphs = text.split("\n\n")
        
        # Resultaat lijst voor paragrafen die binnen token limiet vallen
        result_paragraphs = []
        current_paragraph = ""
        
        for paragraph in paragraphs:
            # Ruwe schatting van tokens (ongeveer 4 tekens per token)
            estimated_tokens = len(paragraph) / 4
            
            if estimated_tokens > max_tokens:
                # Als een enkele paragraaf te groot is, splits deze op zinnen
                sentences = paragraph.replace(". ", ".|").replace("! ", "!|").replace("? ", "?|").split("|")
                current_sentence_group = ""
                
                for sentence in sentences:
                    if not sentence:
                        continue
                    
                    estimated_group_tokens = (len(current_sentence_group) + len(sentence)) / 4
                    
                    if estimated_group_tokens > max_tokens and current_sentence_group:
                        result_paragraphs.append(current_sentence_group)
                        current_sentence_group = sentence
                    else:
                        if current_sentence_group:
                            current_sentence_group += " " + sentence
                        else:
                            current_sentence_group = sentence
                
                if current_sentence_group:
                    result_paragraphs.append(current_sentence_group)
            else:
                # Als huidige paragraaf + nieuwe paragraaf te groot wordt
                estimated_combined_tokens = (len(current_paragraph) + len(paragraph)) / 4
                
                if estimated_combined_tokens > max_tokens and current_paragraph:
                    result_paragraphs.append(current_paragraph)
                    current_paragraph = paragraph
                else:
                    if current_paragraph:
                        current_paragraph += "\n\n" + paragraph
                    else:
                        current_paragraph = paragraph
        
        # Voeg laatste paragraaf toe als die bestaat
        if current_paragraph:
            result_paragraphs.append(current_paragraph)
            
        return result_paragraphs
    
    # Functie om één versie van een paragraaf te genereren
    async def generate_paragraph_version(paragraph_index, paragraph, temp_index, temperature):
        chat_request = {
            "model": model_id,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Vertaal de volgende tekst naar {language_level}-taalniveau. Behoud de structuur en opmaak zoals alinea's en opsommingen:\n\n{paragraph}"
                }
            ],
            "temperature": temperature
        }
        
        # Gebruik de bestaande chat_completion functie
        response = await chat_completion(request, form_data=chat_request, user=user)
        
        # Extraheer de gegenereerde tekst uit de response
        generated_text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "paragraph_index": paragraph_index,
            "temp_index": temp_index,
            "text": generated_text,
            "temperature": temperature
        }
    
    # Voeg deze functie toe voor betere foutafhandeling
    async def safe_generate_paragraph_version(paragraph_index, paragraph, temp_index, temperature):
        try:
            # Voeg een timeout toe om vastlopen te voorkomen
            return await asyncio.wait_for(
                generate_paragraph_version(paragraph_index, paragraph, temp_index, temperature),
                timeout=60  # 60 seconden timeout
            )
        except asyncio.TimeoutError:
            # Bij timeout, geef een eenvoudige versie terug
            return {
                "paragraph_index": paragraph_index,
                "temp_index": temp_index,
                "text": f"<<< {paragraph} >>>",  # Originele tekst teruggeven
                "temperature": temperature
            }
        except Exception as e:
            # Bij andere fouten, log en geef origineel terug
            print(f"Fout bij genereren van paragraaf {paragraph_index}: {str(e)}")
            return {
                "paragraph_index": paragraph_index,
                "temp_index": temp_index,
                "text": f"<<< {paragraph} >>>",
                "temperature": temperature
            }
    
    # Functie om de beste versie van een paragraaf te selecteren
    async def select_best_version(paragraph_index, paragraph, versions):
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
        
        selection_response = await chat_completion(request, form_data=selection_request, user=user)
        selection_text = selection_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Extraheer het versienummer (1, 2 of 3)
        selected_version = 0  # Standaard eerste versie
        for i in range(1, 4):
            if str(i) in selection_text:
                selected_version = i - 1  # Aanpassen naar 0-gebaseerde index
                break
        
        return {
            "paragraph_index": paragraph_index,
            "original": paragraph,
            "translated": versions[selected_version]["text"],
            "selected_version": selected_version + 1,
            "temperature": versions[selected_version]["temperature"]
        }
    
    # Functie om content tussen delimiters te extraheren
    def extract_content(text):
        pattern = r'<<<(.*?)>>>'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text  # Return original if no delimiters found
    
    # Functie om preserved words intact te houden
    def enforce_preserved_words(translations: List[Dict[str, Any]], preserved_words: List[str]) -> List[Dict[str, Any]]:
        """Zorg ervoor dat preserved words niet worden vertaald."""
        for translation in translations:
            for word in preserved_words:
                # Gebruik regex om woorden exact te matchen en te vervangen
                translation["translated"] = re.sub(
                    rf"\b{re.escape(word)}\b", word, translation["translated"], flags=re.IGNORECASE
                )
        return translations
    
    # Functie om tekst in chunks van variabele grootte te verwerken
    async def process_text_in_chunks(text, max_words=max_words_per_chunk):
        # Als max_words None is, verwerk de hele tekst in één keer
        if max_words is None:
            return await process_single_chunk(text, batch_size)
            
        # Eenvoudigere en betrouwbaardere chunking-methode
        chunks = []
        words = text.split()
        total_words = len(words)
        
        # Verdeel in chunks van max_words
        for i in range(0, total_words, max_words):
            chunk = ' '.join(words[i:i+max_words])
            chunks.append(chunk)
        
        # Verwerk elke chunk en combineer de resultaten
        translated_chunks = []
        for chunk in chunks:
            translated_chunk = await process_single_chunk(chunk, batch_size)
            translated_chunks.append(translated_chunk)
        
        return "\n\n".join(translated_chunks)
    
    # Functie om een enkele chunk tekst te verwerken
    async def process_single_chunk(chunk_text, batch_size=batch_size):
        # Split de chunk in paragrafen
        paragraphs = split_into_paragraphs(chunk_text, max_tokens_per_paragraph)
        all_selections = []
        
        # Als batch_size None is, verwerk alle paragrafen tegelijk
        if batch_size is None:
            # Genereer versies voor alle paragrafen tegelijk
            all_generation_tasks = []
            for p_idx, paragraph in enumerate(paragraphs):
                for t_idx, temp in enumerate(temperatures):
                    all_generation_tasks.append(safe_generate_paragraph_version(p_idx, paragraph, t_idx, temp))
            
            all_generated_versions = await asyncio.gather(*all_generation_tasks)
            
            # Organiseer de gegenereerde versies per paragraaf
            paragraph_versions = {}
            for version in all_generated_versions:
                p_idx = version["paragraph_index"]
                if p_idx not in paragraph_versions:
                    paragraph_versions[p_idx] = [None, None, None]
                paragraph_versions[p_idx][version["temp_index"]] = version
            
            # Selecteer beste versies voor alle paragrafen
            all_selection_tasks = []
            for p_idx, paragraph in enumerate(paragraphs):
                versions = paragraph_versions[p_idx]
                all_selection_tasks.append(select_best_version(p_idx, paragraph, versions))
            
            all_selections = await asyncio.gather(*all_selection_tasks)
        else:
            # Verwerk paragrafen in batches om geheugengebruik te beperken
            for i in range(0, len(paragraphs), batch_size):
                batch_paragraphs = paragraphs[i:i+batch_size]
                
                # Genereer versies voor deze batch
                batch_generation_tasks = []
                for p_idx, paragraph in enumerate(batch_paragraphs):
                    for t_idx, temp in enumerate(temperatures):
                        batch_generation_tasks.append(safe_generate_paragraph_version(i+p_idx, paragraph, t_idx, temp))
                
                batch_generated_versions = await asyncio.gather(*batch_generation_tasks)
                
                # Organiseer de gegenereerde versies per paragraaf
                paragraph_versions = {}
                for version in batch_generated_versions:
                    p_idx = version["paragraph_index"]
                    if p_idx not in paragraph_versions:
                        paragraph_versions[p_idx] = [None, None, None]
                    paragraph_versions[p_idx][version["temp_index"]] = version
                
                # Selecteer beste versies voor deze batch
                batch_selection_tasks = []
                for p_idx, paragraph in enumerate(batch_paragraphs):
                    versions = paragraph_versions[i+p_idx]
                    batch_selection_tasks.append(select_best_version(i+p_idx, paragraph, versions))
                
                batch_selections = await asyncio.gather(*batch_selection_tasks)
                all_selections.extend(batch_selections)
        
        # Sorteer de resultaten op paragraaf index
        all_selections.sort(key=lambda x: x["paragraph_index"])
        
        # Extraheer content en behoud preserved words
        for result in all_selections:
            result["translated"] = extract_content(result["translated"])
        
        all_selections = enforce_preserved_words(all_selections, preserved_words)
        
        # Combineer de vertaalde paragrafen
        combined_text = "\n\n".join([result["translated"] for result in all_selections])
        
        return combined_text
    
    try:
        # Voeg een log toe voor het begin van de verwerking
        print(f"Start verwerking van tekst met {len(input_text.split())} woorden")
        print(f"Configuratie: max_words_per_chunk={max_words_per_chunk}, max_tokens_per_paragraph={max_tokens_per_paragraph}, batch_size={batch_size}")
        
        # Verwerk de volledige tekst met de opgegeven configuratie
        combined_translated_text = await process_text_in_chunks(input_text, max_words_per_chunk)
        
        print("Verwerking voltooid")
        
        # Bereid de uiteindelijke response voor
        final_response = {
            "choices": [
                {
                    "message": {
                        "content": combined_translated_text,
                        "role": "assistant"
                    },
                    "index": 0,
                    "finish_reason": "stop"
                }
            ],
            "model": model_id,
            "object": "chat.completion",
            "usage": {
                "completion_tokens": 0,
                "prompt_tokens": 0,
                "total_tokens": 0
            },
            "meta": {
                "processed_in_chunks": max_words_per_chunk is not None and len(input_text.split()) > max_words_per_chunk,
                "total_words": len(input_text.split()),
                "configuration": {
                    "max_words_per_chunk": max_words_per_chunk,
                    "max_tokens_per_paragraph": max_tokens_per_paragraph,
                    "batch_size": batch_size
                }
            }
        }
        
        return final_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )