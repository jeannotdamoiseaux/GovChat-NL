import json # Import json module
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Any, Optional, List, Dict, Union
from datetime import datetime
import json
import hashlib
import traceback
import os
import time

from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.auth import get_current_user
from open_webui.utils.subsidy_storage import SubsidyFileStorage  # Importeer de nieuwe helper

# Initialiseer de router
router = APIRouter()

# Initialiseer de storage helper
subsidy_storage = SubsidyFileStorage()

# Model voor subsidiecriteria
class SubsidyCriterion(BaseModel):
    id: int
    text: str

class SubsidyResponse(BaseModel):
    criteria: List[SubsidyCriterion]
    summary: Optional[str] = None
    savedId: Optional[str] = None
    timestamp: Optional[str] = None
    name: Optional[str] = None

class SubsidyQueryInput(BaseModel):
    user_input: str
    model: Optional[str] = None

class SubsidyQueryOutput(BaseModel):
    criteria: List[SubsidyCriterion]
    summary: Optional[str] = None

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
SYSTEM_PROMPT = """Je bent een expert op het gebied van Nederlandse subsidies. Analyseer de volgende subsidieregeling die door de gebruiker wordt verstrekt.

Identificeer alle criteria die in de regeling worden genoemd, inclusief de nuances uit de toelichting die onderaan het document wordt vermeld. Zorg voor een volledig overzicht waarbij elk criterium wordt genummerd volgens de oorspronkelijke regeling. Zorg ervoor dat de resulterende opsomming juistheid, consistentie en volledigheid vertoont.

BELANGRIJK: Zorg ervoor dat je ALLE artikelen van de regeling opneemt in je set van criteria. Bij twijfel moet je het artikel met onderliggende criteria altijd toevoegen om te voorkomen dat je iets mist.

Geef je antwoord ALLEEN als een geldig JSON-object terug. Het JSON-object moet de volgende structuur hebben:
{
  "criteria": [
    { "id": 1, "text": "Artikel X.Y: Volledige tekst van criterium inclusief nuances..." },
    { "id": 2, "text": "Artikel X.Z: Volledige tekst van criterium inclusief nuances..." },
    // ... meer criteria
  ],
  "summary": "Een korte samenvatting van de regeling met vermelding van de belangrijkste doelstellingen en voorwaarden."
}

Zorg ervoor dat:
1. De 'text' van elk criterium duidelijk, volledig en nauwkeurig is
2. Elk criterium verwijst naar het bijbehorende artikel uit de regeling
3. Alle artikelen en onderdelen van de regeling worden opgenomen
4. De nummering in het 'id' veld opeenvolgend is
5. Het veld 'summary' een beknopt maar volledig overzicht van de regeling bevat

Als er geen criteria gevonden worden, geef dan een lege lijst terug: { "criteria": [], "summary": "Geen specifieke criteria gevonden." }. 

Geef GEEN andere tekst terug buiten het JSON-object."""

# --- System Prompt voor beoordeling subsidieaanvraag ---
ASSESSMENT_SYSTEM_PROMPT = """Je bent verantwoordelijk voor het beoordelen van een subsidieaanvraag aan de hand van een subsidieregeling. Deze regeling ontvang je als een geneste JSON-indeling, waarbij elk artikel en daaronder de bijbehorende criteria worden weergegeven. Het is jouw taak om voor elk criterium in de ontvangen JSON een score tussen 0 en 10, en een beknopte toelichting die de redenering achter de gegeven score beschrijft, toe te voegen.

Een score van 0 geeft aan dat het criterium niet voldoet, terwijl een score van 10 aangeeft dat het criterium volledig voldoet. In het geval dat een criterium een afwijzingsgrond is, betekent een score van 10 dat de afwijzingsgrond niet van toepassing is, en een score van 0 betekent dat deze wel van toepassing is.

Na het beoordelen van alle artikelen en criteria, controleer of er geen gemiste artikelen of criteria zijn. Als er gemiste onderdelen zijn, dien je deze alsnog te beoordelen en te documenteren.

Het is belangrijk om geen aannames te maken en alleen uit te gaan van de informatie in de aanvraag. Als je niet zeker weet hoe je een criterium moet beoordelen, kun je "Onzeker" gebruiken. De vereiste outputstructuur is opnieuw een geneste JSON-indeling, die zoals hieronder aangegeven moet zijn, met behulp van accolades voor de notatie.

{
    "1": {
        "Criterium": "",
        "Score": "",
        "Toelichting": ""
    },
    "2": {
        "Criterium": "",
        "Score": "",
        "Toelichting": ""
    }
}

Zorg ervoor dat je altijd nested accolades ({}) gebruikt om de structuur van je output weer te geven. Wees volledig en neem altijd alle artikelen mee in je evaluatie. Geef ALLEEN het JSON-object terug zonder extra tekst."""

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

