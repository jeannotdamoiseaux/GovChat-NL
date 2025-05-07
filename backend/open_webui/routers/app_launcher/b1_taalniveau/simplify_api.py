import logging
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import List, Any
from pydantic import BaseModel, constr, conlist
import asyncio
import json
import re

try:
    import tiktoken
except ImportError:
    tiktoken = None

from open_webui.utils.chat import generate_chat_completion
from open_webui.utils.auth import get_current_user
from .language_levels import get_level_data, DEFAULT_LANGUAGE_LEVEL

# ------ Configuratie ------

MAX_TEXT_LENGTH = 15_000
MAX_PRESERVED_WORDS = 100
MAX_CHUNKS = 30
MIN_CHUNK_TOKENS = 30
CHUNK_MAX_TOKENS = 1200
MODEL_TOKEN_LIMIT = 8192
TEMPERATURES = [1.0, 0.8, 0.6]
ENCODING_NAME = "cl100k_base"
DEFAULT_LANGUAGE_LEVEL = DEFAULT_LANGUAGE_LEVEL

# Logger configuratie
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# ------ Helpers ------

def get_encoding():
    if tiktoken:
        try:
            return tiktoken.get_encoding(ENCODING_NAME)
        except Exception as e:
            logger.warning(f"tiktoken encoding '{ENCODING_NAME}' niet beschikbaar: {e}")
    return None

def count_tokens(text: str, encoding=None) -> int:
    if encoding:
        try:
            return len(encoding.encode(text))
        except Exception:
            pass
    return max(1, len(text) // 3)

def split_into_chunks(text: str, max_tokens: int = CHUNK_MAX_TOKENS, min_chunk_tokens: int = MIN_CHUNK_TOKENS) -> List[str]:
    """Split text into chunks van ongeveer max_tokens. Houdt rekening met alinea's en woorden. Lange regels worden gesplitst."""
    encoding = get_encoding()
    paragraphs = re.split(r'(\n+)', text)
    chunks = []
    current_chunk = []
    current_tokens = 0
    for para in paragraphs:
        if not para.strip():
            if current_chunk and current_tokens >= min_chunk_tokens:
                chunks.append("".join(current_chunk).strip())
                current_chunk, current_tokens = [], 0
            continue
        words = para.split()
        for w in words:
            word_tokens = count_tokens(w, encoding)
            if word_tokens > max_tokens:
                splitpos = max_tokens * 3
                for i in range(0, len(w), splitpos):
                    part = w[i:i+splitpos]
                    part_tokens = count_tokens(part, encoding)
                    if current_tokens + part_tokens > max_tokens and current_chunk:
                        chunks.append("".join(current_chunk).strip())
                        current_chunk, current_tokens = [], 0
                    current_chunk.append(part + ' ')
                    current_tokens += part_tokens
                continue
            if current_tokens + word_tokens > max_tokens and current_chunk:
                chunks.append("".join(current_chunk).strip())
                current_chunk, current_tokens = [], 0
            current_chunk.append(w + ' ')
            current_tokens += word_tokens
        current_chunk.append('\n')
    if current_chunk and current_tokens >= min_chunk_tokens:
        chunks.append("".join(current_chunk).strip())
    return [c for c in chunks if c.strip()]

def get_prompts(language_level, preserved_words, step="generation"):
    level = get_level_data(language_level)
    preserved_words_text = ", ".join(f"'{w}'" for w in preserved_words) if preserved_words else "geen"
    if step == "generation":
        system_prompt = f"""Je taak is om de volgende tekst te analyseren en te herschrijven naar het gewenste niveau ({language_level}).
{level['description']}
Hier zijn enkele richtlijnen:
{level['guidelines']}
Voorbeelden van vereenvoudiging ({level['source_example_level']}→{language_level}):
{level['examples']}
BELANGRIJK: De volgende woorden moeten exact behouden blijven: {preserved_words_text}.
Vereenvoudig ook tekst tussen dubbele sterretjes (**dit**), maar behoud de sterretjes.
Plaats alleen de herschreven tekst tussen <<< en >>>. Neem korte, niet-te-vereenvoudigen tekst ook zo over."""
        return system_prompt
    elif step == "selection":
        system_prompt = f"""Je taak is om de beste of gecombineerde versie te selecteren uit eerdere herschrijvingen (in {language_level}-taalniveau).
{level['description']}
Richtlijnen:
{level['guidelines']}
Vereenvoudigingsvoorbeelden:{level['examples']}
BELANGRIJK: De volgende woorden moeten exact behouden blijven: {preserved_words_text}.
Vereenvoudig als nodig tekst tussen **sterretjes**, maar behoud de markering.
Plaats alleen het definitieve herschreven resultaat tussen <<< en >>> (geen extra uitleg)."""
        return system_prompt
    else:
        raise ValueError("Unknown prompt step")

def clean_llm_output(output: str) -> str:
    output = re.sub(r'^```[a-zA-Z]*\n?', '', output)
    output = re.sub(r'\n?```$', '', output)
    match = re.search(r'<<<([\s\S]*?)>>>', output, re.DOTALL)
    if match:
        return match.group(1).strip()
    return output.replace('<<<', '').replace('>>>', '').strip()

# ------ LLM async helpers ------

async def generate_version(request: Request, chunk: str, model: str, preserved_words: List[str], language_level: str, user: Any, index: int, temperature: float) -> dict:
    if not chunk or chunk.isspace():
        return {"index": index, "temperature": temperature, "text": chunk, "error": None}
    system_prompt = get_prompts(language_level, preserved_words, step="generation")
    form_data = {
        "model": model,
        "stream": False,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chunk}
        ]
    }
    try:
        response = await generate_chat_completion(request=request, form_data=form_data, user=user)
        llm_output = response['choices'][0]['message']['content']
        simplified_text = clean_llm_output(llm_output)
        return {"index": index, "temperature": temperature, "text": simplified_text, "error": None}
    except Exception as e:
        logger.error(f"Error processing chunk {index} with model {model} at temperature {temperature}: {e}")
        return {"index": index, "temperature": temperature, "text": chunk, "error": str(e)}

