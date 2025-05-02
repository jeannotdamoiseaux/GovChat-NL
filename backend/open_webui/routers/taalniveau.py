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
            chunks.append("")
            continue

        words = paragraph.split()
        paragraph_parts = []
        para_current_length = 0

        for word in words:
            try:
                word_tokens = len(encoding.encode(word))
            except Exception:
                word_tokens = len(word) // 3

            if (current_length + para_current_length + word_tokens > max_tokens and current_chunk_parts) or \
               (para_current_length + word_tokens > max_tokens and paragraph_parts):
                if current_chunk_parts:
                    chunks.append("\n".join(current_chunk_parts))
                    current_chunk_parts = []
                    current_length = 0
                if paragraph_parts:
                    chunks.append(" ".join(paragraph_parts))
                    paragraph_parts = [word]
                    para_current_length = word_tokens
                else:
                     chunks.append(word)
                     para_current_length = 0
            else:
                paragraph_parts.append(word)
                para_current_length += word_tokens

        if paragraph_parts:
            paragraph_text = " ".join(paragraph_parts)
            try:
                paragraph_tokens = len(encoding.encode(paragraph_text))
            except Exception:
                paragraph_tokens = len(paragraph_text) // 3

            if current_length + paragraph_tokens > max_tokens and current_chunk_parts:
                 chunks.append("\n".join(current_chunk_parts))
                 current_chunk_parts = [paragraph_text]
                 current_length = paragraph_tokens
            else:
                 current_chunk_parts.append(paragraph_text)
                 current_length += paragraph_tokens

    if current_chunk_parts:
        chunks.append("\n".join(current_chunk_parts))

    return [chunk for chunk in chunks if chunk is not None]


LANGUAGE_LEVEL_EXAMPLES = {
    "B1": """
- Betreffende -> Over
- Creëren -> Maken
- Prioriteit -> Wat eerst moet, voorrang
- Relevant -> Belangrijk (voor dit onderwerp)
- Verstrekken -> Geven
""",
    "B2": """
- Betreffende -> Met betrekking tot, Over
- Creëren -> Maken, ontwikkelen
- Prioriteit -> Belangrijkste punt, voorrang
- Relevant -> Van toepassing, belangrijk
- Verstrekken -> Geven, aanbieden
""",
    "DEFAULT": """
- Betreffende -> Over
- Creëren -> Ontwerpen, vormen, vormgeven, maken
- Prioriteit -> Voorrang, voorkeur
- Relevant -> Belangrijk
- Verstrekken -> Geven
"""
}

LEVEL_DESCRIPTIONS = {
    "B1": "Het B1-niveau kenmerkt zich door duidelijk en eenvoudig taalgebruik, geschikt voor een breed publiek met basisvaardigheden in de taal.",
    "B2": "Het B2-niveau kenmerkt zich door helder en gedetailleerd taalgebruik, geschikt voor een publiek met gevorderde taalvaardigheden. De tekst moet toegankelijk zijn zonder overmatig gebruik van complexe termen, gericht op lezers die bekend zijn met de basisprincipes van de taal en in staat zijn om zowel praktische als theoretische onderwerpen te begrijpen."
}
LEVEL_GUIDELINES = {
    "B1": """- Gebruik korte zinnen en vermijd lange, complexe zinsconstructies.
- Vervang moeilijke woorden door meer gangbare alternatieven.
- Leg technische termen en (ambtelijk) jargon uit in eenvoudige bewoordingen.
- Gebruik actieve zinsconstructies waar mogelijk.
- Vermijd passieve zinnen en ingewikkelde grammaticale constructies.
- Gebruik concrete voorbeelden om abstracte concepten te verduidelijken.""",
    "B2": """- Gebruik korte tot middelmatige zinnen en vermijd extreme complexiteit, maar behoud enige diepgang in de formulering.
- Vervang zeer complexe woorden door alternatieven die nauwkeurig zijn maar minder specialistisch.
- Leg technische termen en ambtelijk jargon duidelijk uit, waarbij je enige mate van detail behoudt om de nauwkeurigheid te waarborgen.
- Gebruik actieve zinsconstructies waar mogelijk, maar passieve zinnen kunnen gebruikt worden als dit de tekst logischer maakt.
- Beperk ingewikkelde grammaticale constructies, maar behoud een zekere variatie in de zinsopbouw.
- Gebruik passende en concrete voorbeelden om abstracte of lastigere concepten uit te leggen, zodat de lezer een context heeft om de informatie te begrijpen."""
}
LEVEL_SOURCE_EXAMPLE = {
    "B1": "C1",
    "B2": "C2"
}

