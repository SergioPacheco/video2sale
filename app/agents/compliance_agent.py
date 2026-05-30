"""Compliance Agent — valida pacote criativo via OpenAI."""

import json
from pathlib import Path
from openai import AsyncOpenAI
from app.config import settings

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "compliance-agent.md"


def _get_client():
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=120)


async def check_compliance(pack, custom_prompt=None) -> dict:
    """Valida um creative pack contra regras de compliance."""
    if custom_prompt:
        system_prompt = custom_prompt.content
    else:
        system_prompt = PROMPT_PATH.read_text()

    user_prompt = json.dumps({
        "hook": pack.hook,
        "scenes": pack.script_json,
        "caption": pack.caption,
        "hashtags": pack.hashtags,
    }, ensure_ascii=False)

    response = await _get_client().chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    return {
        "status": data.get("status", "APROBADO"),
        "notes": "; ".join(data.get("problems", [])),
        "fixed_scenes": data.get("fixed_creative_pack", {}).get("scenes"),
    }
