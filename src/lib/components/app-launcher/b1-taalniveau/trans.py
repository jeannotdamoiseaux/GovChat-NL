from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
import asyncio

from open_webui.utils.auth import get_verified_user
from open_webui.utils.chat import generate_chat_completion as chat_completion

router = APIRouter()

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
    
    # Maak het chat request
    chat_request = {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Vertaal de volgende tekst naar {language_level}-taalniveau. Behoud de structuur en opmaak zoals alinea's en opsommingen:\n\n{input_text}"
            }
        ],
        "temperature": 0.7,
        "stream": True
    }
    
    try:
        # Gebruik de bestaande chat_completion functie
        response = await chat_completion(request, form_data=chat_request, user=user)
        
        # Als het een streaming response is, geef deze door
        if hasattr(response, 'body_iterator'):
            # Simply pass through the streaming response with the correct media type
            return StreamingResponse(
                response.body_iterator,
                media_type="text/event-stream",
                background=response.background if hasattr(response, 'background') else None
            )
        
        # Anders, geef de normale response terug
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