async def generate_version(request: Request, chunk: str, model: str, preserved_words: List[str], language_level: str, user: Any, index: int, temperature: float) -> dict:
    """Generate a single version of simplified text for a specific temperature and return with index and temperature"""
    if not chunk or chunk.isspace():
        return {"index": index, "temperature": temperature, "text": chunk, "error": None}

    preserved_words_text = ", ".join(f"'{word}'" for word in preserved_words) if preserved_words else "geen"
    level_upper = language_level.upper()
    level_examples = LANGUAGE_LEVEL_EXAMPLES.get(level_upper, LANGUAGE_LEVEL_EXAMPLES["DEFAULT"])

    selected_description = LEVEL_DESCRIPTIONS.get(level_upper, LEVEL_DESCRIPTIONS["B1"])
    selected_guidelines = LEVEL_GUIDELINES.get(level_upper, LEVEL_GUIDELINES["B1"])
    selected_source_example = LEVEL_SOURCE_EXAMPLE.get(level_upper, LEVEL_SOURCE_EXAMPLE["B1"])
    effective_language_level = language_level if level_upper in ["B1", "B2"] else "B1"

    generation_system_prompt = f"""Je taak is om de volgende tekst te analyseren en te herschrijven naar een versie die voldoet aan het {effective_language_level}-taalniveau.
Hierbij is het belangrijk om de informatie zo letterlijk mogelijk over te brengen en de structuur zoveel mogelijk te behouden, zonder onnodige weglatingen.
{selected_description}

Hier zijn enkele richtlijnen om je te helpen bij deze taak:
{selected_guidelines}

Hier zijn enkele voorbeelden van woorden op {selected_source_example}-niveau en hun eenvoudigere {effective_language_level}-equivalenten:{level_examples}
BELANGRIJK: De volgende woorden moeten exact behouden blijven en mogen NIET vereenvoudigd worden: {preserved_words_text}.

Zorg ervoor dat de hoofdboodschap van de tekst behouden blijft en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.
BELANGRIJK: Tekst tussen dubbele sterretjes (zoals **dit**) moet ook vereenvoudigd worden naar {effective_language_level}-niveau. Behoud de dubbele sterretjes rond de vereenvoudigde tekst in de output. Dit geldt ook voor kopjes of andere belangrijke termen die zo gemarkeerd zijn.
Zorg ervoor dat de hoofdboodschap van de tekst behouden blijft en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.
Gebruik deze instructies om de tekst te vereenvoudigen en zorg ervoor dat deze voldoet aan het {effective_language_level}-taalniveau.
Plaats de verbeterde paragraaf tussen "<<<" en ">>>" tekens. Als de tekst te kort is om te verbeteren neem je de tekst een-op-een over en plaats deze tussen de genoemende tekens, bijv. "<<< **Artikel 3.2** >>>"."""

    form_data = {
        "model": model,
        "stream": False,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": generation_system_prompt},
            {"role": "user", "content": chunk}
        ]
    }

    try:
        response = await generate_chat_completion(request=request, form_data=form_data, user=user)
        llm_output = response['choices'][0]['message']['content']
        simplified_text = llm_output.strip()
        simplified_text = re.sub(r'^```[a-zA-Z]*\n?', '', simplified_text)
        simplified_text = re.sub(r'\n?```$', '', simplified_text)
        match = re.search(r'<<<([\s\S]*?)>>>', simplified_text, re.DOTALL)
        if match:
            simplified_text = match.group(1).strip()
        else:
            print(f"Warning: Delimiters '<<<' and '>>>' not found in generation output for chunk {index}, temp {temperature}. Using cleaned output.")
            simplified_text = simplified_text.replace('<<<', '').replace('>>>', '').strip()

        return {"index": index, "temperature": temperature, "text": simplified_text, "error": None}
    except Exception as e:
        print(f"Error processing chunk {index} with model {model} at temperature {temperature}: {e}")
        return {"index": index, "temperature": temperature, "text": chunk, "error": str(e)}