@router.post("/save", response_model=Dict[str, Any])
async def save_subsidy_data(
    request: Request,
    data: SubsidyResponse,
    user = Depends(get_current_user)
):
    """Sla subsidiecriteria op in een bestand"""
    print(f"save_subsidy_data aangeroepen voor gebruiker {user.id}")
    
    try:
        # Removed deduplication check
        
        # Wanneer criteria in Pydantic model zitten, eerst naar dict converteren
        criteria_list = []
        if data.criteria:
            try:
                # Voor Pydantic v2
                criteria_list = [c.model_dump() for c in data.criteria]
            except AttributeError:
                try:
                    # Voor Pydantic v1
                    criteria_list = [c.dict() for c in data.criteria]
                except AttributeError:
                    # Fallback - Probeer direct als dictionary te gebruiken
                    criteria_list = [{"id": c.id, "text": c.text} for c in data.criteria]
        
        # Bereid criteria voor voor opslag
        criteria_data = {
            "criteria": criteria_list,
            "summary": data.summary,
            "is_selection": getattr(data, 'isSelection', False)  # Behoud is_selection flag
        }
        
        # Als het een selectie is, geef het een speciale naam
        name = data.name
        if getattr(data, 'isSelection', False) and not name.startswith("Selectie:"):
            name = f"Selectie: {name or datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Sla op met de helper
        subsidy_id = subsidy_storage.save_criteria(
            user_id=user.id, 
            criteria=criteria_data,
            name=name
        )
        
        print(f"Succesvol opgeslagen met ID: {subsidy_id}")
        
        return {
            "success": True,
            "id": subsidy_id,
            "message": "Subsidie criteria opgeslagen"
        }
    
    except Exception as e:
        print(f"Error bij opslaan subsidiecriteria: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Kon criteria niet opslaan: {str(e)}")


@router.get("/list", response_model=List[SubsidyResponse])
async def list_subsidy_data(
    request: Request,
    user = Depends(get_current_user)
):
    """Haal alle opgeslagen criteria op voor een gebruiker"""
    print(f"list_subsidy_data called for user {user.id}")
    
    try:
        # Haal de lijst op via de helper
        criteria_list = subsidy_storage.list_criteria_for_user(user_id=user.id)
        
        print(f"Found {len(criteria_list)} items for user {user.id}")
        
        # Converteer naar het response model formaat
        result = []
        for item in criteria_list:
            try:
                criteria_objects = []
                for c in item.get("criteria", []):
                    # Zorg dat criteria de juiste structuur heeft
                    if isinstance(c, dict) and "id" in c and "text" in c:
                        criteria_objects.append(SubsidyCriterion(**c))
                
                result.append(SubsidyResponse(
                    criteria=criteria_objects,
                    summary=item.get("summary"),
                    savedId=item.get("id"),
                    timestamp=item.get("timestamp"),
                    name=item.get("name")
                ))
            except Exception as e:
                print(f"Error converting item: {e}, item: {item}")
                continue
            
        print(f"Returning {len(result)} formatted items")
        return result
        
    except Exception as e:
        print(f"Error in list_subsidy_data: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Kon criteria niet ophalen: {str(e)}")


