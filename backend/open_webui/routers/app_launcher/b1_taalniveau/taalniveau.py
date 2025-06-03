from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from typing import List, Any 
from pydantic import BaseModel
import asyncio
import json
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.auth import get_current_user
import tiktoken
import re

router = APIRouter()

def split_into_chunks(text: str, max_tokens: int = 2500) -> List[str]:
    """Split text into chunks of approximately max_tokens"""
    encoding = tiktoken.get_encoding("cl100k_base")
    paragraphs = text.split('\n')
    chunks = []
    current_chunk_parts = []
    current_length = 0

    for paragraph in paragraphs:
        if not paragraph.strip():
            if current_chunk_parts:
                chunks.append("\n".join(current_chunk_parts))
                current_chunk_parts = []
                current_length = 0
            # Decide whether to keep empty lines as chunks or skip them
            # Keeping them preserves paragraph structure more accurately
            chunks.append("")
            continue

        words = paragraph.split()
        paragraph_parts = []
        para_current_length = 0

        for word in words:
            # Estimate token count; consider caching encoding.encode for performance if needed
            # Using len(encoding.encode(word)) per word can be slow for very long texts
            try:
                word_tokens = len(encoding.encode(word))
            except Exception: # Handle potential errors during encoding if needed
                word_tokens = len(word) // 3 # Rough estimate as fallback

            # Check if adding the next word exceeds max_tokens for the current chunk or paragraph part
            if (current_length + para_current_length + word_tokens > max_tokens and current_chunk_parts) or \
               (para_current_length + word_tokens > max_tokens and paragraph_parts):
                # Finish current chunk if it exists
                if current_chunk_parts:
                    chunks.append("\n".join(current_chunk_parts))
                    current_chunk_parts = []
                    current_length = 0
                # Finish current paragraph part if it became a chunk on its own
                if paragraph_parts:
                    chunks.append(" ".join(paragraph_parts))
                    paragraph_parts = [word] # Start new paragraph part with current word
                    para_current_length = word_tokens
                else: # Word itself is too long or first word of a new chunk
                     chunks.append(word)
                     para_current_length = 0 # Reset para length as this word forms a chunk
            else:
                paragraph_parts.append(word)
                para_current_length += word_tokens

        # Add the remaining part of the paragraph to the current chunk
        if paragraph_parts:
            paragraph_text = " ".join(paragraph_parts)
            # Recalculate tokens for the whole paragraph part for accuracy
            try:
                paragraph_tokens = len(encoding.encode(paragraph_text))
            except Exception:
                paragraph_tokens = len(paragraph_text) // 3 # Fallback estimate

            # Check if adding this paragraph exceeds the limit for the current chunk
            if current_length + paragraph_tokens > max_tokens and current_chunk_parts:
                 chunks.append("\n".join(current_chunk_parts))
                 current_chunk_parts = [paragraph_text] # Start new chunk with this paragraph
                 current_length = paragraph_tokens
            else:
                 current_chunk_parts.append(paragraph_text)
                 current_length += paragraph_tokens

    # Add the last remaining chunk
    if current_chunk_parts:
        chunks.append("\n".join(current_chunk_parts))

    # Filter out potential None values, though the logic aims to avoid them
    return [chunk for chunk in chunks if chunk is not None]


