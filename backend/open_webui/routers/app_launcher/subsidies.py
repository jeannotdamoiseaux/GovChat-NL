import json # Import json module
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Any, Optional, List, Dict, Union  # Union toegevoegd
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

# --- Modellen voor beoordeling subsidieaanvraag ---
class SubsidyApplicationInput(BaseModel):
    application_text: str
    criteria: List[SubsidyCriterion]
    model: Optional[str] = None

class SubsidyAssessmentItem(BaseModel):
    Criterium: str
    Score: Union[str, int]  # Aanpassen om zowel strings als integers te accepteren
    Toelichting: str

class SubsidyAssessmentOutput(BaseModel):
    assessment: Dict[str, SubsidyAssessmentItem]  # {"1": {...}, "2": {...}, ...}

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

# --- System Prompt voor beoordeling subsidieaanvraag ---
ASSESSMENT_SYSTEM_PROMPT = """Je bent verantwoordelijk voor het beoordelen van een subsidieaanvraag aan de hand van een subsidieregeling. Deze regeling ontvang je als een geneste JSON-indeling, waarbij elk artikel en daaronder de bijbehorende criteria worden weergegeven. Het is jouw taak om voor elk criterium in de ontvangen JSON een score tussen 0 en 10, en een beknopte toelichting die de redenering achter de gegeven score beschrijft, toe te voegen.

Een score van 0 geeft aan dat het criterium niet voldoet, terwijl een score van 10 aangeeft dat het criterium volledig voldoet. In het geval dat een criterium een afwijzingsgrond is, betekent een score van 10 dat de afwijzingsgrond niet van toepassing is, en een score van 0 betekent dat deze wel van toepassing is.

Na het beoordelen van alle artikelen en criteria, controleer of er geen gemiste artikelen of criteria zijn. Als er gemiste onderdelen zijn, dien je deze alsnog te beoordelen en te documenteren.

Het is belangrijk om geen aannames te maken en alleen uit te gaan van de informatie in de aanvraag. Als je niet zeker weet hoe je een criterium moet beoordelen, kun je "Onzeker" gebruiken. De vereiste outputstructuur is opnieuw een geneste JSON-indeling, die zoals hieronder aangegeven moet zijn, met behulp van accolades voor de notatie.

{
    "1": {
        "Criterium": "Volledige tekst van het eerste criterium",
        "Score": "Uw score (0-10 of 'Onzeker')",
        "Toelichting": "Uw beknopte toelichting voor dit criterium."
    },
    "2": {
        "Criterium": "Volledige tekst van het tweede criterium",
        "Score": "Uw score (0-10 of 'Onzeker')",
        "Toelichting": "Uw beknopte toelichting voor dit criterium."
    }
}

Zorg ervoor dat je altijd nested accolades ({}) gebruikt om de structuur van je output weer te geven. Wees volledig en neem altijd alle criteria mee in je evaluatie. Geef ALLEEN het JSON-object terug zonder extra tekst."""

# --- System Prompt voor samenvatting subsidieaanvraag ---
SUMMARY_SYSTEM_PROMPT = """Je taak is om een korte samenvatting te maken van een subsidieaanvraag, waarbij je uitsluitend gebruikmaakt van het aanvraagformulier als bron van gegevens. De gewenste outputstructuur is een geneste JSON-indeling, waarbij je de volgende structuur volgt:
{
"Aanvrager": "",
"Datum_aanvraag": "",
"Datum_evenement": "",
"Bedrag": "",
"Samenvatting": ""
}

Probeer alle velden te vullen op basis van de informatie in de aanvraag. Als informatie ontbreekt, gebruik dan "Onbekend" als waarde. De "Aanvrager" is de persoon of organisatie die de subsidie aanvraagt. "Datum_aanvraag" is wanneer de aanvraag is ingediend. "Datum_evenement" is wanneer het evenement of project waarvoor subsidie wordt aangevraagd plaatsvindt. "Bedrag" is het aangevraagde subsidiebedrag. "Samenvatting" is een beknopte beschrijving van het doel van de aanvraag.

Zorg ervoor dat je altijd nested accolades ({}) gebruikt om de structuur van je output weer te geven en ALLEEN het JSON-object teruggeeft zonder extra tekst."""