async def select_best_version(request: Request, original_chunk: str, generated_versions: List[dict], model: str, language_level: str, preserved_words: List[str], user: Any, index: int) -> dict:
    """Selects the best version from generated texts using an LLM based on a specific prompt."""

    successful_versions = [v for v in generated_versions if v.get("error") is None and v.get("text", "").strip()]

    if not successful_versions:
         print(f"Warning: No successful versions generated for chunk {index}. Returning original chunk.")
         return {"index": index, "text": original_chunk, "selection_error": "No successful versions to select from."}

    preserved_words_text = ", ".join(f"'{word}'" for word in preserved_words) if preserved_words else "geen"
    level_upper = language_level.upper()
    level_examples = LANGUAGE_LEVEL_EXAMPLES.get(level_upper, LANGUAGE_LEVEL_EXAMPLES["DEFAULT"])

    selected_description = LEVEL_DESCRIPTIONS.get(level_upper, LEVEL_DESCRIPTIONS["B1"])
    selected_guidelines = LEVEL_GUIDELINES.get(level_upper, LEVEL_GUIDELINES["B1"])
    selected_source_example = LEVEL_SOURCE_EXAMPLE.get(level_upper, LEVEL_SOURCE_EXAMPLE["B1"])
    effective_language_level = language_level if level_upper in ["B1", "B2"] else "B1"

    selection_system_prompt = f"""Je taak is om de volgende tekst te analyseren en te herschrijven naar een versie die voldoet aan het {effective_language_level}-taalniveau.
Hierbij is het belangrijk om de informatie zo letterlijk mogelijk over te brengen en de structuur zoveel mogelijk te behouden, zonder onnodige weglatingen.
{selected_description}

Hier zijn enkele richtlijnen om je te helpen bij deze taak:
{selected_guidelines}

Hier zijn enkele voorbeelden van woorden op {selected_source_example}-niveau en hun eenvoudigere {effective_language_level}-equivalenten:{level_examples}
BELANGRIJK: De volgende woorden moeten exact behouden blijven en mogen NIET vereenvoudigd worden: {preserved_words_text}.

Zorg ervoor dat de inhoud en nuances van de oorspronkelijke tekst behouden blijven en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.
BELANGRIJK: Zorg ervoor dat tekst tussen dubbele sterretjes (zoals **dit**) ook vereenvoudigd is naar {effective_language_level}-niveau in de definitieve versie. Behoud de dubbele sterretjes rond de vereenvoudigde tekst in de output. Dit geldt ook voor kopjes of andere belangrijke termen die zo gemarkeerd zijn.

Zorg ervoor dat de inhoud en nuances van de oorspronkelijke tekst behouden blijven en dat de vereenvoudigde versie nog steeds een accurate weergave is van de oorspronkelijke inhoud.
Je ontvangt de originele paragraaf, samen met enkele varianten van deze tekst in eenvoudigere taal ({effective_language_level}). Deze varianten kunnen nog de "<<<" en ">>>" tekens bevatten. Het is jouw taak om tot een definitieve {effective_language_level}-versie te komen ZONDER deze tekens, maar wel met behoud van **dikgedrukte** tekst.

Plaats de definitieve, verbeterde paragraaf tussen "<<<" en ">>>" tekens. Als de tekst te kort is om te verbeteren neem je de tekst een-op-een over en plaats deze tussen de genoemende tekens, bijv. "<<< **Artikel 3.2** >>>"."""

    variants_text = ""
    for i, version_data in enumerate(successful_versions):
        variant_text = version_data.get('text', '')
        variant_text = variant_text.replace('<<<', '').replace('>>>', '').strip()
        variants_text += f"Variant {i+1} (gegenereerd met temperature={version_data['temperature']}):\n{variant_text}\n---\n"

    selection_user_content = f"""Originele Paragraaf:
---
{original_chunk}
---

Gegenereerde {effective_language_level} Varianten:
---
{variants_text}
Kies de beste variant of combineer/verbeter ze tot de definitieve {effective_language_level}-versie, geplaatst tussen <<< en >>>. Zorg ervoor dat tekst binnen **dubbele sterretjes** ook vereenvoudigd is en behoud de sterretjes in de output.
BELANGRIJK: Zorg ervoor dat de volgende woorden exact behouden blijven en NIET vereenvoudigd worden: {preserved_words_text}."""

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
        llm_output = re.sub(r'^```[a-zA-Z]*\n?', '', llm_output)
        llm_output = re.sub(r'\n?```$', '', llm_output)
        match = re.search(r'<<<([\s\S]*?)>>>', llm_output, re.DOTALL)
        if match:
            final_text = match.group(1).strip()
            return {"index": index, "text": final_text}
        else:
            print(f"Warning: Could not parse '<<<' and '>>>' from selection output for chunk {index}. Output was: {llm_output}")
            fallback_text = llm_output.replace('<<<', '').replace('>>>', '').strip()
            return {"index": index, "text": fallback_text, "selection_warning": "Could not parse final version delimiters from selection output."}

    except Exception as e:
        print(f"Error during selection step for chunk {index} with model {model}: {e}")
        return {"index": index, "text": original_chunk, "selection_error": str(e)}


