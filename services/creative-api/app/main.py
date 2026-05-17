from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="Affiliate Video Factory - Creative API",
    version="0.1.0",
    description="API para ranking de produtos, geração criativa e orquestração de vídeos",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "creative-api"}


# --- Endpoints serão implementados aqui ---
# POST /products/import
# POST /weekly-winner
# POST /creative-pack
# POST /compliance-check
