"""OpenAI Services.

Serviços estruturados para interagir com a plataforma OpenAI.
"""

from app.openai.client import OpenAIClient, get_openai_client
from app.openai.structured import StructuredResponseService
from app.openai.vision import VisionAnalysisService
from app.openai.image import ImageService
from app.openai.speech import SpeechService
from app.openai.transcription import TranscriptionService

__all__ = [
    "OpenAIClient",
    "get_openai_client",
    "StructuredResponseService",
    "VisionAnalysisService",
    "ImageService",
    "SpeechService",
    "TranscriptionService",
]
