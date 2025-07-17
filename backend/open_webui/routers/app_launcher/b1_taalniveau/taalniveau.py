from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from typing import List, Any 
from pydantic import BaseModel
import asyncio
import json
import os
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.auth import get_current_user
import tiktoken
import re

router = APIRouter()

# --- START: Language Level Specific Prompt Data ---
LEVEL_SPECIFIC_PROMPTS = {
    "B1": {
        "examples_intro": "Hier zijn enkele voorbeelden van woorden op C1-niveau en hun eenvoudigere B1-equivalenten:",
        "examples_list": [
            "- Betreffende -> Over",
            "- Creëren -> Ontwerpen, vormen, vormgeven, maken",
            "- Prioriteit -> Voorrang, voorkeur",
            "- Relevant -> Belangrijk",
            "- Verstrekken -> Geven"
        ],
        "level_description": "Het B1-niveau kenmerkt zich door duidelijk en eenvoudig taalgebruik, geschikt voor een breed publiek met basisvaardigheden in de taal.",
        "selection_example": {
            "input": (
                "Originele paragraaf:\n"
                "**Algemene Inleiding**\n"
                "Dit is een **zeer** complexe zin die **onmiddellijk** aandacht behoeft.\n"
                "Variant 1 (vereenvoudigd):\n"
                "**Algemene Inleiding**\n"
                "Deze zin is erg moeilijk en heeft meteen aandacht nodig.\n"
                "Variant 2 (vereenvoudigd):\n"
                "**Algemene Inleiding**\n"
                "Dit is een ingewikkelde zin die nu aandacht moet krijgen."
            ),
            "output": (
                "<<< <strong>Algemene Inleiding</strong>\n"
                "Dit is een moeilijke zin die nu aandacht nodig heeft.>>>"
            )
        }
    },
    "B2": {
        "examples_intro": "Hier zijn enkele voorbeelden van woorden op C2-niveau en hun eenvoudigere B2-equivalenten:",
        "examples_list": [
            "- Faciliteren -> Mogelijk maken",
            "- Implementatie -> Uitvoering",
            "- Effectueren -> Realiseren",
            "- Complexiteit -> Moeilijkheidsgraad",
            "- Desalniettemin -> Toch"
        ],
        "level_description": "Het B2-niveau kenmerkt zich door helder en gedetailleerd taalgebruik, geschikt voor een publiek met gevorderde taalvaardigheden. De tekst moet toegankelijk zijn zonder overmatig gebruik van complexe termen, gericht op lezers die bekend zijn met de basisprincipes van de taal en in staat zijn om zowel praktische als theoretische onderwerpen te begrijpen.",
        "selection_example": {
            "input": (
                "Originele paragraaf:\n"
                "**Beleidscontext**\n"
                "Binnen de huidige context is de **implementatie** van aanvullende maatregelen van cruciaal belang.\n"
                "Variant 1 (vereenvoudigd):\n"
                "**Beleidscontext**\n"
                "In deze situatie is het belangrijk extra maatregelen uit te voeren.\n"
                "Variant 2 (vereenvoudigd):\n"
                "**Beleidscontext**\n"
                "Het is nu nodig om meer maatregelen mogelijk te maken."
            ),
            "output": (
                "<<< <strong>Beleidscontext</strong>\n"
                "In deze situatie is het belangrijk dat extra maatregelen uitgevoerd worden.>>>"
            )
        }
    }
    # Voeg eventueel andere niveaus toe (C1, C2) volgens bovenstaand patroon.
}

def get_language_specific_text(language_level: str, key: str, default_level="B1"):
    """Haalt specifieke tekst op voor een taalniveau, met een fallback."""
    level_data = LEVEL_SPECIFIC_PROMPTS.get(language_level, LEVEL_SPECIFIC_PROMPTS.get(default_level))
    return level_data.get(key, "")

def build_generation_prompt(language_level, preserved_words_text):
    level_description = get_language_specific_text(language_level, "level_description")
    examples_intro = get_language_specific_text(language_level, "examples_intro")
    examples = "\n".join(get_language_specific_text(language_level, "examples_list"))
    prompt = f"""Je taak is om de onderstaande tekst te herschrijven, zodat deze geschikt is voor taalniveau {language_level}.
    {level_description}

    Richtlijnen:
    - Breng de informatie zo letterlijk mogelijk over; behoud de structuur.
    - Gebruik korte, duidelijke zinnen.
    - Vervang moeilijke woorden door eenvoudige alternatieven.
    - Licht technische termen of jargon toe in eenvoudige bewoordingen.
    - Gebruik zoveel mogelijk de actieve vorm (vermijd de passieve vorm).
    - Vermijd ingewikkelde grammatica.
    - Geef concrete voorbeelden als dat helpt om abstracte concepten duidelijk te maken.
    - Zorg dat de hoofdboodschap en de inhoud van de tekst volledig behouden blijven.

    {examples_intro}
    {examples}

    Let op:
    - Bepaalde termen moeten ongewijzigd blijven: {preserved_words_text}.
    - Dikgedrukte tekst (gemarkeerd met '**...**'):
        1. Als dit een kopje is (aparte regel): vereenvoudig waar nodig, gebruik <strong>Kopje</strong>.
        2. Anders: vereenvoudig, maar geef weer als gewone tekst zónder dikgedrukte opmaak of '**'.

    Plaats de volledige output tussen '<<<' en '>>>'.
    """
    return "\n".join(line.strip() for line in prompt.splitlines() if line.strip())  # Verwijdert overtollige whitespaces

