from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    products, videos, prompts, stats, metrics, trending, pipeline,
    integrations, presets, projects, assets, renders, publications, tiktok, storyboard,
)

app = FastAPI(
    title="Video2Sale",
    version="1.0.0",
    description="Produto → Vídeo TikTok em 1 chamada",
)

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline.router)
app.include_router(products.router)
app.include_router(videos.router)
app.include_router(prompts.router)
app.include_router(stats.router)
app.include_router(metrics.router)
app.include_router(trending.router)
app.include_router(integrations.router)
app.include_router(presets.router)
app.include_router(projects.router)
app.include_router(assets.router)
app.include_router(renders.router)
app.include_router(publications.router)
app.include_router(tiktok.router)
app.include_router(storyboard.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "video2sale", "version": "1.0.0"}