@router.delete("/{subsidy_id}", response_model=Dict[str, Any])
async def delete_subsidy_data(
    request: Request,
    subsidy_id: str,
    user = Depends(get_current_user)
):
    """Verwijder opgeslagen criteria"""
    try:
        # Verwijder via de helper
        success = subsidy_storage.delete_criteria(
            subsidy_id=subsidy_id,
            user_id=user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Subsidiecriteria niet gevonden")
            
        return {
            "success": True,
            "message": "Subsidiecriteria verwijderd"
        }
        
    except HTTPException:
        raise
        
    except Exception as e:
        print(f"Error bij verwijderen subsidiecriteria: {e}")
        raise HTTPException(status_code=500, detail=f"Kon criteria niet verwijderen: {str(e)}")

@router.post("/query", response_model=SubsidyQueryOutput)
async def handle_subsidy_query(
    request: Request,
    query_input: SubsidyQueryInput,
    user = Depends(get_current_user)
):
    """
    Neemt een subsidieregeling, extraheert criteria via LLM als JSON,
    slaat het resultaat op en retourneert de gestructureerde data.
    """
    if not query_input.user_input:
        raise HTTPException(status_code=400, detail="Input mag niet leeg zijn.")

    # Removed deduplication check using input_hash
    
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

            # Sla de criteria op voor toekomstige deduplicatie
            criteria_data = {
                "criteria": [{"id": c.id, "text": c.text} for c in output_data.criteria],
                "summary": output_data.summary
            }
            
            subsidy_storage.save_criteria(
                user_id=user.id,
                criteria=criteria_data,
                input_text=query_input.user_input,
                name=f"Subsidie {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )

            return output_data

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Fout bij parsen LLM JSON response: {e}")
            print(f"Ontvangen raw response:\n{raw_response_content}")
            raise HTTPException(status_code=500, detail=f"Kon de LLM response niet correct verwerken: {e}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error calling generate_chat_completion or processing: {e}")
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
            raise HTTPException(status_code=500, detail="Lege response van LLM.")

        # Parse de JSON response van de LLM
        try:
            # Soms zit de JSON in een code block, probeer dat te strippen
            if raw_response_content.startswith("```json"):
                raw_response_content = raw_response_content[7:]
                
            if raw_response_content.endswith("```"):
                raw_response_content = raw_response_content[:-3]
                
            raw_response_content = raw_response_content.strip()

            parsed_data = json.loads(raw_response_content)
            
            # Valideer de structuur (basis check)
            if not parsed_data or not isinstance(parsed_data, dict):
                raise ValueError("Ongeldige JSON structuur: verwacht een dictionary met assessment items.")

            # Converteer scores naar string indien nodig
            for key, value in parsed_data.items():
                if isinstance(value, dict) and "Score" in value:
                    parsed_data[key]["Score"] = str(parsed_data[key]["Score"])

            assessment_output = SubsidyAssessmentOutput(assessment=parsed_data)
            return assessment_output

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Fout bij parsen LLM JSON response: {e}")
            print(f"Ontvangen raw response:\n{raw_response_content}")
            raise HTTPException(status_code=500, detail=f"Kon de LLM response niet correct verwerken: {e}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error in handle_subsidy_assessment: {e}")
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
            summary_output = SubsidySummaryOutput(**parsed_data)
            return summary_output

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Fout bij parsen LLM JSON response voor samenvatting: {e}")
            print(f"Ontvangen raw response:\n{raw_response_content}")
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
        try:
            # In Pydantic v2+ gebruik je model_dump() in plaats van dict()
            summary_dict = report_input.summary_result.model_dump()
        except AttributeError:
            try:
                summary_dict = report_input.summary_result.dict()
            except AttributeError:
                summary_dict = dict(report_input.summary_result)
                
        summary_formatted = json.dumps(summary_dict, ensure_ascii=False)
        
        # Nu de assessment results
        try:
            # Assessment results is al een dict
            assessment_formatted = json.dumps(report_input.assessment_results, ensure_ascii=False)
        except Exception as e:
            print(f"Fout bij formatteren assessment: {e}")
            raise HTTPException(status_code=500, detail="Kon de beoordelingsresultaten niet formatteren.")
        
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
        raise HTTPException(status_code=500, detail=f"Fout bij complete beoordeling: {str(e)}")

@router.get("/debug/write-test", response_model=Dict[str, Any])
async def test_write_access(
    request: Request,
    user = Depends(get_current_user)
):
    """Test endpoint om te controleren of de bestandsopslag werkt"""
    try:
        # Test directory creatie en schrijfpermissies
        test_dir = subsidy_storage.base_dir
        os.makedirs(test_dir, exist_ok=True)
        
        # Test bestand aanmaken en schrijven
        test_file = os.path.join(test_dir, f"test_write_{int(time.time())}.txt")
        with open(test_file, 'w') as f:
            f.write(f"Test schrijftoegang voor gebruiker {user.id}")
        
        # Lees het bestand om te verifiëren dat het schrijven is gelukt
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Verwijder het testbestand
        os.remove(test_file)
        
        # Lijst alle bestanden in de directory
        files = os.listdir(test_dir)
        
        return {
            "success": True,
            "message": f"Schrijftest geslaagd in {test_dir}",
            "content": content,
            "test_file": test_file,
            "files_in_directory": files[:10],  # Toon slechts de eerste 10 bestanden
            "directory_exists": os.path.exists(test_dir),
            "is_writable": os.access(test_dir, os.W_OK)
        }
    except Exception as e:
        print(f"Fout bij testen schrijftoegang: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Voeg deze nieuwe endpoints toe

@router.post("/select/{subsidy_id}", response_model=Dict[str, Any])
async def select_subsidy_data(
    request: Request,
    subsidy_id: str,
    user = Depends(get_current_user)
):
    """Stel een bepaalde set subsidiecriteria in als geselecteerd voor een gebruiker"""
    try:
        # Controleer of de subsidie bestaat
        subsidy_data = subsidy_storage.get_criteria_by_id(subsidy_id, user.id)
        
        if not subsidy_data:
            raise HTTPException(status_code=404, detail="Subsidiecriteria niet gevonden")
        
        # Sla de selectie op voor deze gebruiker
        user_settings = {
            "user_id": user.id,
            "last_selection_id": subsidy_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Gebruik een speciale bestandsnaam voor gebruikersinstellingen
        filename = f"user_settings_{user.id}.json"
        filepath = os.path.join(subsidy_storage.base_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(user_settings, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "Subsidie selectie ingesteld",
            "selection_id": subsidy_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error bij instellen subsidie selectie: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Kon selectie niet instellen: {str(e)}")

@router.get("/selection", response_model=Dict[str, Any])
async def get_current_selection(
    request: Request,
    user = Depends(get_current_user)
):
    """Haal de huidige selectie op voor een gebruiker"""
    try:
        # Zoek de gebruikersinstellingen
        filename = f"user_settings_{user.id}.json"
        filepath = os.path.join(subsidy_storage.base_dir, filename)
        
        if not os.path.exists(filepath):
            return {
                "success": True,
                "has_selection": False,
                "message": "Geen huidige selectie gevonden"
            }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            user_settings = json.load(f)
        
        selection_id = user_settings.get("last_selection_id")
        if not selection_id:
            return {
                "success": True,
                "has_selection": False,
                "message": "Geen huidige selectie gevonden"
            }
            
        # Haal de geselecteerde subsidie op
        subsidy_data = subsidy_storage.get_criteria_by_id(selection_id, user.id)
        
        if not subsidy_data:
            return {
                "success": True,
                "has_selection": False,
                "message": "Geselecteerde subsidie niet meer gevonden"
            }
        
        # Converteer de data naar het juiste formaat
        criteria = []
        for c in subsidy_data.get("criteria", []):
            if isinstance(c, dict) and "id" in c and "text" in c:
                criteria.append({"id": c["id"], "text": c["text"]})
        
        selection = {
            "criteria": criteria,
            "summary": subsidy_data.get("summary"),
            "name": subsidy_data.get("name"),
            "savedId": subsidy_data.get("id"),
            "timestamp": subsidy_data.get("timestamp"),
            "isSelection": True
        }
        
        return {
            "success": True,
            "has_selection": True,
            "selection": selection
        }
        
    except Exception as e:
        print(f"Error bij ophalen subsidie selectie: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "has_selection": False,
            "message": f"Kon selectie niet ophalen: {str(e)}"
        }

# Voeg deze nieuwe endpoints toe aan het einde van het bestand

import os
import json
import traceback
from datetime import datetime

@router.post("/global/set/{subsidy_id}", response_model=Dict[str, Any])
async def set_global_selection(
    request: Request,
    subsidy_id: str,
    user = Depends(get_current_user)
):
    """Stel een bepaalde set subsidiecriteria in als globale standaard voor alle gebruikers"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Alleen beheerders kunnen de globale selectie instellen")
    
    try:
        # Controleer of de subsidie bestaat
        subsidy_data = subsidy_storage.get_criteria_by_id(subsidy_id)
        
        if not subsidy_data:
            raise HTTPException(status_code=404, detail="Subsidiecriteria niet gevonden")
        
        # Sla de globale selectie op
        global_settings = {
            "global_selection_id": subsidy_id,
            "set_by_user_id": user.id,
            "set_by_user_name": user.name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Gebruik een speciale bestandsnaam voor globale instellingen
        filename = "global_subsidy_settings.json"
        filepath = os.path.join(subsidy_storage.base_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(global_settings, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "Globale subsidie selectie ingesteld voor alle gebruikers",
            "selection_id": subsidy_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error bij instellen globale subsidie selectie: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Kon globale selectie niet instellen: {str(e)}")

@router.get("/global", response_model=Dict[str, Any])
async def get_global_selection(
    request: Request,
    user = Depends(get_current_user)
):
    """Haal de globale selectie op die voor alle gebruikers geldt"""
    try:
        # Zoek de globale instellingen
        filename = "global_subsidy_settings.json"
        filepath = os.path.join(subsidy_storage.base_dir, filename)
        
        if not os.path.exists(filepath):
            return {
                "success": True,
                "has_global_selection": False,
                "message": "Geen globale selectie gevonden"
            }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            global_settings = json.load(f)
        
        selection_id = global_settings.get("global_selection_id")
        if not selection_id:
            return {
                "success": True,
                "has_global_selection": False,
                "message": "Geen globale selectie ID gevonden"
            }
            
        # Haal de geselecteerde subsidie op
        subsidy_data = subsidy_storage.get_criteria_by_id(selection_id)
        
        if not subsidy_data:
            return {
                "success": True, 
                "has_global_selection": False,
                "message": "Globale selectie niet meer gevonden"
            }
        
        # Converteer de data naar het juiste formaat
        criteria = []
        for c in subsidy_data.get("criteria", []):
            if isinstance(c, dict) and "id" in c and "text" in c:
                criteria.append({"id": c["id"], "text": c["text"]})
        
        selection = {
            "criteria": criteria,
            "summary": subsidy_data.get("summary", ""),
            "name": subsidy_data.get("name", "Globale standaard selectie"),
            "savedId": subsidy_data.get("id", ""),
            "timestamp": subsidy_data.get("timestamp", datetime.now().isoformat()),
            "isSelection": True,
            "isGlobalSelection": True
        }
        
        print(f"Returning global selection with {len(criteria)} criteria")
        
        return {
            "success": True,
            "has_global_selection": True,
            "selection": selection,
            "set_by_user_id": global_settings.get("set_by_user_id"),
            "set_by_user_name": global_settings.get("set_by_user_name"),
            "timestamp": global_settings.get("timestamp")
        }
        
    except Exception as e:
        print(f"Error bij ophalen globale subsidie selectie: {e}")
        traceback.print_exc()
        return {
            "success": False,
            "has_global_selection": False,
            "message": f"Kon globale selectie niet ophalen: {str(e)}"
        }