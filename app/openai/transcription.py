"""Transcription Service — Transcrição de áudio com Whisper.

Usado para extrair texto de vídeos de referência.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from app.openai.client import OpenAIClient, get_openai_client


class TranscriptionResult:
    """Resultado de transcrição."""

    def __init__(
        self,
        text: str,
        language: str,
        duration_seconds: float,
        segments: list[dict] | None = None,
    ):
        self.text = text
        self.language = language
        self.duration_seconds = duration_seconds
        self.segments = segments or []

    def get_text_at_time(self, time_seconds: float) -> str | None:
        """Retorna texto no timestamp especificado."""
        for segment in self.segments:
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            if start <= time_seconds <= end:
                return segment.get("text", "")
        return None

    def get_segments_in_range(self, start: float, end: float) -> list[dict]:
        """Retorna segmentos em um intervalo de tempo."""
        return [
            s for s in self.segments
            if s.get("start", 0) < end and s.get("end", 0) > start
        ]


class TranscriptionService:
    """Serviço de transcrição de áudio."""

    def __init__(self, client: OpenAIClient | None = None):
        self.client = client or get_openai_client()

    async def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        response_format: Literal["json", "text", "srt", "vtt", "verbose_json"] = "verbose_json",
        prompt: str | None = None,
    ) -> TranscriptionResult:
        """Transcreve arquivo de áudio.

        Args:
            audio_path: Path do arquivo de áudio
            language: Código do idioma (ex: "es", "en") ou None para auto-detect
            response_format: Formato da resposta
            prompt: Prompt opcional para guiar transcrição

        Returns:
            TranscriptionResult com texto e segmentos
        """
        model = self.client.config.transcription_model

        with open(audio_path, "rb") as audio_file:
            kwargs = {
                "model": model,
                "file": audio_file,
                "response_format": response_format,
            }

            if language:
                kwargs["language"] = language

            if prompt:
                kwargs["prompt"] = prompt

            response = await self.client.async_client.audio.transcriptions.create(**kwargs)

        # Processar resposta baseado no formato
        if response_format == "verbose_json":
            text = response.text
            language_detected = response.language
            duration = response.duration
            segments = [
                {
                    "start": s.start,
                    "end": s.end,
                    "text": s.text,
                }
                for s in (response.segments or [])
            ]
        elif response_format == "json":
            text = response.text
            language_detected = language or "unknown"
            duration = 0
            segments = []
        else:
            text = response if isinstance(response, str) else str(response)
            language_detected = language or "unknown"
            duration = 0
            segments = []

        # Track usage
        self.client.tracker.record(
            model=model,
            operation="transcription",
            audio_seconds=duration,
        )

        return TranscriptionResult(
            text=text,
            language=language_detected,
            duration_seconds=duration,
            segments=segments,
        )

    async def transcribe_video_audio(
        self,
        video_path: str,
        output_audio_path: str | None = None,
        language: str | None = None,
    ) -> TranscriptionResult:
        """Transcreve áudio de um vídeo.

        Extrai áudio primeiro usando FFmpeg, depois transcreve.

        Args:
            video_path: Path do vídeo
            output_audio_path: Path para salvar áudio extraído (opcional)
            language: Idioma esperado

        Returns:
            TranscriptionResult
        """
        import subprocess
        import tempfile

        # Criar path temporário se não especificado
        if output_audio_path:
            audio_path = output_audio_path
            Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
        else:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            audio_path = tmp.name
            tmp.close()

        # Extrair áudio com FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",  # Sem vídeo
            "-acodec", "libmp3lame",
            "-q:a", "4",
            audio_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg falhou ao extrair áudio: {result.stderr}")

        # Transcrever
        transcription = await self.transcribe(
            audio_path=audio_path,
            language=language,
        )

        # Limpar temp se foi criado
        if not output_audio_path:
            Path(audio_path).unlink(missing_ok=True)

        return transcription

    async def extract_speech_structure(
        self,
        transcription: TranscriptionResult,
    ) -> dict:
        """Analisa estrutura da fala transcrita.

        Identifica:
        - Hook (primeiros segundos)
        - Pontos-chave
        - CTA
        - Ofertas/preços mencionados

        Args:
            transcription: Resultado da transcrição

        Returns:
            Dict com análise estruturada
        """
        from app.openai.structured import get_structured_service
        from pydantic import BaseModel, Field

        class SpeechStructure(BaseModel):
            hook_text: str = Field(description="Texto do hook (primeiros 2-3 segundos)")
            key_points: list[str] = Field(description="Pontos principais mencionados")
            product_mentions: list[str] = Field(description="Menções ao produto")
            price_mentions: list[str] = Field(description="Menções a preço/oferta")
            cta_text: str | None = Field(description="Call-to-action se houver")
            language: str = Field(description="Idioma detectado")
            tone: str = Field(description="Tom da fala (casual, urgente, informativo, etc)")

        service = get_structured_service()

        result = await service.generate(
            schema=SpeechStructure,
            system_prompt=(
                "Analise a transcrição de um vídeo de TikTok/redes sociais. "
                "Identifique os elementos estruturais da fala."
            ),
            user_prompt=f"Transcrição completa:\n{transcription.text}",
        )

        return result.model_dump()


# Singleton
_service: TranscriptionService | None = None


def get_transcription_service() -> TranscriptionService:
    """Retorna instância singleton do serviço."""
    global _service
    if _service is None:
        _service = TranscriptionService()
    return _service
