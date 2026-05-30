from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM (OpenAI)
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    # TTS (OpenAI)
    openai_tts_model: str = "tts-1"
    openai_tts_voice: str = "nova"

    # Vídeo
    video_width: int = 1080
    video_height: int = 1920
    video_fps: int = 30
    video_duration_seconds: int = 30

    # Banco
    database_url: str = "postgresql://avf:avf@postgres:5432/avf"

    # Scoring weights (TikTok Shop)
    weight_pain: float = 0.20
    weight_visual: float = 0.25
    weight_demo: float = 0.20
    weight_impulse: float = 0.15
    weight_trend: float = 0.10
    weight_availability: float = 0.05
    weight_commission: float = 0.05
    weight_competition: float = 0.05

    # Geral
    default_language: str = "es-ES"

    # TikTok Developer API
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""

    # Serper.dev (Google Search API — imagens)
    serper_api_key: str = ""

    # Seedance (Volcengine Ark — AI video generation)
    seedance_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
