from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import (
    products, videos, prompts, pipeline, assets, publications, tiktok,
)
from app.routers import creative

app = FastAPI(
    title="Video2Sale",
    version="2.0.0",
    description="Creative Intelligence Engine para TikTok Shop — Produto → Referências → Análise → Criativos → Vídeo",
)

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers existentes
app.include_router(pipeline.router)
app.include_router(products.router)
app.include_router(videos.router)
app.include_router(prompts.router)
app.include_router(assets.router)
app.include_router(publications.router)
app.include_router(tiktok.router)

# Novo Creative Intelligence Engine
app.include_router(creative.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "video2sale", "version": "2.0.0"}


# Servir vídeos/áudio/thumbnails gerados
app.mount("/output", StaticFiles(directory="/output"), name="output")
