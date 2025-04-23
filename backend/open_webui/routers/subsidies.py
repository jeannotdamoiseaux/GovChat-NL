from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Any, Optional # Import Optional
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.auth import get_current_user
# Importeer eventueel je standaard model uit instellingen
# from open_webui.config import DEFAULT_MODEL # Voorbeeld

router = APIRouter()

# Model voor de input data van de frontend
class SubsidyQueryInput(BaseModel):
    user_input: str
    model: Optional[str] = None # Voeg optioneel model veld toe

# Model voor de output data naar de frontend
class SubsidyQueryOutput(BaseModel):
    response: str

# De vaste prompt die je wilt gebruiken (als system prompt)
SYSTEM_PROMPT = """Je bent een expert op het gebied van Nederlandse subsidies. Beantwoord de volgende vraag zo specifiek en behulpzaam mogelijk."""

@router.post("/query", response_model=SubsidyQueryOutput)
async def handle_subsidy_query(
    request: Request,
    query_input: SubsidyQueryInput,
    user = Depends(get_current_user)
):
    """
    Neemt een gebruikersvraag, formatteert deze met een vaste prompt,
    roept generate_chat_completion aan met het opgegeven model en retourneert het antwoord.
    """
    if not query_input.user_input:
        raise HTTPException(status_code=400, detail="Input mag niet leeg zijn.")

    # --- Model Selectie ---
    # Gebruik het model uit de input, of een standaard fallback
    # Pas DEFAULT_MODEL aan naar je daadwerkelijke standaard/fallback model ID
    DEFAULT_MODEL_FALLBACK = "openai/gpt-4o" # <<< VERANDER DIT INDIEN NODIG
    model_to_use = query_input.model or DEFAULT_MODEL_FALLBACK
    if not model_to_use: # Extra check voor het geval de fallback ook leeg is
         raise HTTPException(status_code=400, detail="Model niet gespecificeerd en geen standaard model beschikbaar.")


    DEFAULT_TEMPERATURE = 0.7 # Stel een standaard temperatuur in

    # Bereid form_data voor generate_chat_completion voor
    form_data = {
        "model": model_to_use, # Gebruik het geselecteerde model
        "stream": False,
        "temperature": DEFAULT_TEMPERATURE,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": query_input.user_input
            }
        ]
    }

    try:
        completion_result = await generate_chat_completion(
            request=request,
            form_data=form_data,
            user=user
        )

        if completion_result and "choices" in completion_result and len(completion_result["choices"]) > 0:
            message = completion_result["choices"][0].get("message", {})
            response_content = message.get("content", "")
            if not response_content:
                 response_content = "Kon geen geldig antwoord genereren uit de completion."
        else:
            print(f"Onverwachte structuur van completion_result: {completion_result}")
            response_content = "Ongeldige of lege response van chat completion."

        return SubsidyQueryOutput(response=response_content.strip())

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error calling generate_chat_completion: {e}")
        raise HTTPException(status_code=500, detail=f"Interne serverfout bij het verwerken van de vraag: {str(e)}")

# ... (rest van het bestand) ...