class SimplifyTextRequest(BaseModel):
    text: str
    model: str
    preserved_words: list[str] = []
    language_level: str = "B1"

@router.post("/translate")
async def simplify_text_endpoint(request: Request, data: SimplifyTextRequest, user = Depends(get_current_user)):
    """Endpoint to simplify text to B1/B2 level. Generates 3 versions per chunk, then selects the best."""

    chunks = split_into_chunks(data.text)
    num_chunks = len(chunks)
    temperatures = [1.0, 0.8, 0.6]

    if num_chunks == 0:
        async def empty_stream():
             yield json.dumps({"total_chunks": 0}) + "\n"
             if False: yield None
        return StreamingResponse(empty_stream(), media_type="application/x-ndjson")

    async def stream_results():
        yield json.dumps({"total_chunks": num_chunks}) + "\n"

        generation_tasks = []
        for i, chunk in enumerate(chunks):
            for temp in temperatures:
                generation_tasks.append(
                    generate_version(request, chunk, data.model, data.preserved_words, data.language_level, user, i, temp)
                )

        chunk_results = {i: [] for i in range(num_chunks)}
        tasks_outstanding = {i: len(temperatures) for i in range(num_chunks)}
        selection_tasks = []

        for future in asyncio.as_completed(generation_tasks):
            try:
                gen_result = await future
                idx = gen_result['index']
                chunk_results[idx].append(gen_result)
                tasks_outstanding[idx] -= 1

                if tasks_outstanding[idx] == 0:
                    original_chunk = chunks[idx]
                    versions = chunk_results[idx]
                    selection_tasks.append(
                        select_best_version(request, original_chunk, versions, data.model, data.language_level, data.preserved_words, user, idx)
                    )

            except Exception as e:
                 print(f"Error awaiting generation task result: {e}")
                 pass

        for future in asyncio.as_completed(selection_tasks):
             try:
                 final_result = await future
                 if 'text' in final_result and isinstance(final_result['text'], str):
                     final_result['text'] = final_result['text'].replace('<<<', '').replace('>>>', '').strip()
                 yield json.dumps(final_result) + "\n"
             except Exception as e:
                 print(f"Error awaiting or processing selection task result: {e}")

    return StreamingResponse(stream_results(), media_type="application/x-ndjson")