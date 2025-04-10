from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import List
import tiktoken

from open_webui.utils.auth import get_verified_user
from open_webui.utils.chat import generate_chat_completion as chat_completion

router = APIRouter()

# Add these constants at the top of the file
MAX_WORDS_PER_BATCH = 15000
MAX_TOKENS_PER_PARAGRAPH = 1500
MAX_CONCURRENT_BATCHES = 20

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

def split_text_into_batches(text: str) -> List[str]:
    """Split text into batches of approximately MAX_WORDS_PER_BATCH words."""
    words = text.split()
    total_words = len(words)
    
    if total_words > MAX_WORDS_PER_BATCH * MAX_CONCURRENT_BATCHES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tekst is te lang. Maximum is {MAX_WORDS_PER_BATCH * MAX_CONCURRENT_BATCHES} woorden, aangeleverde tekst bevat {total_words} woorden."
        )
    
    batches = []
    current_batch = []
    current_word_count = 0
    
    for word in words:
        if current_word_count + 1 > MAX_WORDS_PER_BATCH:
            # Find the last period to make a clean break
            batch_text = ' '.join(current_batch)
            last_period = batch_text.rfind('.')
            if last_period != -1:
                # Split at the last period
                batches.append(batch_text[:last_period + 1])
                remainder = batch_text[last_period + 1:] + ' ' + word
                current_batch = remainder.split()
                current_word_count = len(current_batch)
            else:
                # If no period found, just split at the word limit
                batches.append(batch_text)
                current_batch = [word]
                current_word_count = 1
        else:
            current_batch.append(word)
            current_word_count += 1
    
    # Add the last batch if there's anything left
    if current_batch:
        batches.append(' '.join(current_batch))
    
    return batches

async def generate_paragraph_version(request: Request, model_id: str, system_prompt: str, paragraph: str, user: dict) -> str:
    chat_request = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Vereenvoudig deze paragraaf naar B1-taalniveau en plaats het resultaat tussen <<< en >>> tekens:\n\n{paragraph}"}
        ],
        "temperature": 0.7,
        "stream": False
    }
    
    response = await chat_completion(request, form_data=chat_request, user=user)
    content = response["choices"][0]["message"]["content"]
    
    # Extract text between markers
    start = content.find('<<<')
    end = content.find('>>>')
    if start >= 0 and end >= 0:
        return content[start+3:end].strip()
    return content.strip()

async def evaluate_versions(request: Request, model_id: str, versions: List[str], user: dict) -> str:
    evaluation_prompt = """Je taak is om de volgende tekst te analyseren en de beste B1-niveau versie te selecteren.
    
    Beoordeel de versies op basis van deze B1-criteria:
    - Gebruik van korte zinnen en vermijding van complexe constructies
    - Gebruik van gangbare woorden in plaats van moeilijke alternatieven
    - Uitleg van technische termen in eenvoudige bewoordingen
    - Gebruik van actieve zinsconstructies
    - Behoud van de originele betekenis en nuances
    
    Selecteer de beste versie die voldoet aan deze criteria en plaats deze tussen <<< en >>> tekens."""

    chat_request = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": evaluation_prompt},
            {"role": "user", "content": f"Versie 1:\n{versions[0]}\n\nVersie 2:\n{versions[1]}\n\nVersie 3:\n{versions[2]}"}
        ],
        "temperature": 0.3,
        "stream": False
    }
    
    response = await chat_completion(request, form_data=chat_request, user=user)
    content = response["choices"][0]["message"]["content"]
    
    # Extract text between <<< and >>> markers
    start = content.find('<<<')
    end = content.find('>>>')
    if start >= 0 and end >= 0:
        return content[start+3:end].strip()
    return content.strip()

async def process_paragraph_result(para_tuple, request: Request, model_id: str, system_prompt: str, user: dict):
    paragraph, position = para_tuple
    # Generate 3 versions concurrently
    versions = await asyncio.gather(*[
        generate_paragraph_version(request, model_id, system_prompt, paragraph, user)
        for _ in range(3)
    ])
    
    # Evaluate versions and get best version
    best_version = await evaluate_versions(request, model_id, versions, user)
    return best_version, position

async def process_batch(batch_text: str, batch_num: int, total_batches: int, request: Request, model_id: str, system_prompt: str, user: dict):
    # Split batch into paragraphs
    paragraphs = split_into_paragraphs(batch_text, MAX_TOKENS_PER_PARAGRAPH)
    
    # Process the paragraphs in this batch
    tasks = [
        asyncio.create_task(
            process_paragraph_result(para, request, model_id, system_prompt, user)
        ) 
        for para in paragraphs
    ]
    pending = tasks
    
    try:
        # Send batch progress update
        progress_data = json.dumps({
            'type': 'progress',
            'batch': batch_num + 1,
            'total_batches': total_batches
        })
        yield f"data: {progress_data}\n\n"
        
        while pending:
            done, pending = await asyncio.wait(
                pending, 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in done:
                try:
                    text, position = await task
                    words = text.split()
                    for word in words:
                        data = json.dumps({
                            'text': word + ' ',
                            'position': position,
                            'isPartial': True
                        })
                        yield f"data: {data}\n\n"
                        await asyncio.sleep(0.05)
                    
                    completion_data = json.dumps({
                        'text': '\n\n',
                        'position': position,
                        'isPartial': False
                    })
                    yield f"data: {completion_data}\n\n"
                except Exception as e:
                    print(f"Error processing task: {e}")
                    continue
    finally:
        for task in pending:
            task.cancel()

async def stream_results(paragraphs: List[tuple], request: Request, model_id: str, system_prompt: str, user: dict):
    # Create tasks for processing each paragraph
    tasks = [
        asyncio.create_task(
            process_paragraph_result(para, request, model_id, system_prompt, user)
        ) 
        for para in paragraphs
    ]
    pending = tasks
    
    try:
        while pending:
            # Wait for any task to complete
            done, pending = await asyncio.wait(
                pending, 
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Process completed tasks
            for task in done:
                try:
                    text, position = await task
                    # Stream the text word by word
                    words = text.split()
                    for word in words:
                        data = json.dumps({
                            'text': word + ' ',
                            'position': position,
                            'isPartial': True
                        })
                        yield f"data: {data}\n\n"
                        await asyncio.sleep(0.05)  # Add small delay between words
                    
                    # Send paragraph completion marker
                    completion_data = json.dumps({
                        'text': '\n\n',
                        'position': position,
                        'isPartial': False
                    })
                    yield f"data: {completion_data}\n\n"
                except Exception as e:
                    print(f"Error processing task: {e}")
                    continue
        
        # Signal overall completion
        yield "data: [DONE]\n\n"
        
    finally:
        # Clean up any remaining tasks
        for task in pending:
            task.cancel()

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
    
    # Split text into batches
    batches = split_text_into_batches(input_text)
    total_batches = len(batches)
    
    async def process_all_batches():
        for batch_num, batch_text in enumerate(batches):
            async for chunk in process_batch(
                batch_text, 
                batch_num, 
                total_batches,
                request, 
                model_id, 
                system_prompt, 
                user
            ):
                yield chunk
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        process_all_batches(),
        media_type="text/event-stream"
    )