# --- System Prompt voor eindrapport ---
REPORT_SYSTEM_PROMPT = """Je bent verantwoordelijk voor het maken van een korte samenvatting van een beoordeling van een subsidieaanvraag. Een subsidie kan worden verleend als aan alle criteria is voldaan. In de samenvatting noem je expliciet welke criteria niet voldoen en of deze eventueel nog verbeterd kunnen worden.

De aanvraag ontvang je als een geneste JSON-indeling met de volgende structuur:

{ 
  "Aanvrager": "",
  "Datum_aanvraag": "",
  "Datum_evenement": "", 
  "Bedrag": "",
  "Samenvatting": "" }

De beoordeling ontvang je als een geneste JSON-indeling met de volgende structuur per criterium:

{
  "Criterium": "",
  "Score": "",
  "Toelichting": ""
}

De gewenste outputstructuur is opnieuw een geneste JSON-indeling, waarbij je de volgende structuur volgt:

{
  "Samenvatting": "",
  "Eindoordeel": "",
  "Bedrag": ""
}

De Samenvatting moet een beknopte analyse bevatten van de hele aanvraag en beoordeling, met focus op belangrijke sterke en zwakke punten.
Het Eindoordeel moet duidelijk aangeven of de subsidie kan worden verleend, gedeeltelijk kan worden verleend, of moet worden afgewezen, met toelichting.
Het Bedrag is het aanbevolen toe te kennen bedrag, dat kan afwijken van het aangevraagde bedrag als daar redenen voor zijn.

Zorg ervoor dat je altijd nested accolades ({}) gebruikt om de structuur van je output weer te geven. Geef ALLEEN het JSON-object terug zonder extra tekst."""

# --- Model voor samenvatting output ---
class SubsidySummaryOutput(BaseModel):
    Aanvrager: str
    Datum_aanvraag: str
    Datum_evenement: str
    Bedrag: str
    Samenvatting: str

# --- Model voor gecombineerd rapport input ---
class SubsidyCombinedReportInput(BaseModel):
    assessment_results: Dict[str, SubsidyAssessmentItem]
    summary_result: SubsidySummaryOutput
    model: Optional[str] = None
    
    class Config:
        # Dit maakt het model flexibeler bij JSON serialisatie/deserialisatie
        arbitrary_types_allowed = True

# --- Model voor rapport output ---
class SubsidyReportOutput(BaseModel):
    Samenvatting: str
    Eindoordeel: str
    Bedrag: str

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