async def select_best_version(request: Request, original_chunk: str, generated_versions: List[dict], model: str, language_level: str, preserved_words: List[str], user: Any, index: int) -> dict:
    successful_versions = [v for v in generated_versions if v.get("error") is None and v.get("text", "").strip()]
    if not successful_versions:
        logger.warning(f"No successful versions generated for chunk {index}. Returning original chunk.")
        return {"index": index, "text": original_chunk, "selection_error": "No successful versions to select from."}
    system_prompt = get_prompts(language_level, preserved_words, step="selection")
    variants_text = ""
    for i, version_data in enumerate(successful_versions):
        variant_text = version_data.get('text', '')
        variant_text = variant_text.replace('<<<', '').replace('>>>', '').strip()
        variants_text += f"Variant {i+1} (gegenereerd met temperature={version_data['temperature']}):\n{variant_text}\n---\n"
    selection_user_content = f"""Originele Paragraaf:
---
{original_chunk}
---
Gegenereerde Varianten:
{variants_text}
Kies de beste of combineer tot de definitieve versie tussen <<< en >>>. De lijst behouden woorden mocht niet gewijzigd worden: {', '.join(preserved_words) or 'geen'}."""
    form_data = {
        "model": model,
        "stream": False,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": selection_user_content}
        ]
    }
    try:
        response = await generate_chat_completion(request=request, form_data=form_data, user=user)
        llm_output = response['choices'][0]['message']['content']
        final_text = clean_llm_output(llm_output)
        return {"index": index, "text": final_text}
    except Exception as e:
        logger.error(f"Error during selection step for chunk {index} with model {model}: {e}")
        return {"index": index, "text": original_chunk, "selection_error": str(e)}

# ------ API Inputvalidatie ------

class SimplifyTextRequest(BaseModel):
    text: constr(min_length=1, max_length=MAX_TEXT_LENGTH)
    model: constr(strip_whitespace=True, min_length=2, max_length=32)
    preserved_words: conlist(str, max_length=MAX_PRESERVED_WORDS) = []
    language_level: constr(strip_whitespace=True, to_upper=True, pattern="^(B1|B2)$") = DEFAULT_LANGUAGE_LEVEL

    @classmethod
    def validate_words(cls, preserved_words):
        for w in preserved_words:
            if len(w) > 50:
                raise ValueError(f"Preserved word '{w}' is te lang (max 50 tekens)")
    def dict(self, **kwargs):
        data = super().dict(**kwargs)
        self.validate_words(data.get("preserved_words", []))
        return data

@router.post("/translate")
async def simplify_text_endpoint(request: Request, data: SimplifyTextRequest, user=Depends(get_current_user)):
    if len(data.preserved_words) > MAX_PRESERVED_WORDS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Maximaal {MAX_PRESERVED_WORDS} woorden toegestaan in preserved_words.")

    if len(data.text) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Input tekst is te lang (max {MAX_TEXT_LENGTH} tekens).")

    chunks = split_into_chunks(data.text)
    num_chunks = len(chunks)
    if num_chunks > MAX_CHUNKS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Tekst resulteert in te veel delen ({num_chunks} chunks, max {MAX_CHUNKS}). Verkort of vereenvoudig de tekst.")

    if num_chunks == 0:
        async def empty_stream():
            yield json.dumps({"total_chunks": 0}) + "\n"
            if False: yield None
        return StreamingResponse(empty_stream(), media_type="application/x-ndjson")

    async def stream_results():
        yield json.dumps({"total_chunks": num_chunks}) + "\n"
        generation_tasks = []
        for i, chunk in enumerate(chunks):
            for temp in TEMPERATURES:
                generation_tasks.append(
                    generate_version(request, chunk, data.model, data.preserved_words, data.language_level, user, i, temp)
                )
        chunk_results = {i: [] for i in range(num_chunks)}
        tasks_outstanding = {i: len(TEMPERATURES) for i in range(num_chunks)}
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
                logger.exception(f"Error in generation task: {e}")
                yield json.dumps({"error": f"Generation error: {str(e)}"}) + "\n"
        for future in asyncio.as_completed(selection_tasks):
            try:
                final_result = await future
                if 'text' in final_result and isinstance(final_result['text'], str):
                    final_result['text'] = final_result['text'].replace('<<<', '').replace('>>>', '').strip()
                yield json.dumps(final_result) + "\n"
            except Exception as e:
                logger.exception(f"Error in selection task: {e}")
                yield json.dumps({"error": f"Selection error: {str(e)}"}) + "\n"
    return StreamingResponse(stream_results(), media_type="application/x-ndjson")