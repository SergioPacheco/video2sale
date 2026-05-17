"""Script Agent — gera 3 variações de pacote criativo via OpenAI."""

import json
from pathlib import Path
from openai import AsyncOpenAI
from app.config import settings

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "script-agent.md"


def _get_client():
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=120)


async def generate_creative_packs(product, video, custom_prompt=None) -> list[dict]:
    """Gera 3 variações de roteiro para um produto."""
    if custom_prompt:
        # Substituir variáveis no template customizado
        system_prompt = custom_prompt.content.replace(
            "{{product_name}}", product.name
        ).replace(
            "{{category}}", product.category
        ).replace(
            "{{audience}}", "Personas en España que buscan soluciones prácticas"
        ).replace(
            "{{pain}}", "Problema que resuelve este producto en el día a día"
        ).replace(
            "{{allowed_claims}}", "Solo los que se pueden demostrar visualmente"
        ).replace(
            "{{restrictions}}", "No inventar características, no prometer resultados imposibles"
        )
    else:
        system_prompt = PROMPT_PATH.read_text()

    user_prompt = (
        f"Producto: {product.name}\n"
        f"Categoría: {product.category}\n"
        f"Público: Personas en España que buscan soluciones prácticas\n"
        f"Dolor principal: Problema que resuelve este producto en el día a día\n"
        f"Beneficios permitidos: Solo los que se pueden demostrar visualmente\n"
        f"Restricciones: No inventar características, no prometer resultados imposibles\n\n"
        f"Genera 3 variaciones diferentes del paquete creativo.\n"
        f"Devuelve JSON con esta estructura exacta:\n"
        f'{{"packs": [{{"hook": "texto del gancho", "scenes": [{{"start": 0, "end": 3, "text": "texto en pantalla", "voiceover": "narración", "visual": "descripción visual"}}], "caption": "texto para redes", "hashtags": ["tag1"], "affiliate_disclaimer": "aviso"}}]}}'
    )

    response = await _get_client().chat.completions.create(
        model=settings.openai_model,
        temperature=0.7,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    # Log para debug
    print(f"[OPENAI] Raw response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
    print(f"[OPENAI] First item keys: {list(data[0].keys()) if isinstance(data, list) and data else list((data.get('packs') or data.get('variations') or [data])[0].keys()) if isinstance(data, dict) else 'N/A'}")

    # Normalizar: pode vir como {"packs": [...]} ou {"variations": [...]} ou [...]
    if isinstance(data, list):
        packs = data[:3]
    else:
        packs = data.get("packs") or data.get("variations") or data.get("creative_packs") or [data]
        packs = packs[:3]

    # Adicionar metadados de custo
    usage = response.usage
    cost_per_pack = (
        (usage.prompt_tokens * 0.0000004 + usage.completion_tokens * 0.0000016) / len(packs)
    )

    for pack in packs:
        # Normalizar scenes para sempre ser lista de dicts
        scenes = pack.get("scenes") or pack.get("escenas") or []
        normalized_scenes = []
        for j, scene in enumerate(scenes):
            if isinstance(scene, dict):
                normalized_scenes.append(scene)
            elif isinstance(scene, str):
                normalized_scenes.append({"start": j*5, "end": (j+1)*5, "text": "", "voiceover": scene, "visual": scene})
        pack["scenes"] = normalized_scenes
        pack["tokens_input"] = usage.prompt_tokens
        pack["tokens_output"] = usage.completion_tokens // len(packs)
        pack["cost"] = cost_per_pack

    return packs
