"""TTS — gera narração via OpenAI TTS API.

Inline, sem serviço separado. Retorna path do arquivo MP3.
"""

import os
from pathlib import Path
from openai import OpenAI

from app.config import settings

OUTPUT_BASE = Path("/output")


def generate_voiceover(
    text: str,
    week: str,
    product_id: int,
    voice: str | None = None,
) -> dict:
    """Gera áudio de narração via OpenAI TTS.

    Returns:
        {"audio_path": str, "characters": int, "cost": float}
    """
    if not text.strip():
        return {"audio_path": None, "characters": 0, "cost": 0}

    output_dir = OUTPUT_BASE / week / str(product_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "voiceover.mp3")

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.audio.speech.create(
        model=settings.openai_tts_model,
        voice=voice or settings.openai_tts_voice,
        input=text,
    )
    response.stream_to_file(output_path)

    characters = len(text)
    cost = characters * 0.000015  # ~$15/1M chars

    return {
        "audio_path": output_path,
        "characters": characters,
        "cost": cost,
    }
