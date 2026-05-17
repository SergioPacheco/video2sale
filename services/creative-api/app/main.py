from fastapi import FastAPI
from app.routers import products, videos

app = FastAPI(
    title="Video2Sale — Creative API",
    version="0.1.0",
    description="API para ranking de produtos, geração criativa e orquestração de vídeos",
)

app.include_router(products.router)
app.include_router(videos.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "creative-api", "version": "0.1.0"}
