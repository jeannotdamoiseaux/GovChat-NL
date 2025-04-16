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


async def generate_version(request: Request, chunk: str, model: str, preserved_words: List[str], language_level: str, user: Any, index: int) -> dict:
    """Generate a single version of simplified text and return with index"""
    if not chunk or chunk.isspace():
        # Return empty strings as they might be intentional paragraph breaks
        return {"index": index, "text": chunk}

    form_data = {
        "model": model,
        "stream": False, # Ensure streaming is off for this internal call
        "messages": [
            {
                "role": "system",
                "content": f"""Je taak is om de volgende tekst te analyseren en te herschrijven naar een versie die voldoet aan het {language_level}-taalniveau.
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

                           Behoud de volgende woorden ongewijzigd: {', '.join(preserved_words) if preserved_words else 'geen'}.
                           Zorg ervoor dat de hoofdboodschap van de tekst behouden blijft en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.

                           Behoud alle tekst tussen ** sterretjes exact zoals deze is en zet deze ook tussen ** sterretjes in de output.
                           Bijvoorbeeld: "Dit is een **belangrijk** woord" moet in de output ook "Dit is een **belangrijk** woord" worden.

                           Geef ALLEEN de herschreven tekst terug, zonder extra uitleg, inleiding of afsluiting. Als de tekst niet vereenvoudigd hoeft te worden (bijv. een titel of een al eenvoudige zin), geef dan de originele tekst terug."""
            },
            {
                "role": "user",
                "content": chunk
            }
        ]
    }

    try:
        # Assuming generate_chat_completion handles potential API errors gracefully
        response = await generate_chat_completion(request=request, form_data=form_data, user=user)
        simplified_text = response['choices'][0]['message']['content']

        # Clean potential markdown code blocks added by the model
        simplified_text = re.sub(r'^```[a-zA-Z]*\n?', '', simplified_text)
        simplified_text = re.sub(r'\n?```$', '', simplified_text)

        return {"index": index, "text": simplified_text.strip()}
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error processing chunk {index} with model {model}: {e}")
        # Return the original chunk in case of an error to avoid data loss
        return {"index": index, "text": chunk}

class SimplifyTextRequest(BaseModel):
    text: str
    model: str
    preserved_words: list[str] = []
    language_level: str = "B1"

@router.post("/translate")
async def simplify_text_endpoint(request: Request, data: SimplifyTextRequest, user = Depends(get_current_user)): # Renamed function slightly
    """Endpoint to simplify text to B1/B2 language level with concurrent processing and streaming"""

    # Consider adding basic input validation if needed (e.g., max text length on backend too)
    # Although frontend has a limit, backend validation is good practice.

    chunks = split_into_chunks(data.text)
    num_chunks = len(chunks)

    # If there are no chunks (e.g., empty input after split), handle gracefully
    if num_chunks == 0:
        async def empty_stream():
             yield json.dumps({"total_chunks": 0}) + "\n"
             # Need to yield at least one item for StreamingResponse
             if False: yield None # Trick to make it an async generator
        return StreamingResponse(empty_stream(), media_type="application/x-ndjson")


    async def stream_results():
        # Send total chunk count first
        yield json.dumps({"total_chunks": num_chunks}) + "\n"

        # Create concurrent tasks for processing each chunk
        tasks = [
            generate_version(request, chunk, data.model, data.preserved_words, data.language_level, user, i)
            for i, chunk in enumerate(chunks)
        ]

        # Yield results as they become available
        for future in asyncio.as_completed(tasks):
            try:
                result = await future
                yield json.dumps(result) + "\n"
            except Exception as e:
                # This catch might be redundant if generate_version handles its errors,
                # but can catch errors during await future itself.
                print(f"Error awaiting chunk result: {e}")
                # Decide how to handle this - potentially yield an error object or skip
                # yield json.dumps({"index": -1, "error": str(e)}) + "\n" # Example error yield

    return StreamingResponse(stream_results(), media_type="application/x-ndjson")