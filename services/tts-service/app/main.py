import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="AVF TTS Service", version="0.1.0")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class TTSRequest(BaseModel):
    text: str
    language: str = "es-ES"
    voice: str | None = None
    output_dir: str = "/output"
    filename: str = "voiceover.mp3"


class TTSResponse(BaseModel):
    status: str
    audio_path: str
    characters: int


@app.get("/health")
def health():
    return {"status": "ok", "service": "tts-service", "provider": "openai"}


@app.post("/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """Gera áudio via OpenAI TTS API."""
    os.makedirs(request.output_dir, exist_ok=True)
    output_path = os.path.join(request.output_dir, request.filename)

    response = client.audio.speech.create(
        model=os.getenv("OPENAI_TTS_MODEL", "tts-1"),
        voice=request.voice or os.getenv("OPENAI_TTS_VOICE", "nova"),
        input=request.text,
    )
    response.stream_to_file(output_path)

    return TTSResponse(
        status="OK",
        audio_path=output_path,
        characters=len(request.text),
    )