def build_selection_prompt(language_level, preserved_words_text):
    level_description = get_language_specific_text(language_level, "level_description")
    selection_example = get_language_specific_text(language_level, "selection_example", default_level="B1")
    prompt = f"""Je taak is om uit de volgende aangeleverde varianten (en het origineel) de beste {language_level}-versie samen te stellen. Je mag hiervoor onderdelen combineren, zolang:
    - De hoofdboodschap en informatie van het origineel zo goed mogelijk behouden worden;
    - De tekst volledig voldoet aan {language_level}-taalniveau.

    {level_description}

    Richtlijnen:
    - Gebruik korte, duidelijke zinnen. Vermijd lange of complexe zinsconstructies.
    - Vervang moeilijke woorden door meer gangbare alternatieven.
    - Leg technische termen en (vak)jargon uit in eenvoudige bewoordingen.
    - Gebruik de actieve vorm waar mogelijk.
    - Vermijd passieve zinnen en ingewikkelde grammatica.
    - Maak gebruik van concrete voorbeelden indien nuttig.
    - Behoud de logische structuur en samenhang.

    Let op:
    - Bepaalde woorden moeten worden behouden: {preserved_words_text}.
    - Vetgedrukte tekst (met '**...**'):
        1. Als het een kopje/titel is (aparte regel): vereenvoudig en gebruik <strong>Kopje</strong>.
        2. Anders: vereenvoudig, maar geen vetgedrukte opmaak of '**'.

    Output:
    - Plaats uitsluitend de samengestelde, definitieve versie tussen \"<<<\" en \">>>\", zonder extra uitleg.

    Voorbeeld:
    Input:
    {selection_example.get('input', '')}

    Output:
    {selection_example.get('output', '')}
    """
    return "\n".join(line.strip() for line in prompt.splitlines() if line.strip())  # Verwijdert overtollige whitespaces
# --- END: Language Level Specific Prompt Data ---

def split_into_chunks(text: str, max_tokens) -> List[str]:
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

    preserved_words_text = "; ".join(f"'{word}'" for word in preserved_words) if preserved_words else "Geen"
    
    generation_system_prompt = build_generation_prompt(language_level, preserved_words_text)

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
        print(f"Error processing chunk {index} with model {model} at temperature {temperature}: {e}")
        # Return the original chunk in case of an error to avoid data loss, include temperature and error info
        return {"index": index, "temperature": temperature, "text": chunk, "error": str(e)}

async def select_best_version(request: Request, original_chunk: str, generated_versions: List[dict], model: str, language_level: str, preserved_words: List[str], user: Any, index: int) -> dict: # Added preserved_words
    """Selects the best version from generated texts using an LLM based on a specific prompt."""

    successful_versions = [v for v in generated_versions if v.get("error") is None and v.get("text", "").strip()]

    if not successful_versions:
         print(f"Warning: No successful versions generated for chunk {index}. Returning original chunk.")
         return {"index": index, "text": original_chunk, "selection_error": "No successful versions to select from."}

    preserved_words_text = ", ".join(f"'{word}'" for word in preserved_words) if preserved_words else "geen"
    
    selection_system_prompt = build_selection_prompt(language_level, preserved_words_text)

    # Prepare the text of each successful version for the selection prompt
    variants_text = ""
    for i, version_data in enumerate(successful_versions):
        variant_text = version_data.get('text', '')
        variants_text += f"Variant {i+1}:\n{variant_text}\n---\n"

    selection_user_content = f"""
        Originele Paragraaf:
        ---
        {original_chunk}
        ---

        Vereenvoudigde Varianten:
        ---
        {variants_text}
        ---
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

@router.get("/config")
async def get_versimpelaar_config():
    """Get B1 configuration values from environment variables"""
    return {
        "max_input_words": int(os.getenv('versimpelaar_MAX_INPUT_WORDS', 24750)),
        "max_chunk_tokens": int(os.getenv('versimpelaar_MAX_CHUNK_TOKENS', 1200)),
    }

@router.post("/translate")
async def simplify_text_endpoint(request: Request, data: SimplifyTextRequest, user = Depends(get_current_user)):
    """Endpoint to simplify text to B1/B2 level. Generates 3 versions per chunk, then selects the best."""

    print(f"Using model: {data.model}")

    # Load configuration values from environment or defaults
    config = await get_versimpelaar_config()
    print(f"Configuration: {config}")
    
    # Validate input word count
    word_count = len(data.text.split()) if data.text else 0
    if word_count > config['max_input_words']:
        return StreamingResponse(
            iter([json.dumps({"error": f"Input text ({word_count} words) exceeds the limit of {config['max_input_words']} words."}) + "\n"]),
            media_type="application/x-ndjson"
        )

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

    chunks = split_into_chunks(data.text, config['max_chunk_tokens'])
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
                # Continue processing other tasks
                pass

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
                # Yield error result for this chunk
                error_result = {"index": -1, "error": f"Processing failed after selection: {e}"}
                yield json.dumps(error_result) + "\n"


    return StreamingResponse(stream_results(), media_type="application/x-ndjson")