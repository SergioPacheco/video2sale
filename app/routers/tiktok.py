"""TikTok Integration — OAuth2 Login Kit + Content Posting API."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models import Integration, Product
from app.config import settings
from app.agents.product_ranker import calculate_score

router = APIRouter(prefix="/tiktok", tags=["tiktok"])

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_API = "https://open.tiktokapis.com/v2"
REDIRECT_URI = "http://localhost:8090/tiktok/callback"


@router.get("/login")
async def tiktok_login():
    """Redireciona para TikTok OAuth (Login Kit). Usuário autoriza a app."""
    params = {
        "client_key": settings.tiktok_client_key,
        "scope": "user.info.basic,video.upload",
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": "video2sale",
    }
    url = TIKTOK_AUTH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url)


@router.get("/callback")
async def tiktok_callback(code: str, state: str = "", db: Session = Depends(get_db)):
    """Callback do OAuth. Troca code por access_token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(TIKTOK_TOKEN_URL, data={
            "client_key": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)

    data = resp.json()
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {data}")

    # Salvar token
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    if integration:
        integration.access_token = access_token
        integration.refresh_token = data.get("refresh_token")
        integration.token_expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 86400))
        integration.status = "connected"
        integration.config = {"open_id": data.get("open_id", ""), "scope": data.get("scope", "")}
        db.commit()

    return {
        "status": "connected",
        "open_id": data.get("open_id"),
        "scope": data.get("scope"),
        "expires_in": data.get("expires_in"),
    }


@router.get("/status")
async def tiktok_status(db: Session = Depends(get_db)):
    """Verifica status da conexão TikTok."""
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    if not integration or not integration.access_token:
        return {"status": "disconnected", "login_url": "http://localhost:8090/tiktok/login"}

    expired = integration.token_expires_at and integration.token_expires_at < datetime.utcnow()
    return {
        "status": "expired" if expired else "connected",
        "open_id": integration.config.get("open_id", "") if integration.config else "",
        "scope": integration.config.get("scope", "") if integration.config else "",
        "login_url": "http://localhost:8090/tiktok/login" if expired else None,
    }


@router.post("/upload-video")
async def upload_video(video_id: int, db: Session = Depends(get_db)):
    """Upload de vídeo para TikTok como draft via Content Posting API."""
    from app.models import Video, VideoCreativePack, VideoEvent

    # Verificar token
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    if not integration or not integration.access_token:
        raise HTTPException(status_code=401, detail="TikTok não conectado. Acesse /tiktok/login primeiro.")

    if integration.token_expires_at and integration.token_expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token expirado. Reconecte via /tiktok/login")

    # Buscar vídeo
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video or not video.video_path:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado ou não renderizado")

    # Buscar caption
    caption = ""
    if video.selected_creative_pack_id:
        pack = db.query(VideoCreativePack).filter(VideoCreativePack.id == video.selected_creative_pack_id).first()
        if pack:
            caption = (pack.caption or "") + " " + " ".join(pack.hashtags or [])

    token = integration.access_token

    # Step 1: Iniciar upload (obter upload_url)
    async with httpx.AsyncClient() as client:
        # Query creator info para verificar permissões
        info_resp = await client.post(
            f"{TIKTOK_API}/post/publish/creator_info/query/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        if info_resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"TikTok creator info failed: {info_resp.text}")

        # Ler arquivo de vídeo
        video_path = video.video_path
        import os
        if not os.path.exists(video_path):
            # Tentar path dentro do container
            video_path = f"/output/{'/'.join(video.video_path.split('/')[-3:])}"
        
        file_size = os.path.getsize(video_path)

        # Step 2: Iniciar upload via push
        init_resp = await client.post(
            f"{TIKTOK_API}/post/publish/video/init/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "post_info": {
                    "title": caption[:150] if caption else "Video2Sale",
                    "privacy_level": "SELF_ONLY",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": file_size,
                    "total_chunk_count": 1,
                }
            },
            timeout=15,
        )

    if init_resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"TikTok init upload failed: {init_resp.text}")

    init_data = init_resp.json()
    publish_id = init_data.get("data", {}).get("publish_id", "")
    upload_url = init_data.get("data", {}).get("upload_url", "")

    if not upload_url:
        raise HTTPException(status_code=502, detail=f"No upload URL: {init_data}")

    # Step 3: Upload do arquivo
    async with httpx.AsyncClient() as client:
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        upload_resp = await client.put(
            upload_url,
            content=video_bytes,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            },
            timeout=120,
        )

    if upload_resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"Upload failed: {upload_resp.status_code}")

    # Registrar evento
    video.status = "published_draft"
    db.add(VideoEvent(video_id=video_id, event_type="tiktok_uploaded", actor="system",
                      details={"publish_id": publish_id, "privacy": "SELF_ONLY"}))
    db.commit()

    return {
        "status": "ok",
        "publish_id": publish_id,
        "message": "Vídeo enviado como draft para TikTok. Abra o app TikTok para publicar.",
    }