async def generate_version(request: Request, chunk: str, model: str, preserved_words: List[str], language_level: str, user: Any, index: int, temperature: float) -> dict:
    """Generate a single version of simplified text for a specific temperature and return with index and temperature"""
    if not chunk or chunk.isspace():
        return {"index": index, "temperature": temperature, "text": chunk, "error": None}

    preserved_words_text = ", ".join(f"'{word}'" for word in preserved_words) if preserved_words else "geen"
    
    generation_system_prompt = f"""Je taak is om de volgende tekst te analyseren en te herschrijven naar een versie die voldoet aan het {language_level}-taalniveau.
Behoud de structuur zoveel mogelijk.

Richtlijnen {language_level}-niveau:
- Korte zinnen.
- Eenvoudige, alledaagse woorden.
- Leg jargon uit.
- Actieve zinsconstructies.
- Concrete voorbeelden.

Voorbeelden C1 -> {language_level}:
- Betreffende -> Over
- Creëren -> Maken, ontwerpen, vormen
- Prioriteit -> Voorrang, voorkeur
- Relevant -> Belangrijk
- Verstrekken -> Geven

BELANGRIJK - Te behouden woorden: De volgende woorden/termen moeten exact behouden blijven en mogen NIET vereenvoudigd worden: {preserved_words_text}.

BELANGRIJK - Omgaan met **dikgedrukte** tekst (gemarkeerd met dubbele asterisken):
1.  Als de tekst binnen **...** een KOPJE is (bijvoorbeeld: het staat op een eigen regel, is kort en introduceert een nieuwe sectie):
    a. Vereenvoudig de inhoud van het kopje naar {language_level}-niveau.
    b. Formatteer het vereenvoudigde kopje in de output als `<strong>Vereenvoudigd Kopje</strong>`.
    c. Als een 'te behouden woord' deel is van het kopje, blijft dat woord ongewijzigd binnen de `<strong>` tags.
2.  Als de tekst binnen **...** GEEN kopje is (maar een ander benadrukt woord of zinsdeel):
    a. Vereenvoudig de inhoud naar {language_level}-niveau.
    b. Geef deze vereenvoudigde inhoud weer als normale tekst, ZONDER `<strong>` tags of andere vetgedrukte opmaak. Verwijder de `**` markeringen.

Zorg dat de hoofdboodschap van de tekst behouden blijft en dat de vereenvoudigde versie een accurate weergave is van de oorspronkelijke inhoud.
Plaats de volledige, verbeterde paragraaf tussen "<<<" en ">>>" tekens.
Voorbeeld input:
"**Algemene Inleiding**
Dit is een **zeer** complexe zin die **onmiddellijk** aandacht behoeft."
Mogelijke output (als "Algemene Inleiding" een kopje is en "zeer" en "onmiddellijk" niet):
"<<< <strong>Inleiding</strong>
Dit is een moeilijke zin die nu aandacht nodig heeft. >>>"
Als de tekst te kort is om te verbeteren (bijv. alleen een kopje dat al B1 is, of een 'te behouden woord' als kopje), neem de tekst dan over met de juiste formattering. Bijvoorbeeld, input: "**Artikel 3.2**", output (als "Artikel 3.2" een te behouden woord is en als kopje wordt gezien): "<<< <strong>Artikel 3.2</strong> >>>".
"""

    form_data = {
        "model": model,
        "stream": False, # Ensure streaming is off for this internal call
        "temperature": temperature, # Add temperature parameter
        "messages": [
            {
                "role": "system",
                "content": generation_system_prompt # Use the updated prompt
            },
            {
                "role": "user",
                "content": chunk
            }
        ]
    }

    try:
        # Assuming generate_chat_completion handles potential API errors gracefully
        # and accepts the 'temperature' key in form_data
        response = await generate_chat_completion(request=request, form_data=form_data, user=user)
        llm_output = response['choices'][0]['message']['content']

        # --- REMOVED EXTRACTION LOGIC ---
        # The llm_output now contains the full response, potentially including <<< >>>
        simplified_text = llm_output.strip()
        # Optional: Still clean potential markdown code blocks if the model adds them unexpectedly
        simplified_text = re.sub(r'^```[a-zA-Z]*\n?', '', simplified_text)
        simplified_text = re.sub(r'\n?```$', '', simplified_text)
        # --- END REMOVED EXTRACTION LOGIC ---


        return {"index": index, "temperature": temperature, "text": simplified_text, "error": None} # Return the full (cleaned) output
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error processing chunk {index} with model {model} at temperature {e}")
        # Return the original chunk in case of an error to avoid data loss, include temperature and error info
        return {"index": index, "temperature": temperature, "text": chunk, "error": str(e)}

