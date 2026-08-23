"""TikTok Integration — OAuth2 Login Kit + Content Posting API.

Fluxo:
1. GET /tiktok/login → Redireciona para OAuth TikTok
2. GET /tiktok/callback → Recebe code, troca por access_token
3. GET /tiktok/status → Verifica se está conectado
4. POST /tiktok/upload/{video_id} → Envia vídeo como draft
5. GET /tiktok/publish-status/{publish_id} → Verifica status do upload

Requisitos:
- TikTok Developer App com Login Kit + Content Posting API
- Variáveis: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET
"""

import os
import hashlib
import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models import Integration, Video, VideoCreativePack, VideoEvent
from app.config import settings

router = APIRouter(prefix="/tiktok", tags=["tiktok"])

# TikTok API URLs
TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_API = "https://open.tiktokapis.com/v2"

# Scopes necessários
SCOPES = "user.info.basic,video.upload,video.publish"


def get_redirect_uri() -> str:
    """Retorna a URI de callback baseada no ambiente."""
    # Em produção, usar URL configurada
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8090")
    return f"{base_url}/tiktok/callback"


def generate_code_verifier() -> str:
    """Gera code_verifier para PKCE (43-128 chars)."""
    return secrets.token_urlsafe(32)


def generate_code_challenge(verifier: str) -> str:
    """Gera code_challenge a partir do verifier (SHA256 + base64url)."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


# Cache temporário para PKCE (em produção usar Redis)
_pkce_cache: dict[str, str] = {}


# ============================================================
# OAUTH ENDPOINTS
# ============================================================


@router.get("/login")
async def tiktok_login(db: Session = Depends(get_db)):
    """Inicia fluxo OAuth com TikTok.
    
    Redireciona o usuário para a página de login do TikTok.
    Após autorização, TikTok redireciona para /tiktok/callback.
    """
    if not settings.tiktok_client_key:
        raise HTTPException(
            status_code=500, 
            detail="TikTok não configurado. Defina TIKTOK_CLIENT_KEY e TIKTOK_CLIENT_SECRET no .env"
        )
    
    # PKCE (mais seguro que client_secret)
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = secrets.token_urlsafe(16)
    
    # Guardar verifier para usar no callback
    _pkce_cache[state] = code_verifier
    
    params = {
        "client_key": settings.tiktok_client_key,
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": get_redirect_uri(),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    url = TIKTOK_AUTH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url)


@router.get("/callback")
async def tiktok_callback(
    code: str = Query(..., description="Authorization code do TikTok"),
    state: str = Query(..., description="State para validação CSRF"),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Callback do OAuth. Troca authorization code por access_token.
    
    O TikTok redireciona para cá após o usuário autorizar.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error} - {error_description}")
    
    # Recuperar code_verifier do PKCE
    code_verifier = _pkce_cache.pop(state, None)
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Invalid state. Tente fazer login novamente.")
    
    # Trocar code por token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TIKTOK_TOKEN_URL,
            data={
                "client_key": settings.tiktok_client_key,
                "client_secret": settings.tiktok_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": get_redirect_uri(),
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
    
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"TikTok token request failed: {resp.text}")
    
    data = resp.json()
    access_token = data.get("access_token")
    if not access_token:
        error_msg = data.get("error_description", data.get("error", "Unknown error"))
        raise HTTPException(status_code=400, detail=f"OAuth failed: {error_msg}")
    
    # Salvar ou atualizar integração
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    if not integration:
        integration = Integration(provider="tiktok")
        db.add(integration)
    
    integration.access_token = access_token
    integration.refresh_token = data.get("refresh_token")
    integration.token_expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 86400))
    integration.status = "connected"
    integration.config = {
        "open_id": data.get("open_id", ""),
        "scope": data.get("scope", ""),
    }
    integration.last_used_at = datetime.utcnow()
    db.commit()
    
    # Redirecionar para frontend com sucesso
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3090")
    return RedirectResponse(f"{frontend_url}/settings?tiktok=connected")


@router.post("/refresh")
async def refresh_token(db: Session = Depends(get_db)):
    """Renova o access_token usando refresh_token."""
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    if not integration or not integration.refresh_token:
        raise HTTPException(status_code=401, detail="Nenhum refresh_token disponível. Faça login novamente.")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TIKTOK_TOKEN_URL,
            data={
                "client_key": settings.tiktok_client_key,
                "client_secret": settings.tiktok_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": integration.refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
    
    if resp.status_code != 200:
        integration.status = "expired"
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh falhou. Faça login novamente.")
    
    data = resp.json()
    integration.access_token = data.get("access_token")
    integration.refresh_token = data.get("refresh_token", integration.refresh_token)
    integration.token_expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 86400))
    integration.status = "connected"
    integration.last_used_at = datetime.utcnow()
    db.commit()
    
    return {"status": "ok", "expires_in": data.get("expires_in")}


@router.get("/status")
async def tiktok_status(db: Session = Depends(get_db)):
    """Verifica status da conexão com TikTok."""
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    
    if not integration or not integration.access_token:
        return {
            "status": "disconnected",
            "message": "TikTok não conectado",
            "login_url": "/tiktok/login",
        }
    
    expired = integration.token_expires_at and integration.token_expires_at < datetime.utcnow()
    
    if expired:
        return {
            "status": "expired",
            "message": "Token expirado. Renove ou faça login novamente.",
            "login_url": "/tiktok/login",
            "can_refresh": bool(integration.refresh_token),
        }
    
    return {
        "status": "connected",
        "open_id": integration.config.get("open_id", "") if integration.config else "",
        "scope": integration.config.get("scope", "") if integration.config else "",
        "expires_at": integration.token_expires_at.isoformat() if integration.token_expires_at else None,
    }


@router.delete("/disconnect")
async def disconnect(db: Session = Depends(get_db)):
    """Desconecta integração TikTok (revoga tokens localmente)."""
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    if integration:
        integration.access_token = None
        integration.refresh_token = None
        integration.status = "disconnected"
        db.commit()
    return {"status": "disconnected"}


# ============================================================
# CONTENT POSTING API
# ============================================================


class UploadResponse(BaseModel):
    status: str
    publish_id: str
    message: str


async def get_valid_token(db: Session) -> str:
    """Obtém token válido, renovando se necessário."""
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    
    if not integration or not integration.access_token:
        raise HTTPException(status_code=401, detail="TikTok não conectado. Acesse /tiktok/login")
    
    # Se expirado, tentar refresh
    if integration.token_expires_at and integration.token_expires_at < datetime.utcnow():
        if integration.refresh_token:
            await refresh_token(db)
            db.refresh(integration)
        else:
            raise HTTPException(status_code=401, detail="Token expirado. Reconecte via /tiktok/login")
    
    return integration.access_token


@router.post("/upload/{video_id}", response_model=UploadResponse)
async def upload_video(video_id: int, db: Session = Depends(get_db)):
    """Envia vídeo para TikTok como draft (SELF_ONLY).
    
    O vídeo fica nos rascunhos do TikTok. O usuário precisa abrir o app
    para revisar e publicar manualmente.
    
    Fluxo:
    1. Verificar token
    2. Buscar vídeo e caption
    3. Iniciar upload (POST /post/publish/video/init/)
    4. Enviar bytes do vídeo (PUT upload_url)
    5. Registrar evento
    """
    token = await get_valid_token(db)
    
    # Buscar vídeo
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    
    if not video.video_path:
        raise HTTPException(status_code=400, detail="Vídeo ainda não foi renderizado")
    
    # Buscar caption do creative pack
    caption = ""
    if video.selected_creative_pack_id:
        pack = db.query(VideoCreativePack).filter(
            VideoCreativePack.id == video.selected_creative_pack_id
        ).first()
        if pack:
            caption = (pack.caption or "")
            if pack.hashtags:
                caption += " " + " ".join(pack.hashtags)
    
    # Encontrar arquivo de vídeo
    video_path = video.video_path
    if not os.path.exists(video_path):
        # Tentar path alternativo (dentro do container)
        alt_path = f"/output/{'/'.join(video.video_path.split('/')[-3:])}"
        if os.path.exists(alt_path):
            video_path = alt_path
        else:
            raise HTTPException(status_code=404, detail=f"Arquivo de vídeo não encontrado: {video_path}")
    
    file_size = os.path.getsize(video_path)
    
    # Limite TikTok: 4GB
    if file_size > 4 * 1024 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Vídeo muito grande (máximo 4GB)")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Verificar permissões do creator
        info_resp = await client.post(
            f"{TIKTOK_API}/post/publish/creator_info/query/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={},
            timeout=15,
        )
        
        if info_resp.status_code != 200:
            error_data = info_resp.json() if info_resp.text else {}
            raise HTTPException(
                status_code=502,
                detail=f"TikTok creator info failed: {error_data.get('error', {}).get('message', info_resp.text)}"
            )
        
        # Step 2: Iniciar upload
        init_resp = await client.post(
            f"{TIKTOK_API}/post/publish/video/init/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "post_info": {
                    "title": (caption[:150] if caption else "Video criado com Video2Sale"),
                    "privacy_level": "SELF_ONLY",  # Draft - só o usuário vê
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": file_size,  # Upload em um chunk só
                    "total_chunk_count": 1,
                }
            },
            timeout=30,
        )
        
        if init_resp.status_code != 200:
            error_data = init_resp.json() if init_resp.text else {}
            raise HTTPException(
                status_code=502,
                detail=f"TikTok init failed: {error_data.get('error', {}).get('message', init_resp.text)}"
            )
        
        init_data = init_resp.json()
        publish_id = init_data.get("data", {}).get("publish_id", "")
        upload_url = init_data.get("data", {}).get("upload_url", "")
        
        if not upload_url:
            raise HTTPException(status_code=502, detail=f"TikTok não retornou upload_url: {init_data}")
        
        # Step 3: Upload do arquivo
        with open(video_path, "rb") as f:
            video_bytes = f.read()
        
        upload_resp = await client.put(
            upload_url,
            content=video_bytes,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            },
            timeout=300,  # 5 min para uploads grandes
        )
        
        if upload_resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=502,
                detail=f"Upload falhou: {upload_resp.status_code} - {upload_resp.text}"
            )
    
    # Registrar evento e atualizar status
    video.status = "published_draft"
    db.add(VideoEvent(
        video_id=video_id,
        event_type="tiktok_uploaded",
        actor="system",
        details={
            "publish_id": publish_id,
            "privacy": "SELF_ONLY",
            "file_size": file_size,
        }
    ))
    
    # Atualizar last_used da integração
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    if integration:
        integration.last_used_at = datetime.utcnow()
    
    db.commit()
    
    return UploadResponse(
        status="ok",
        publish_id=publish_id,
        message="Vídeo enviado como rascunho para TikTok. Abra o app TikTok para revisar e publicar.",
    )


@router.get("/publish-status/{publish_id}")
async def check_publish_status(publish_id: str, db: Session = Depends(get_db)):
    """Verifica status de publicação de um vídeo.
    
    Status possíveis:
    - PROCESSING_UPLOAD: Upload em andamento
    - PROCESSING_DOWNLOAD: TikTok baixando
    - SEND_TO_USER_INBOX: Disponível nos rascunhos
    - PUBLISH_COMPLETE: Publicado
    - FAILED: Falhou
    """
    token = await get_valid_token(db)
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TIKTOK_API}/post/publish/status/fetch/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"publish_id": publish_id},
            timeout=15,
        )
    
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Status check failed: {resp.text}")
    
    data = resp.json()
    status = data.get("data", {}).get("status", "UNKNOWN")
    
    return {
        "publish_id": publish_id,
        "status": status,
        "fail_reason": data.get("data", {}).get("fail_reason"),
        "publicaly_available_post_id": data.get("data", {}).get("publicaly_available_post_id"),
    }
