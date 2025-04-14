from fastapi import APIRouter, Request, Depends
from typing import Optional, List, Any
from pydantic import BaseModel
import asyncio
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.auth import get_current_user
import tiktoken
import re

router = APIRouter()

def split_into_chunks(text: str, max_tokens: int = 1500) -> List[str]:
    """Split text into chunks of approximately max_tokens"""
    encoding = tiktoken.get_encoding("cl100k_base")
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_tokens = len(encoding.encode(word))
        if current_length + word_tokens > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = word_tokens
        else:
            current_chunk.append(word)
            current_length += word_tokens
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

async def generate_version(request: Request, chunk: str, model: str, preserved_words: List[str], language_level: str, user: Any) -> str:
    """Generate a single version of simplified text"""
    form_data = {
        "model": model,
        "stream": False,  # Set to False for parallel processing
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

                           Plaats de verbeterde paragraaf tussen "<<<" en ">>>" tekens. Als de tekst te kort is om te verbeteren neem je de tekst een-op-een over en plaats deze tussen de genoemende tekens, bijv. "<<< Artikel 3.2 >>>".""" 
            },
            {
                "role": "user",
                "content": chunk
            }
        ]
    }
    
    response = await generate_chat_completion(request=request, form_data=form_data, user=user)
    return response['choices'][0]['message']['content']

class SimplifyTextRequest(BaseModel):
    text: str
    model: str
    preserved_words: list[str] = []
    language_level: str = "B1"

@router.post("/translate")
async def simplify_text(
    request: Request,
    data: SimplifyTextRequest,
    user = Depends(get_current_user)
):
    """Endpoint to simplify text to B1/B2 language level with parallel processing"""
    
    # Split text into chunks
    chunks = split_into_chunks(data.text)
    all_versions = []
    batch_size = 20  # Process 20 chunks at a time

    # Process all chunks in batches
    for batch_start in range(0, len(chunks), batch_size):
        batch_end = min(batch_start + batch_size, len(chunks))
        batch_chunks = chunks[batch_start:batch_end]

        # Process each chunk in parallel
        version_tasks = []
        for i, chunk in enumerate(batch_chunks):
            chunk_tasks = [
                generate_version(request, chunk, data.model, data.preserved_words, data.language_level, user)
                for _ in range(3)
            ]
            version_tasks.extend(chunk_tasks)

        # Process batch results
        batch_results = await asyncio.gather(*version_tasks)
        
        # Store results in memory
        for i in range(0, len(batch_results), 3):
            chunk_versions = batch_results[i:i+3]
            all_versions.append({
                "chunk": batch_start + (i // 3),
                "versions": chunk_versions
            })

    # Process all chunks at once
    form_data = {
        "model": data.model,
        "stream": True,
        "temperature": 0.2,  # Lower temperature for faster responses
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "messages": [
            {
                "role": "system",
                "content": f"""Je taak is om de volgende tekst te analyseren en te herschrijven naar een versie die voldoet aan het {data.language_level}-taalniveau.
                           Hierbij is het belangrijk om de informatie zo letterlijk mogelijk over te brengen en de structuur zoveel mogelijk te behouden, zonder onnodige weglatingen.
                           Het {data.language_level}-niveau kenmerkt zich door duidelijk en eenvoudig taalgebruik, geschikt voor een breed publiek met basisvaardigheden in de taal.

                           Hier zijn enkele richtlijnen om je te helpen bij deze taak:
                           - Gebruik korte zinnen en vermijd lange, complexe zinsconstructies.
                           - Vervang moeilijke woorden door meer gangbare alternatieven.
                           - Leg technische termen en (ambtelijk) jargon uit in eenvoudige bewoordingen.
                           - Gebruik actieve zinsconstructies waar mogelijk.
                           - Vermijd passieve zinnen en ingewikkelde grammaticale constructies.
                           - Gebruik concrete voorbeelden om abstracte concepten te verduidelijken.
                           
                           Hier zijn enkele voorbeelden van woorden op C1-niveau en hun eenvoudigere {data.language_level}-equivalenten:
                           - Betreffende -> Over
                           - Creëren -> Ontwerpen, vormen, vormgeven, maken
                           - Prioriteit -> Voorrang, voorkeur
                           - Relevant -> Belangrijk
                           - Verstrekken -> Geven
                           
                           Zorg ervoor dat de inhoud en nuances van de oorspronkelijke tekst behouden blijven en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.

                           Je ontvangt de originele paragraaf, samen met enkele varianten van deze tekst in eenvoudigere taal ({data.language_level}). Het is jouw taak om tot een definitieve {data.language_level}-versie te komen.
                           
                           Verwijder alle "<<<" en ">>>" tekens uit de tekst en combineer de beste versies tot één samenhangend geheel."""
            },
            {
                "role": "user",
                "content": "\n\n".join([
                    f"Paragraaf {chunk['chunk'] + 1}:\n" + 
                    "\n".join([f"Versie {i+1}: {version}" for i, version in enumerate(chunk['versions'])])
                    for chunk in all_versions
                ])
            }
        ]
    }

    return await generate_chat_completion(
        request=request,
        form_data=form_data,
        user=user
    )