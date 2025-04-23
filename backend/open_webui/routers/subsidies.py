import json # Import json module
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Any, Optional, List # Import List
from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.auth import get_current_user
# --- Placeholder voor Database interactie ---
# Importeer je database sessie en modellen (bijv. SQLAlchemy)
# from open_webui.database import get_db
# from open_webui.models.subsidy import SubsidyData # Voorbeeld DB model

router = APIRouter()

# Model voor de input data van de frontend
class SubsidyQueryInput(BaseModel):
    user_input: str
    model: Optional[str] = None

# --- Aangepast Model voor gestructureerde output ---
class SubsidyCriterion(BaseModel):
    id: int # Of UUID
    text: str
    # Voeg eventueel andere velden toe (bijv. bron, type)

class SubsidyQueryOutput(BaseModel):
    # id: int # ID van het opgeslagen record in de DB
    criteria: List[SubsidyCriterion]
    summary: Optional[str] = None # Optioneel een samenvatting
    # Voeg eventueel andere velden toe

# --- Aangepaste System Prompt voor JSON Output ---
# Instrueer de LLM om een JSON object terug te geven met specifieke sleutels.
SYSTEM_PROMPT = """Je bent een expert op het gebied van Nederlandse subsidies. Analyseer de volgende subsidieregeling die door de gebruiker wordt verstrekt. Identificeer alle relevante criteria waaraan een aanvrager moet voldoen. Geef je antwoord ALLEEN als een geldig JSON-object terug. Het JSON-object moet de volgende structuur hebben:
{
  "criteria": [
    { "id": 1, "text": "Criterium 1 beschrijving..." },
    { "id": 2, "text": "Criterium 2 beschrijving..." },
    // ... meer criteria
  ],
  "summary": "Een korte samenvatting van de belangrijkste criteria of de regeling (optioneel)."
}
Zorg ervoor dat de 'text' van elk criterium duidelijk en volledig is. Nummer de criteria opeenvolgend in het 'id' veld. Als er geen criteria gevonden worden, geef dan een lege lijst terug: { "criteria": [], "summary": "Geen specifieke criteria gevonden." }. Geef GEEN andere tekst terug buiten het JSON-object."""

@router.post("/query", response_model=SubsidyQueryOutput)
async def handle_subsidy_query(
    request: Request,
    query_input: SubsidyQueryInput,
    user = Depends(get_current_user),
    # db: Session = Depends(get_db) # Placeholder voor DB sessie
):
    """
    Neemt een subsidieregeling, extraheert criteria via LLM als JSON,
    slaat het resultaat op (placeholder) en retourneert de gestructureerde data.
    """
    if not query_input.user_input:
        raise HTTPException(status_code=400, detail="Input mag niet leeg zijn.")

    # --- Placeholder: Check of deze input al verwerkt is in DB ---
    # existing_data = db.query(SubsidyData).filter(SubsidyData.input_hash == hash(query_input.user_input)).first()
    # if existing_data:
    #     # Converteer opgeslagen data naar SubsidyQueryOutput en return
    #     try:
    #         parsed_criteria = json.loads(existing_data.criteria_json)
    #         return SubsidyQueryOutput(criteria=parsed_criteria, summary=existing_data.summary)
    #     except json.JSONDecodeError:
    #         # Fallback naar opnieuw genereren als opgeslagen JSON corrupt is
    #         pass

    # --- Model Selectie ---
    DEFAULT_MODEL_FALLBACK = "openai/gpt-4o" # Pas aan indien nodig
    model_to_use = query_input.model or DEFAULT_MODEL_FALLBACK
    if not model_to_use:
         raise HTTPException(status_code=400, detail="Model niet gespecificeerd.")

    DEFAULT_TEMPERATURE = 0.5 # Lagere temperatuur voor consistentere JSON

    form_data = {
        "model": model_to_use,
        "stream": False,
        "temperature": DEFAULT_TEMPERATURE,
        "response_format": { "type": "json_object" }, # Vraag expliciet om JSON (indien ondersteund door LLM/API)
        "messages": [
            { "role": "system", "content": SYSTEM_PROMPT },
            { "role": "user", "content": query_input.user_input }
        ]
    }

    try:
        completion_result = await generate_chat_completion(
            request=request, form_data=form_data, user=user
        )

        raw_response_content = ""
        if completion_result and "choices" in completion_result and len(completion_result["choices"]) > 0:
            message = completion_result["choices"][0].get("message", {})
            raw_response_content = message.get("content", "").strip()

        if not raw_response_content:
            raise HTTPException(status_code=500, detail="Lege response van LLM.")

        # --- Parse de JSON response van de LLM ---
        try:
            # Soms zit de JSON in een code block, probeer dat te strippen
            if raw_response_content.startswith("```json"):
                raw_response_content = raw_response_content[7:]
            if raw_response_content.endswith("```"):
                raw_response_content = raw_response_content[:-3]
            raw_response_content = raw_response_content.strip()

            parsed_data = json.loads(raw_response_content)

            # Valideer de structuur (basis check)
            if "criteria" not in parsed_data or not isinstance(parsed_data["criteria"], list):
                 raise ValueError("Ongeldige JSON structuur: 'criteria' lijst ontbreekt of is geen lijst.")

            # Creëer het output object
            output_data = SubsidyQueryOutput(
                criteria=[SubsidyCriterion(**item) for item in parsed_data.get("criteria", [])],
                summary=parsed_data.get("summary")
            )

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Fout bij parsen LLM JSON response: {e}")
            print(f"Ontvangen raw response:\n{raw_response_content}")
            raise HTTPException(status_code=500, detail=f"Kon de LLM response niet correct verwerken: {e}")

        # --- Placeholder: Sla gestructureerde data op in DB ---
        # try:
        #     new_subsidy_data = SubsidyData(
        #         input_hash=hash(query_input.user_input), # Simpele hash van input
        #         criteria_json=json.dumps([c.dict() for c in output_data.criteria]), # Sla criteria op als JSON string
        #         summary=output_data.summary,
        #         created_by=user.id # Koppel aan gebruiker
        #     )
        #     db.add(new_subsidy_data)
        #     db.commit()
        #     db.refresh(new_subsidy_data)
        #     # output_data.id = new_subsidy_data.id # Voeg DB ID toe aan response indien nodig
        # except Exception as db_error:
        #     db.rollback()
        #     print(f"Database error: {db_error}")
        #     # Overweeg of je de gebruiker wilt informeren of alleen loggen

        return output_data

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error calling generate_chat_completion or processing: {e}")
        # import traceback
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Interne serverfout: {str(e)}")

# ... (rest van het bestand) ...