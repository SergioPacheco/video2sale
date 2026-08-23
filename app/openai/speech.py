"""Speech Service — Text-to-Speech com OpenAI.

Gera narrações naturais para vídeos de TikTok.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from app.openai.client import OpenAIClient, get_openai_client


# Vozes disponíveis
VOICES = {
    "alloy": "Neutro, versátil",
    "echo": "Masculino, grave",
    "fable": "Expressivo, narrativo",
    "onyx": "Masculino, profundo",
    "nova": "Feminino, jovem, natural",  # Recomendado para UGC
    "shimmer": "Feminino, suave",
}

# Configurações por estilo de vídeo
VOICE_PRESETS = {
    "ugc_female": {
        "voice": "nova",
        "speed": 1.1,  # Levemente mais rápido para TikTok
    },
    "ugc_male": {
        "voice": "echo",
        "speed": 1.1,
    },
    "professional": {
        "voice": "alloy",
        "speed": 1.0,
    },
    "storytelling": {
        "voice": "fable",
        "speed": 0.95,
    },
}


class SpeechService:
    """Serviço de Text-to-Speech para narrações."""

    def __init__(self, client: OpenAIClient | None = None):
        self.client = client or get_openai_client()

    async def generate(
        self,
        text: str,
        output_path: str,
        voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"] = "nova",
        model: Literal["tts-1", "tts-1-hd"] = "tts-1",
        speed: float = 1.0,
        response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3",
    ) -> dict:
        """Gera áudio de narração.

        Args:
            text: Texto para narrar
            output_path: Path para salvar o áudio
            voice: Voz a usar
            model: Modelo TTS
            speed: Velocidade (0.25 a 4.0)
            response_format: Formato do áudio

        Returns:
            Dict com path, duração e custo estimado
        """
        if not text.strip():
            return {
                "audio_path": None,
                "characters": 0,
                "cost": 0,
                "duration_seconds": 0,
            }

        # Criar diretório se necessário
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Gerar áudio
        response = await self.client.async_client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
            response_format=response_format,
        )

        # Salvar arquivo
        response.stream_to_file(output_path)

        # Calcular custo
        characters = len(text)
        cost = characters * 0.000015  # ~$15/1M chars para tts-1

        if model == "tts-1-hd":
            cost *= 2  # HD custa o dobro

        # Track usage
        self.client.tracker.record(
            model=model,
            operation="tts",
            audio_chars=characters,
        )

        # Estimar duração (aproximadamente 150 palavras/minuto)
        words = len(text.split())
        duration_seconds = (words / 150) * 60 / speed

        return {
            "audio_path": output_path,
            "characters": characters,
            "cost": cost,
            "duration_seconds": duration_seconds,
            "voice": voice,
            "model": model,
        }

    async def generate_with_preset(
        self,
        text: str,
        output_path: str,
        preset: str = "ugc_female",
        model: Literal["tts-1", "tts-1-hd"] = "tts-1",
    ) -> dict:
        """Gera áudio usando preset de voz.

        Args:
            text: Texto para narrar
            output_path: Path para salvar
            preset: Nome do preset (ugc_female, ugc_male, professional, storytelling)
            model: Modelo TTS
        """
        config = VOICE_PRESETS.get(preset, VOICE_PRESETS["ugc_female"])

        return await self.generate(
            text=text,
            output_path=output_path,
            voice=config["voice"],
            speed=config["speed"],
            model=model,
        )

    async def generate_tiktok_narration(
        self,
        scenes: list[dict],
        output_path: str,
        language: str = "pt-BR",
        voice: str = "nova",
    ) -> dict:
        """Gera narração completa para vídeo TikTok.

        Args:
            scenes: Lista de cenas com campo 'narration' ou 'voiceover'
            output_path: Path para salvar
            language: Idioma (para ajustes futuros)
            voice: Voz a usar

        Returns:
            Dict com path, custo e metadados
        """
        # Extrair texto de narração das cenas
        narration_parts = []

        for scene in scenes:
            text = scene.get("narration") or scene.get("voiceover") or ""
            if text.strip():
                narration_parts.append(text.strip())

        full_text = " ".join(narration_parts)

        if not full_text:
            return {
                "audio_path": None,
                "characters": 0,
                "cost": 0,
                "duration_seconds": 0,
                "scenes_with_audio": 0,
            }

        result = await self.generate(
            text=full_text,
            output_path=output_path,
            voice=voice,
            speed=1.1,  # Levemente mais rápido para TikTok
        )

        result["scenes_with_audio"] = len(narration_parts)
        result["full_text"] = full_text

        return result


# Singleton
_service: SpeechService | None = None


def get_speech_service() -> SpeechService:
    """Retorna instância singleton do serviço."""
    global _service
    if _service is None:
        _service = SpeechService()
    return _service