async def select_best_version(request: Request, original_chunk: str, generated_versions: List[dict], model: str, language_level: str, preserved_words: List[str], user: Any, index: int) -> dict: # Added preserved_words
    """Selects the best version from generated texts using an LLM based on a specific prompt."""

    successful_versions = [v for v in generated_versions if v.get("error") is None and v.get("text", "").strip()]

    if not successful_versions:
         print(f"Warning: No successful versions generated for chunk {index}. Returning original chunk.")
         return {"index": index, "text": original_chunk, "selection_error": "No successful versions to select from."}

    preserved_words_text = ", ".join(f"'{word}'" for word in preserved_words) if preserved_words else "geen"
    
    selection_system_prompt = f"""Je taak is het selecteren en eventueel combineren van de beste {language_level}-versie uit de aangeleverde varianten van een originele paragraaf. De definitieve tekst moet voldoen aan {language_level}-taalniveau.

Richtlijnen {language_level}-niveau:
- Korte zinnen, eenvoudige woorden.
- Jargon uitleggen.
- Actieve zinnen, concreet.

BELANGRIJK - Te behouden woorden: De volgende woorden/termen moeten exact behouden blijven en mogen NIET vereenvoudigd worden: {preserved_words_text}.

BELANGRIJK - Definitieve formattering van **dikgedrukte** tekst (oorspronkelijk gemarkeerd met dubbele asterisken `**...**`):
1.  Identificeer KOPJES in de originele tekst (vaak op een eigen regel, kort, introducerend een sectie).
    a. Zorg dat de inhoud van deze kopjes vereenvoudigd is naar {language_level}-niveau in de gekozen/gecombineerde variant.
    b. Formatteer deze vereenvoudigde kopjes in de output als `<strong>Vereenvoudigd Kopje</strong>`.
    c. 'Te behouden woorden' binnen kopjes blijven ongewijzigd binnen de `<strong>` tags.
2.  Voor andere tekst die oorspronkelijk **dikgedrukt** was (maar GEEN kopje):
    a. Zorg dat de inhoud vereenvoudigd is naar {language_level}-niveau.
    b. Geef deze vereenvoudigde inhoud weer als normale tekst, ZONDER `<strong>` tags of andere vetgedrukte opmaak. Verwijder eventuele overgebleven `**` markeringen.

De input varianten kunnen nog `<<<` en `>>>` tekens bevatten en mogelijk `<strong>` tags of `**` markup van de vorige stap.
Jouw taak is om tot één definitieve, schone {language_level}-versie te komen.

Plaats de definitieve, verbeterde paragraaf tussen "<<<" en ">>>" tekens. Zorg ervoor dat alleen de geïdentificeerde en vereenvoudigde kopjes `<strong>` HTML-tags gebruiken in de uiteindelijke output binnen de `<<<` en `>>>`. Alle andere `**` markeringen moeten verwijderd zijn.
"""

    variants_text = ""
    for i, version_data in enumerate(successful_versions):
        variant_text = version_data.get('text', '')
        variants_text += f"Variant {i+1} (gegenereerd met temperature={version_data['temperature']}):\n{variant_text}\n---\n"

    selection_user_content = f"""Originele Paragraaf:
---
{original_chunk}
---

Gegenereerde {language_level} Varianten (kunnen '<<<', '>>>', '**', of '<strong>' bevatten):
---
{variants_text}
---
Selecteer/combineer tot de beste {language_level}-versie.
Pas de formatteringsregels voor KOPJES (`<strong>Kopje</strong>`) en andere **dikgedrukte** tekst (verwijder `**`, normale tekst) correct toe.
Behoud de 'te behouden woorden': {preserved_words_text}.
Plaats de definitieve tekst tussen `<<<` en `>>>`.
"""

    form_data = {
        "model": model,
        "stream": False,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": selection_system_prompt},
            {"role": "user", "content": selection_user_content}
        ]
    }

    try:
        response = await generate_chat_completion(request=request, form_data=form_data, user=user)
        llm_output = response['choices'][0]['message']['content']

        # Extract text between <<< and >>> for the FINAL output from the selection step
        match = re.search(r'<<<([\s\S]*?)>>>', llm_output, re.DOTALL)
        if match:
            final_text = match.group(1).strip()
            return {"index": index, "text": final_text}
        else:
            # Fallback if the SELECTION model didn't use <<< >>>
            print(f"Warning: Could not parse '<<<' and '>>>' from selection output for chunk {index}. Output was: {llm_output}")
            # Fallback: Try to return the raw output from the selection model, hoping it's usable.
            # Or revert to the first generated version (which might still have <<< >>>)
            # Let's return the raw selection output as fallback here.
            fallback_text = llm_output.strip()
            return {"index": index, "text": fallback_text, "selection_warning": "Could not parse final version delimiters from selection output."}

    except Exception as e:
        print(f"Error during selection step for chunk {index} with model {model}: {e}")
        # Fallback in case of selection error - return original chunk
        return {"index": index, "text": original_chunk, "selection_error": str(e)}


