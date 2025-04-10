from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import List
import tiktoken

from open_webui.utils.auth import get_verified_user
from open_webui.utils.chat import generate_chat_completion as chat_completion

router = APIRouter()

# Helper function to split text into paragraphs based on token count
def split_into_paragraphs(text: str, max_tokens: int = 500) -> List[tuple]:
    enc = tiktoken.get_encoding("cl100k_base")
    paragraphs = text.split('\n\n')
    result = []
    current_position = 0
    
    for para in paragraphs:
        tokens = len(enc.encode(para))
        if tokens > max_tokens:
            # Further split long paragraphs by sentences
            sentences = para.split('. ')
            current_para = []
            current_tokens = 0
            
            for sentence in sentences:
                sentence_tokens = len(enc.encode(sentence))
                if current_tokens + sentence_tokens > max_tokens:
                    if current_para:
                        combined = '. '.join(current_para) + '.'
                        result.append((combined, current_position))
                        current_position += len(combined) + 2  # +2 for '\n\n'
                        current_para = [sentence]
                        current_tokens = sentence_tokens
                else:
                    current_para.append(sentence)
                    current_tokens += sentence_tokens
            
            if current_para:
                combined = '. '.join(current_para) + '.'
                result.append((combined, current_position))
                current_position += len(combined) + 2
        else:
            result.append((para, current_position))
            current_position += len(para) + 2
    
    return result

async def generate_paragraph_version(request: Request, model_id: str, system_prompt: str, paragraph: str, user: dict) -> str:
    chat_request = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Vertaal deze paragraaf naar B1-taalniveau:\n\n{paragraph}"}
        ],
        "temperature": 0.7,
        "stream": False  # We don't stream individual versions
    }
    
    response = await chat_completion(request, form_data=chat_request, user=user)
    return response["choices"][0]["message"]["content"]

async def evaluate_versions(request: Request, model_id: str, versions: List[str], user: dict) -> int:
    evaluation_prompt = """Evalueer welke van de volgende tekstversies het beste voldoet aan B1-taalniveau criteria. 
    Geef alleen het nummer (0, 1, of 2) van de beste versie terug."""
    
    chat_request = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": evaluation_prompt},
            {"role": "user", "content": f"Versie 0:\n{versions[0]}\n\nVersie 1:\n{versions[1]}\n\nVersie 2:\n{versions[2]}"}
        ],
        "temperature": 0.3,
        "stream": False
    }
    
    response = await chat_completion(request, form_data=chat_request, user=user)
    result = response["choices"][0]["message"]["content"].strip()
    return int(result)

@router.post("")
async def simplify_text(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user)
):
    """
    Eenvoudige endpoint voor het vertalen van tekst naar B1-taalniveau.
    Verwacht een JSON body met:
    - text: De tekst die vereenvoudigd moet worden
    - model: Het model ID om te gebruiken
    - preserved_words: (optioneel) Lijst van woorden die niet vereenvoudigd moeten worden
    """
    # Haal de benodigde gegevens uit de request
    input_text = form_data.get("text", "")
    model_id = form_data.get("model", None)
    preserved_words = form_data.get("preserved_words", [])
    language_level = form_data.get("language_level", "B1")
    
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
-Maak abstracte begrippen concreet met duidelijke voorbeelden."""
    else:  # B2 taalniveau
        system_prompt = """Je taak is om onderstaande tekst zorgvuldig te analyseren en vervolgens te herschrijven naar helder, begrijpelijk Nederlands op taalniveau B2. Hierbij is het essentieel dat je de informatie zo letterlijk en nauwkeurig mogelijk weergeeft en de structuur en betekenis van de originele tekst behoudt, zonder belangrijke informatie weg te laten.

Houd je hierbij aan onderstaande richtlijnen voor B2-niveau:
-Gebruik duidelijke zinnen van gemiddelde lengte.
-Complexe zinnen mogen, maar zorg dat ze logisch opgebouwd zijn.
-Vaktermen mogen gebruikt worden als ze uitgelegd worden.
-Gebruik een mix van actieve en passieve zinnen waar passend.
-Abstracte begrippen zijn toegestaan maar moeten duidelijk zijn uit de context."""

    # Voeg instructies toe over woorden die niet vereenvoudigd moeten worden
    if preserved_words:
        system_prompt += f" De volgende woorden/termen mag je NIET vereenvoudigen of veranderen, gebruik ze exact zoals ze zijn: {', '.join(preserved_words)}."
    
    # Split text into paragraphs with positions
    paragraphs = split_into_paragraphs(input_text)
    
    async def process_paragraph(para_tuple):
        paragraph, position = para_tuple
        # Generate 3 versions concurrently
        versions = await asyncio.gather(*[
            generate_paragraph_version(request, model_id, system_prompt, paragraph, user)
            for _ in range(3)
        ])
        
        # Evaluate versions
        best_version_idx = await evaluate_versions(request, model_id, versions, user)
        best_version = versions[best_version_idx]
        
        return {"text": best_version, "position": position}

    async def stream_results():
        # Process all paragraphs concurrently
        tasks = [process_paragraph(para) for para in paragraphs]
        pending = tasks
        
        while pending:
            # Wait for any task to complete
            done, pending = await asyncio.wait(
                pending, 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done:
                result = await task
                # Stream result as SSE
                yield f"data: {json.dumps(result)}\n\n"
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_results(),
        media_type="text/event-stream"
    )
