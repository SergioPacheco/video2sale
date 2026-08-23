from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM (OpenAI)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # OpenAI Models - Centralizados para fácil troca
    openai_creative_model: str = "gpt-4o"        # Análise criativa, planejamento
    openai_premium_model: str = "gpt-4o"         # Tarefas complexas
    openai_fast_model: str = "gpt-4o-mini"       # Tarefas simples

    # OpenAI Image
    openai_image_model: str = "dall-e-3"         # Geração de imagem (ou gpt-image quando disponível)

    # OpenAI Video (quando disponível)
    openai_video_model: str = "sora"
    openai_video_premium_model: str = "sora"

    # OpenAI Audio
    openai_transcription_model: str = "whisper-1"

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

    # Scoring weights (TikTok Shop) - Legacy, será substituído por performance real
    weight_pain: float = 0.20
    weight_visual: float = 0.25
    weight_demo: float = 0.20
    weight_impulse: float = 0.15
    weight_trend: float = 0.10
    weight_availability: float = 0.05
    weight_commission: float = 0.05
    weight_competition: float = 0.05

    # Geral
    default_language: str = "pt-BR"

    # TikTok Developer API
    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""

    # Serper.dev (Google Search API — imagens)
    serper_api_key: str = ""

    # Creative Intelligence Engine
    creative_max_retries: int = 2
    creative_min_fidelity_score: int = 90
    creative_min_quality_score: int = 80

    class Config:
        env_file = ".env"


settings = Settings()
