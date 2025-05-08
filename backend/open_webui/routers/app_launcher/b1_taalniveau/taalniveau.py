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

def split_into_chunks(text: str, max_tokens: int = 1500) -> List[str]:
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
        # Return empty strings as they might be intentional paragraph breaks
        return {"index": index, "temperature": temperature, "text": chunk, "error": None} # Ensure error key exists

    preserved_words_text = ", ".join(f"'{word}'" for word in preserved_words) if preserved_words else "geen"
    # Updated system prompt with instruction for bold text and preserved words
    generation_system_prompt = f"""Je taak is om de volgende tekst te analyseren en te herschrijven naar een versie die voldoet aan het {language_level}-taalniveau.
Hierbij is het belangrijk om de informatie zo letterlijk mogelijk over te brengen en de structuur zoveel mogelijk te behouden, zonder onnodige weglatingen.
Het {language_level}-niveau kenmerkt zich door duidelijk en eenvoudig taalgebruik, geschikt voor een breed publiek met basisvaardigheden in de taal.

Hier zijn enkele richtlijnen om je te helpen bij deze taak:
- Gebruik korte zinnen en vermijd lange, complexe zinsconstructies.
- Vervang moeilijke woorden door meer gangbare alternatieven.
- Leg technische termen en (ambtelijk) jargon uit in eenvoudige bewoordingen.
- Gebruik actieve zinsconstructies waar mogelijk.
- Vermijd passieve zinnen en ingewikkelde grammaticale constructies.
- Gebruik concrete voorbeelden om abstracte concepten te verduidelijken.

Hier zijn enkele voorbeelden van woorden op C1-niveau en hun eenvoudigere {language_level}-equivalenten:
- Betreffende -> Over
- Creëren -> Ontwerpen, vormen, vormgeven, maken
- Prioriteit -> Voorrang, voorkeur
- Relevant -> Belangrijk
- Verstrekken -> Geven

BELANGRIJK: De volgende woorden moeten exact behouden blijven en mogen NIET vereenvoudigd worden: {preserved_words_text}.

Zorg ervoor dat de hoofdboodschap van de tekst behouden blijft en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.
BELANGRIJK: Tekst tussen dubbele sterretjes (zoals **dit**) moet ook vereenvoudigd worden naar {language_level}-niveau. Behoud de dubbele sterretjes rond de vereenvoudigde tekst in de output. Dit geldt ook voor kopjes of andere belangrijke termen die zo gemarkeerd zijn.
Zorg ervoor dat de hoofdboodschap van de tekst behouden blijft en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.
Gebruik deze instructies om de tekst te vereenvoudigen en zorg ervoor dat deze voldoet aan het {language_level}-taalniveau.
Plaats de verbeterde paragraaf tussen "<<<" en ">>>" tekens. Als de tekst te kort is om te verbeteren neem je de tekst een-op-een over en plaats deze tussen de genoemende tekens, bijv. "<<< **Artikel 3.2** >>>"."""

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

    # Filter successful versions (generated_versions now contain the full LLM output from generate_version)
    successful_versions = [v for v in generated_versions if v.get("error") is None and v.get("text", "").strip()]

    # Handle cases with no successful versions or only empty results
    if not successful_versions:
         print(f"Warning: No successful versions generated for chunk {index}. Returning original chunk.")
         return {"index": index, "text": original_chunk, "selection_error": "No successful versions to select from."}

    preserved_words_text = ", ".join(f"'{word}'" for word in preserved_words) if preserved_words else "geen"
    # System prompt for selection remains the same
    selection_system_prompt = f"""Je taak is om de volgende tekst te analyseren en te herschrijven naar een versie die voldoet aan het {language_level}-taalniveau.
Hierbij is het belangrijk om de informatie zo letterlijk mogelijk over te brengen en de structuur zoveel mogelijk te behouden, zonder onnodige weglatingen.
Het {language_level}-niveau kenmerkt zich door duidelijk en eenvoudig taalgebruik, geschikt voor een breed publiek met basisvaardigheden in de taal.

Hier zijn enkele richtlijnen om je te helpen bij deze taak:
- Gebruik korte zinnen en vermijd lange, complexe zinsconstructies.
- Vervang moeilijke woorden door meer gangbare alternatieven.
- Leg technische termen en (ambtelijk) jargon uit in eenvoudige bewoordingen.
- Gebruik actieve zinsconstructies waar mogelijk.
- Vermijd passieve zinnen en ingewikkelde grammaticale constructies.
- Gebruik concrete voorbeelden om abstracte concepten te verduidelijken.

Hier zijn enkele voorbeelden van woorden op C1-niveau en hun eenvoudigere {language_level}-equivalenten:
- Betreffende -> Over
- Creëren -> Ontwerpen, vormen, vormgeven, maken
- Prioriteit -> Voorrang, voorkeur
- Relevant -> Belangrijk
- Verstrekken -> Geven

BELANGRIJK: De volgende woorden moeten exact behouden blijven en mogen NIET vereenvoudigd worden: {preserved_words_text}.

Zorg ervoor dat de inhoud en nuances van de oorspronkelijke tekst behouden blijven en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.
BELANGRIJK: Zorg ervoor dat tekst tussen dubbele sterretjes (zoals **dit**) ook vereenvoudigd is naar {language_level}-niveau in de definitieve versie. Behoud de dubbele sterretjes rond de vereenvoudigde tekst in de output. Dit geldt ook voor kopjes of andere belangrijke termen die zo gemarkeerd zijn.

Zorg ervoor dat de inhoud en nuances van de oorspronkelijke tekst behouden blijven en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.
Je ontvangt de originele paragraaf, samen met enkele varianten van deze tekst in eenvoudigere taal ({language_level}). Deze varianten kunnen nog de "<<<" en ">>>" tekens bevatten. Het is jouw taak om tot een definitieve {language_level}-versie te komen ZONDER deze tekens, maar wel met behoud van **dikgedrukte** tekst.

Plaats de definitieve, verbeterde paragraaf tussen "<<<" en ">>>" tekens. Als de tekst te kort is om te verbeteren neem je de tekst een-op-een over en plaats deze tussen de genoemende tekens, bijv. "<<< **Artikel 3.2** >>>".""" # Prompt still asks selection model to use <<< >>>

    variants_text = ""
    for i, version_data in enumerate(successful_versions):
        # Pass the full text (potentially with <<< >>>) from generate_version
        variant_text = version_data.get('text', '')
        variants_text += f"Variant {i+1} (gegenereerd met temperature={version_data['temperature']}):\n{variant_text}\n---\n" # Pass the raw text

    selection_user_content = f"""Originele Paragraaf:
---
{original_chunk}
---

Gegenereerde {language_level} Varianten (kunnen '<<<' en '>>>' bevatten):
---
{variants_text}
Kies de beste variant of combineer/verbeter ze tot de definitieve {language_level}-versie, geplaatst tussen <<< en >>>. Verwijder de <<< en >>> uit de input varianten in de uiteindelijke output. Zorg ervoor dat tekst binnen **dubbele sterretjes** ook vereenvoudigd is en behoud de sterretjes in de output.
BELANGRIJK: Zorg ervoor dat de volgende woorden exact behouden blijven en NIET vereenvoudigd worden: {preserved_words_text}.""" # Updated user content instruction

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

    chunks = split_into_chunks(data.text)
    num_chunks = len(chunks)
    temperatures = [1.0, 0.8, 0.6]

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