class SimplifyTextRequest(BaseModel):
    text: str
    model: str
    preserved_words: list[str] = []
    language_level: str = "B1"

@router.post("/translate")
async def simplify_text_endpoint(request: Request, data: SimplifyTextRequest, user = Depends(get_current_user)):
    """Endpoint to simplify text to B1/B2 level. Generates 3 versions per chunk, then selects the best."""

    # --- START: Automatically detect and add law articles to preserved_words ---
    # Regex to find common law article mentions (e.g., Artikel 1, art. 2.3, Artikel 3:16)
    # This regex aims for "Artikel X", "Artikel X.Y", "Artikel X:Y", "Artikel Xa", "artikel X lid Y" (captures "artikel X")
    law_article_regex = r'\b(?:[Aa]rtikel|[Aa]rt\.)\s*\d+(?:[.:]\w+)*\b'
    
    found_articles = re.findall(law_article_regex, data.text)
    
    # Combine with user-provided preserved words, ensuring uniqueness
    current_preserved_words = set(data.preserved_words)
    for article in found_articles:
        current_preserved_words.add(article)
    
    data.preserved_words = list(current_preserved_words)
    # --- END: Automatically detect and add law articles to preserved_words ---

    chunks = split_into_chunks(data.text)
    num_chunks = len(chunks)
    temperatures = [1.0, 1.0, 1.0]

    if num_chunks == 0:
        async def empty_stream():
             yield json.dumps({"total_chunks": 0}) + "\n"
             if False: yield None
        return StreamingResponse(empty_stream(), media_type="application/x-ndjson")

    async def stream_results():
        # Send total chunk count first (client expects one final result per chunk)
        yield json.dumps({"total_chunks": num_chunks}) + "\n"

        generation_tasks = []
        for i, chunk in enumerate(chunks):
            for temp in temperatures:
                generation_tasks.append(
                    generate_version(request, chunk, data.model, data.preserved_words, data.language_level, user, i, temp)
                )

        # Use dictionaries to store results and track completion
        chunk_results = {i: [] for i in range(num_chunks)}
        tasks_outstanding = {i: len(temperatures) for i in range(num_chunks)}
        selection_tasks = [] # Store tasks for the selection step

        # Process generation results as they complete
        for future in asyncio.as_completed(generation_tasks):
            try:
                gen_result = await future
                idx = gen_result['index']
                chunk_results[idx].append(gen_result)
                tasks_outstanding[idx] -= 1

                # If all versions for a chunk are generated, create selection task
                if tasks_outstanding[idx] == 0:
                    original_chunk = chunks[idx]
                    versions = chunk_results[idx]
                    # Schedule the selection task
                    selection_tasks.append(
                        select_best_version(request, original_chunk, versions, data.model, data.language_level, data.preserved_words, user, idx) # Added preserved_words
                    )
                    # Optional: Clean up memory if chunks are very large
                    # del chunk_results[idx] # Be careful if original_chunk is needed elsewhere

            except Exception as e:
                 # Handle errors during the await future itself (less likely if generate_version catches errors)
                 print(f"Error awaiting generation task result: {e}")
                 # Consider how to handle this failure downstream. Maybe skip selection for this chunk?
                 # For now, it might prevent the selection task from being scheduled if an error occurs here.
                 pass # Continue processing other tasks

        # Process selection results as they complete and yield them
        for future in asyncio.as_completed(selection_tasks):
             try:
                 final_result = await future
                 # --- DOUBLE CHECK and REMOVE DELIMITERS ---
                 if 'text' in final_result and isinstance(final_result['text'], str):
                     # Remove <<< and >>> just in case they slipped through selection/parsing
                     final_result['text'] = final_result['text'].replace('<<<', '').replace('>>>', '').strip()
                 # --- END DOUBLE CHECK ---
                 yield json.dumps(final_result) + "\n"
             except Exception as e:
                 print(f"Error awaiting or processing selection task result: {e}")
                 # Decide how to inform the client about selection failure
                 # Example: yield json.dumps({"index": final_result.get('index', -1), "error": f"Processing failed after selection: {e}"}) + "\n"
                 # Current select_best_version tries to return fallback text with error info.


    return StreamingResponse(stream_results(), media_type="application/x-ndjson")