@router.post("/assess", response_model=SubsidyAssessmentOutput)
async def handle_subsidy_assessment(
    request: Request,
    assessment_input: SubsidyApplicationInput,
    user = Depends(get_current_user),
):
    """
    Beoordeelt een subsidieaanvraag tegen een set van eerder geëxtraheerde criteria 
    m.b.v. een LLM en geeft een gestructureerde beoordeling terug.
    """
    if not assessment_input.application_text:
        raise HTTPException(status_code=400, detail="Subsidieaanvraag tekst mag niet leeg zijn.")
    if not assessment_input.criteria or len(assessment_input.criteria) == 0:
        raise HTTPException(status_code=400, detail="Er zijn geen criteria opgegeven om te beoordelen.")

    # Model Selectie met betere foutafhandeling
    DEFAULT_MODEL_FALLBACK = "openai/gpt-4o"
    model_to_use = None
    
    # Probeer een model te krijgen, met uitgebreide foutafhandeling
    try:
        model_to_use = assessment_input.model
        # Als model leeg is of None, gebruik fallback
        if not model_to_use:
            print(f"Geen model gespecificeerd, gebruik fallback: {DEFAULT_MODEL_FALLBACK}")
            model_to_use = DEFAULT_MODEL_FALLBACK
            
        # Log het gebruikte model voor debugging
        print(f"Model dat gebruikt wordt voor beoordeling: {model_to_use}")
    except Exception as e:
        print(f"Fout bij het selecteren van het model: {e}")
        model_to_use = DEFAULT_MODEL_FALLBACK
        
    if not model_to_use:
        raise HTTPException(status_code=400, detail="Kon geen geldig model selecteren voor de beoordeling.")

    DEFAULT_TEMPERATURE = 0.2  # Lagere temperatuur voor meer consistente beoordelingen

    # Bereid criteria voor in een genummerde lijst voor de LLM
    criteria_context = []
    for criterion in assessment_input.criteria:
        criteria_context.append(f"Criterium {criterion.id}: {criterion.text}")
    
    criteria_text = "\n".join(criteria_context)

    user_message_content = f"""Beoordeel de volgende subsidieaanvraag:
--- START SUBSIDIEAANVRAAG ---
{assessment_input.application_text}
--- EINDE SUBSIDIEAANVRAAG ---

Aan de hand van de volgende criteria uit de subsidieregeling:
--- START CRITERIA SUBSIDIEREGELING ---
{criteria_text}
--- EINDE CRITERIA SUBSIDIEREGELING ---

Volg de instructies in de system prompt nauwkeurig voor de beoordeling en de outputstructuur.
Zorg ervoor dat elk criterium uit de lijst hierboven wordt beoordeeld.
Het "Criterium" veld in je JSON output MOET de volledige tekst van het beoordeelde criterium bevatten.
De output moet een JSON-object zijn waarbij de sleutels genummerd zijn (als strings, "1", "2", etc.) overeenkomend met de nummering van de criteria hierboven.
"""

    form_data = {
        "model": model_to_use,
        "stream": False,
        "temperature": DEFAULT_TEMPERATURE,
        "response_format": { "type": "json_object" },
        "messages": [
            { "role": "system", "content": ASSESSMENT_SYSTEM_PROMPT },
            { "role": "user", "content": user_message_content }
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
            raise HTTPException(status_code=500, detail="Lege response van LLM bij beoordeling.")

        # Parse de JSON response van de LLM
        try:
            # Verwijder eventuele markdown code block markering
            if raw_response_content.startswith("```json"):
                raw_response_content = raw_response_content[7:]
            if raw_response_content.endswith("```"):
                raw_response_content = raw_response_content[:-3]
            raw_response_content = raw_response_content.strip()

            parsed_data = json.loads(raw_response_content)
            
            if not isinstance(parsed_data, dict):
                raise ValueError("LLM response voor beoordeling is geen geldige JSON dictionary.")
            
            # Converteer alle score waarden naar strings indien nodig
            for key, item in parsed_data.items():
                if "Score" in item and isinstance(item["Score"], int):
                    item["Score"] = str(item["Score"])
            
            # Validatie via Pydantic model
            assessment_output = SubsidyAssessmentOutput(assessment=parsed_data)
            return assessment_output

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Fout bij parsen LLM JSON response voor beoordeling: {e}")
            print(f"Ontvangen raw response LLM (beoordeling):\n{raw_response_content}")
            raise HTTPException(status_code=500, detail=f"Kon de LLM beoordelingsresponse niet correct verwerken: {e}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in handle_subsidy_assessment: {e}")
        # import traceback
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Interne serverfout bij beoordeling: {str(e)}")

@router.post("/summarize", response_model=SubsidySummaryOutput)
async def handle_subsidy_summary(
    request: Request,
    assessment_input: SubsidyApplicationInput,
    user = Depends(get_current_user),
):
    """
    Genereert een beknopte samenvatting van een subsidieaanvraag
    met gestructureerde informatie zoals aanvrager, data en bedrag.
    """
    if not assessment_input.application_text:
        raise HTTPException(status_code=400, detail="Subsidieaanvraag tekst mag niet leeg zijn.")

    # Model Selectie met betere foutafhandeling
    DEFAULT_MODEL_FALLBACK = "openai/gpt-4o"
    model_to_use = assessment_input.model or DEFAULT_MODEL_FALLBACK
    
    if not model_to_use:
        print(f"Geen model gespecificeerd, gebruik fallback: {DEFAULT_MODEL_FALLBACK}")
        model_to_use = DEFAULT_MODEL_FALLBACK
        
    print(f"Model dat gebruikt wordt voor samenvatting: {model_to_use}")

    DEFAULT_TEMPERATURE = 0.3  # Temperatuur voor de samenvatting

    user_message_content = f"""Maak een samenvatting van de volgende subsidieaanvraag:
--- START SUBSIDIEAANVRAAG ---
{assessment_input.application_text}
--- EINDE SUBSIDIEAANVRAAG ---

Identificeer de aanvrager, datums, bedrag en maak een beknopte samenvatting.
Zorg ervoor dat je de JSON output structuur volgt zoals beschreven in de systeemprompt.
"""

    form_data = {
        "model": model_to_use,
        "stream": False,
        "temperature": DEFAULT_TEMPERATURE,
        "response_format": { "type": "json_object" },
        "messages": [
            { "role": "system", "content": SUMMARY_SYSTEM_PROMPT },
            { "role": "user", "content": user_message_content }
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
            raise HTTPException(status_code=500, detail="Lege response van LLM bij samenvatting.")

        # Parse de JSON response van de LLM
        try:
            # Verwijder eventuele markdown code block markering
            if raw_response_content.startswith("```json"):
                raw_response_content = raw_response_content[7:]
            if raw_response_content.endswith("```"):
                raw_response_content = raw_response_content[:-3]
            raw_response_content = raw_response_content.strip()

            parsed_data = json.loads(raw_response_content)
            
            # Converteer de sleutels naar de verwachte Pydantic model veldnamen
            # (merk op dat we underscore gebruiken in het Pydantic model vanwege Python conventies)
            if "Datum_aanvraag" not in parsed_data and "Datum aanvraag" in parsed_data:
                parsed_data["Datum_aanvraag"] = parsed_data.pop("Datum aanvraag")
            if "Datum_evenement" not in parsed_data and "Datum evenement" in parsed_data:
                parsed_data["Datum_evenement"] = parsed_data.pop("Datum evenement")
            
            # Validatie via Pydantic model
            summary_output = SubsidySummaryOutput(**parsed_data)
            return summary_output

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Fout bij parsen LLM JSON response voor samenvatting: {e}")
            print(f"Ontvangen raw response LLM (samenvatting):\n{raw_response_content}")
            raise HTTPException(status_code=500, detail=f"Kon de LLM samenvattingsresponse niet correct verwerken: {e}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in handle_subsidy_summary: {e}")
        raise HTTPException(status_code=500, detail=f"Interne serverfout bij samenvatting: {str(e)}")

@router.post("/generate_report", response_model=SubsidyReportOutput)
async def handle_subsidy_report(
    request: Request,
    report_input: SubsidyCombinedReportInput,
    user = Depends(get_current_user),
):
    """
    Genereert een eindrapport door de samenvatting en beoordelingsresultaten te combineren.
    """
    if not report_input.assessment_results:
        raise HTTPException(status_code=400, detail="Beoordelingsresultaten zijn vereist voor het rapport.")
    if not report_input.summary_result:
        raise HTTPException(status_code=400, detail="Samenvattingsresultaat is vereist voor het rapport.")

    # Model Selectie
    DEFAULT_MODEL_FALLBACK = "openai/gpt-4o"
    model_to_use = report_input.model or DEFAULT_MODEL_FALLBACK
    
    if not model_to_use:
        print(f"Geen model gespecificeerd, gebruik fallback: {DEFAULT_MODEL_FALLBACK}")
        model_to_use = DEFAULT_MODEL_FALLBACK
        
    print(f"Model dat gebruikt wordt voor eindrapport: {model_to_use}")

    DEFAULT_TEMPERATURE = 0.4  # Iets hogere temperatuur voor meer creativiteit in het rapport

    # Bereid de JSON input voor de LLM prompt voor - Met betere foutafhandeling
    summary_formatted = ""
    assessment_formatted = ""
    
    try:
        # Probeer eerst de summary_result als een Python dict te krijgen
        # In Pydantic v2+ gebruik je model_dump() in plaats van dict()
        # We proberen beide methoden om compatibel te zijn met verschillende Pydantic versies
        try:
            if hasattr(report_input.summary_result, "model_dump"):
                summary_dict = report_input.summary_result.model_dump()
            elif hasattr(report_input.summary_result, "dict"):
                summary_dict = report_input.summary_result.dict()
            else:
                # Fallback: converteer het naar een dict met __dict__
                summary_dict = {
                    "Aanvrager": report_input.summary_result.Aanvrager,
                    "Datum_aanvraag": report_input.summary_result.Datum_aanvraag,
                    "Datum_evenement": report_input.summary_result.Datum_evenement,
                    "Bedrag": report_input.summary_result.Bedrag,
                    "Samenvatting": report_input.summary_result.Samenvatting
                }
                
            # Nu pas proberen te serialiseren naar JSON
            summary_formatted = json.dumps(summary_dict, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Fout bij het serialiseren van summary_result: {e}")
            # Handmatige formattering als fallback
            summary_formatted = f"""{{
  "Aanvrager": "{report_input.summary_result.Aanvrager}",
  "Datum_aanvraag": "{report_input.summary_result.Datum_aanvraag}",
  "Datum_evenement": "{report_input.summary_result.Datum_evenement}",
  "Bedrag": "{report_input.summary_result.Bedrag}",
  "Samenvatting": "{report_input.summary_result.Samenvatting}"
}}"""
        
        # Nu de assessment results
        try:
            assessment_formatted = json.dumps(report_input.assessment_results, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Fout bij het serialiseren van assessment_results: {e}")
            # Handmatige formattering als fallback - veiliger implementatie
            assessment_parts = []
            for key, item in report_input.assessment_results.items():
                criterium_escaped = item.Criterium.replace('"', '\\"')
                score_value = item.Score
                toelichting_escaped = item.Toelichting.replace('"', '\\"')
                
                item_json = f'  "{key}": {{\n'
                item_json += f'    "Criterium": "{criterium_escaped}",\n'
                item_json += f'    "Score": "{score_value}",\n'
                item_json += f'    "Toelichting": "{toelichting_escaped}"\n'
                item_json += '  }'
                
                assessment_parts.append(item_json)
            
            assessment_formatted = "{\n" + ",\n".join(assessment_parts) + "\n}"
        
    except Exception as e:
        print(f"Algemene fout bij het voorbereiden van input data: {e}")
        raise HTTPException(status_code=500, detail=f"Kon de input data niet correct voorbereiden voor het rapport: {str(e)}")

    if not summary_formatted or not assessment_formatted:
        raise HTTPException(status_code=500, detail="Kon de input data niet formatteren voor het rapport.")

    user_message_content = f"""Maak een eindrapport voor de volgende subsidieaanvraag.

Informatie over de aanvraag (samenvatting):
```json
{summary_formatted}
```

Beoordeling van de subsidieaanvraag:
```json
{assessment_formatted}
```

Analyseer de samenvatting en beoordeling, en genereer een eindrapport volgens de structuur in de system prompt.
Focus specifiek op criteria die niet (volledig) aan de eisen voldoen (scores lager dan 8), 
en leg uit of deze nog verbeterd kunnen worden.
"""

    form_data = {
        "model": model_to_use,
        "stream": False,
        "temperature": DEFAULT_TEMPERATURE,
        "response_format": { "type": "json_object" },
        "messages": [
            { "role": "system", "content": REPORT_SYSTEM_PROMPT },
            { "role": "user", "content": user_message_content }
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
            raise HTTPException(status_code=500, detail="Lege response van LLM bij het genereren van het rapport.")

        # Parse de JSON response van de LLM
        try:
            # Verwijder eventuele markdown code block markering
            if raw_response_content.startswith("```json"):
                raw_response_content = raw_response_content[7:]
            if raw_response_content.endswith("```"):
                raw_response_content = raw_response_content[:-3]
            raw_response_content = raw_response_content.strip()

            parsed_data = json.loads(raw_response_content)
            
            # Validatie via Pydantic model
            report_output = SubsidyReportOutput(**parsed_data)
            return report_output

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Fout bij parsen LLM JSON response voor rapport: {e}")
            print(f"Ontvangen raw response LLM (rapport):\n{raw_response_content}")
            raise HTTPException(status_code=500, detail=f"Kon de LLM rapportresponse niet correct verwerken: {e}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in handle_subsidy_report: {e}")
        raise HTTPException(status_code=500, detail=f"Interne serverfout bij het genereren van het rapport: {str(e)}")

@router.post("/complete_assessment", response_model=Dict[str, Any])
async def handle_complete_assessment(
    request: Request,
    assessment_input: SubsidyApplicationInput,
    user = Depends(get_current_user),
):
    """
    Voert alle drie de stappen uit: beoordeling, samenvatting en eindrapport, in één API-call.
    """
    if not assessment_input.application_text:
        raise HTTPException(status_code=400, detail="Subsidieaanvraag tekst mag niet leeg zijn.")
    if not assessment_input.criteria or len(assessment_input.criteria) == 0:
        raise HTTPException(status_code=400, detail="Er zijn geen criteria opgegeven om te beoordelen.")

    # Model Selectie
    DEFAULT_MODEL_FALLBACK = "openai/gpt-4o"
    model_to_use = assessment_input.model or DEFAULT_MODEL_FALLBACK
    
    if not model_to_use:
        print(f"Geen model gespecificeerd, gebruik fallback: {DEFAULT_MODEL_FALLBACK}")
        model_to_use = DEFAULT_MODEL_FALLBACK
    
    print(f"Complete assessment gestart met model: {model_to_use}")
    
    try:
        # Stap 1: Beoordeling maken
        assessment_result = await handle_subsidy_assessment(
            request=request, 
            assessment_input=assessment_input,
            user=user
        )
        
        # Stap 2: Samenvatting maken
        summary_result = await handle_subsidy_summary(
            request=request, 
            assessment_input=assessment_input,
            user=user
        )
        
        # Stap 3: Eindrapport maken
        report_input = SubsidyCombinedReportInput(
            assessment_results=assessment_result.assessment,
            summary_result=summary_result,
            model=model_to_use
        )
        
        report_result = await handle_subsidy_report(
            request=request, 
            report_input=report_input,
            user=user
        )
        
        # Combineer alle resultaten in één response
        return {
            "assessment": assessment_result.assessment,
            "summary": summary_result.dict(),
            "report": report_result.dict()
        }
        
    except Exception as e:
        print(f"Error in handle_complete_assessment: {e}")
        # import traceback
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fout bij complete beoordeling: {str(e)}")