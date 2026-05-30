"""Seedance Renderer — gera vídeo via Seedance 2.0 API (Volcengine Ark).

Async: submete task, poll até completar, download do MP4.
Custo: ~$0.93 por 5s 1080p, ~$1.97 por 15s.
"""

import os
import time
import httpx
from pathlib import Path
from dataclasses import dataclass

from app.config import settings

ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
OUTPUT_BASE = Path("/output")


@dataclass
class SeedanceResult:
    video_path: str
    duration: float
    scenes_count: int
    cost: float


async def render_with_seedance(
    scenes: list[dict],
    image_urls: list[str],
    product_name: str,
    week: str,
    product_id: int,
    duration: int = 5,
    resolution: str = "1080p",
) -> SeedanceResult:
    """Gera vídeo via Seedance 2.0 API.

    Para cada cena, gera um clip de ~5s e concatena com ffmpeg.
    """
    ark_api_key = settings.seedance_api_key
    if not ark_api_key:
        raise ValueError("SEEDANCE_API_KEY não configurado no .env")

    output_dir = OUTPUT_BASE / week / str(product_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    clips = []
    total_cost = 0

    # Gerar um clip por cena (max 3 para controlar custo)
    scenes_to_render = scenes[:3]

    for i, scene in enumerate(scenes_to_render):
        prompt = scene.get("visual", "") or scene.get("text", "")
        prompt += f". Vertical 9:16, product video, {product_name}, TikTok style, high quality."

        # Montar content array
        content = [{"type": "text", "text": prompt}]

        # Adicionar imagem de referência se disponível
        if i < len(image_urls) and image_urls[i]:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_urls[i]}
            })

        # Submeter task
        task_id = await _submit_task(ark_api_key, content, duration=duration, resolution=resolution)

        # Poll até completar
        result = await _poll_task(ark_api_key, task_id)

        if result["status"] != "succeeded":
            raise RuntimeError(f"Seedance task {task_id} failed: {result.get('status')}")

        # Download do clip
        video_url = result["video_url"]
        clip_path = str(output_dir / f"clip_{i}.mp4")
        await _download_video(video_url, clip_path)
        clips.append(clip_path)

        # Custo
        tokens = result.get("tokens", 103000)
        total_cost += tokens * 6.40 / 1_000_000

    # Concatenar clips com ffmpeg
    final_path = str(output_dir / f"video_seedance_{product_id}.mp4")

    if len(clips) == 1:
        os.rename(clips[0], final_path)
    else:
        _concat_clips(clips, final_path)

    # Calcular duração real
    actual_duration = duration * len(clips)

    return SeedanceResult(
        video_path=final_path,
        duration=actual_duration,
        scenes_count=len(clips),
        cost=total_cost,
    )


async def _submit_task(api_key: str, content: list, duration: int = 5, resolution: str = "1080p") -> str:
    """Submete task de geração de vídeo."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{ARK_BASE_URL}/contents/generations/tasks",
            json={
                "model": "doubao-seedance-2-0-260128",
                "content": content,
                "resolution": resolution,
                "ratio": "9:16",
                "duration": duration,
                "watermark": False,
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"Seedance submit failed: {resp.status_code} {resp.text}")

    data = resp.json()
    return data["id"]


async def _poll_task(api_key: str, task_id: str, max_wait: int = 300) -> dict:
    """Poll até task completar (max 5 min)."""
    wait = 10
    elapsed = 0

    async with httpx.AsyncClient() as client:
        while elapsed < max_wait:
            resp = await client.get(
                f"{ARK_BASE_URL}/contents/generations/tasks/{task_id}",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )

            data = resp.json()
            status = data.get("status", "")

            if status == "succeeded":
                return {
                    "status": "succeeded",
                    "video_url": data.get("content", {}).get("video_url", ""),
                    "tokens": data.get("usage", {}).get("completion_tokens", 0),
                }
            elif status in ("failed", "expired", "cancelled"):
                return {"status": status}

            await _async_sleep(wait)
            elapsed += wait
            wait = min(wait * 1.5, 60)

    return {"status": "timeout"}


async def _download_video(url: str, output_path: str):
    """Download do vídeo gerado (URL expira em 24h)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=60)
        with open(output_path, "wb") as f:
            f.write(resp.content)


def _concat_clips(clips: list[str], output_path: str):
    """Concatena clips com ffmpeg."""
    import subprocess
    import tempfile

    list_file = tempfile.mktemp(suffix=".txt")
    with open(list_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output_path
    ], check=True, capture_output=True)

    os.unlink(list_file)


async def _async_sleep(seconds):
    """Sleep assíncrono."""
    import asyncio
    await asyncio.sleep(seconds)
