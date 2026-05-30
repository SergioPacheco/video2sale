"""Renderer — gera vídeo MP4 para TikTok usando ffmpeg.

Ken Burns effect sobre imagens + texto animado + narração TTS + música de fundo.
Sem Remotion, sem Chromium, sem Node. Apenas ffmpeg.

Output: 1080x1920, 30fps, h264, 15-30s.
"""

import os
import subprocess
import shutil
import tempfile
from pathlib import Path
from dataclasses import dataclass

# Diretório de músicas de fundo
MUSIC_DIR = Path("/data/music")
OUTPUT_BASE = Path("/output")


@dataclass
class Scene:
    start: float
    end: float
    text: str
    voiceover: str
    visual: str
    image_path: str | None = None


@dataclass
class RenderResult:
    video_path: str
    thumbnail_path: str | None
    duration: float
    scenes_count: int


def _run(cmd: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Executa comando ffmpeg. Raise em caso de erro."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou: {result.stderr[:500]}")
    return result


def _get_duration(file_path: str) -> float:
    """Retorna duração de um arquivo de mídia em segundos."""
    result = subprocess.run(
        f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{file_path}"',
        shell=True, capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, TypeError):
        return 0.0


def _select_music() -> str | None:
    """Seleciona uma música de fundo aleatória do diretório."""
    if not MUSIC_DIR.exists():
        return None
    tracks = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    if not tracks:
        return None
    import random
    return str(random.choice(tracks))


def _escape_text(text: str) -> str:
    """Escapa texto para uso no filtro drawtext do ffmpeg."""
    # ffmpeg drawtext precisa escapar: ', :, \, [, ]
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\u2019")  # substituir por aspas tipográficas
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "%%")
    return text


def _render_scene_with_image(
    image_path: str,
    text: str,
    duration: float,
    output_path: str,
    effect: str = "zoom_in",
) -> None:
    """Renderiza 1 cena: imagem com Ken Burns + texto overlay."""

    # Ken Burns effects
    effects = {
        "zoom_in": "zoompan=z='1+0.001*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30",
        "zoom_out": "zoompan=z='1.2-0.001*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30",
        "pan_left": "zoompan=z='1.1':x='iw*0.1+on*0.5':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30",
        "pan_right": "zoompan=z='1.1':x='iw*0.3-on*0.3':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30",
        "pan_up": "zoompan=z='1.1':x='iw/2-(iw/zoom/2)':y='ih*0.3-on*0.3':d={frames}:s=1080x1920:fps=30",
    }

    frames = int(duration * 30)
    zoom_filter = effects.get(effect, effects["zoom_in"]).format(frames=frames)

    # Construir filtro
    escaped_text = _escape_text(text)
    filters = [
        f"scale=2160:3840,{zoom_filter}",  # Escalar para 2x e depois zoompan reduz para 1080x1920
        f"fade=t=in:d=0.3,fade=t=out:st={duration - 0.3}:d=0.3",  # Fade in/out
    ]

    # Adicionar texto se existir
    if text.strip():
        # Texto com borda preta para legibilidade
        text_filter = (
            f"drawtext=text='{escaped_text}'"
            f":fontsize=52:fontcolor=white:borderw=3:bordercolor=black"
            f":x=(w-text_w)/2:y=(h-text_h)*0.75"
            f":enable='between(t,0.3,{duration - 0.3})'"
            f":font='Noto Sans'"
        )
        filters.append(text_filter)

    filter_str = ",".join(filters)

    cmd = (
        f'ffmpeg -y -loop 1 -i "{image_path}" -t {duration} '
        f'-vf "{filter_str}" '
        f'-c:v libx264 -preset fast -pix_fmt yuv420p -r 30 '
        f'"{output_path}"'
    )
    _run(cmd)


def _render_scene_no_image(
    text: str,
    duration: float,
    output_path: str,
    scene_index: int = 0,
) -> None:
    """Renderiza 1 cena sem imagem: gradiente animado + texto."""
    escaped_text = _escape_text(text)

    # Paletas de gradiente para TikTok (vibrantes)
    gradients = [
        ("0x1a1a2e", "0xe94560"),  # azul escuro → vermelho
        ("0x0f3460", "0x533483"),  # azul → roxo
        ("0x16213e", "0x0f3460"),  # azul profundo
        ("0x1b1b2f", "0x162447"),  # escuro elegante
        ("0x2d132c", "0xee4540"),  # vinho → vermelho
    ]
    c1, c2 = gradients[scene_index % len(gradients)]

    text_filter = ""
    if text.strip():
        text_filter = (
            f",drawtext=text='{escaped_text}'"
            f":fontsize=58:fontcolor=white:borderw=4:bordercolor=black@0.8"
            f":x=(w-text_w)/2:y=(h-text_h)/2"
            f":enable='between(t,0.3,{duration - 0.3})'"
            f":font='Noto Sans Bold'"
        )

    # Gradiente vertical animado com lavfi
    cmd = (
        f'ffmpeg -y -f lavfi '
        f'-i "gradients=s=1080x1920:c0={c1}:c2={c2}:x0=0:y0=0:x1=0:y1=1920:speed=0.3:d={duration}:r=30" '
        f'-vf "format=yuv420p{text_filter}" '
        f'-c:v libx264 -preset fast -pix_fmt yuv420p '
        f'"{output_path}"'
    )
    _run(cmd)


def _download_image(url: str, dest_path: str) -> bool:
    """Baixa imagem de URL para path local. Usa cache em /data/shared/images/."""
    import hashlib

    # Cache: verificar se já existe
    cache_dir = Path("/data/shared/images")
    cache_dir.mkdir(parents=True, exist_ok=True)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    ext = ".jpg"
    if ".png" in url.lower():
        ext = ".png"
    elif ".webp" in url.lower():
        ext = ".webp"
    cache_path = cache_dir / f"{url_hash}{ext}"

    if cache_path.exists() and cache_path.stat().st_size > 0:
        shutil.copy2(str(cache_path), dest_path)
        return True

    import httpx
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
                # Salvar no cache
                shutil.copy2(dest_path, str(cache_path))
                return True
    except Exception as e:
        print(f"[DOWNLOAD] Failed {url}: {e}")
    return False


def render_video(
    scenes: list[dict],
    voiceover_path: str | None,
    image_urls: list[str],
    product_name: str,
    week: str,
    product_id: int,
) -> RenderResult:
    """Renderiza vídeo completo a partir de cenas + imagens + áudio.

    Args:
        scenes: Lista de dicts com {start, end, text, voiceover, visual}
        voiceover_path: Path do áudio TTS (ou None)
        image_urls: URLs das imagens do produto
        product_name: Nome do produto (para metadata)
        week: Semana (para organizar output)
        product_id: ID do produto

    Returns:
        RenderResult com paths do vídeo e thumbnail
    """
    # Criar diretório de output
    output_dir = OUTPUT_BASE / week / str(product_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Diretório temporário para cenas individuais
    tmp_dir = tempfile.mkdtemp(prefix="v2s_render_")

    try:
        # 1. Baixar imagens
        local_images = []
        assets_dir = os.path.join(tmp_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)

        for i, url in enumerate(image_urls):
            if not url:
                continue
            ext = ".jpg"
            if ".png" in url.lower():
                ext = ".png"
            elif ".webp" in url.lower():
                ext = ".webp"
            local_path = os.path.join(assets_dir, f"img_{i}{ext}")
            if _download_image(url, local_path):
                local_images.append(local_path)

        # 2. Renderizar cada cena
        scene_files = []
        effects_cycle = ["zoom_in", "zoom_out", "pan_left", "pan_right", "zoom_in", "pan_up"]

        for i, scene in enumerate(scenes):
            duration = scene.get("end", 5) - scene.get("start", 0)
            if duration <= 0:
                duration = 5
            text = scene.get("text", "")
            scene_path = os.path.join(tmp_dir, f"scene_{i:02d}.mp4")

            # Atribuir imagem à cena (round-robin)
            if local_images:
                img_idx = i % len(local_images)
                effect = effects_cycle[i % len(effects_cycle)]
                _render_scene_with_image(
                    image_path=local_images[img_idx],
                    text=text,
                    duration=duration,
                    output_path=scene_path,
                    effect=effect,
                )
            else:
                # Sem imagens: gradiente animado com texto
                _render_scene_no_image(
                    text=text,
                    duration=duration,
                    output_path=scene_path,
                    scene_index=i,
                )

            scene_files.append(scene_path)

        if not scene_files:
            raise RuntimeError("Nenhuma cena renderizada")

        # 3. Concatenar cenas com crossfade
        concat_file = os.path.join(tmp_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for sf in scene_files:
                f.write(f"file '{sf}'\n")

        raw_video = os.path.join(tmp_dir, "raw.mp4")
        _run(
            f'ffmpeg -y -f concat -safe 0 -i "{concat_file}" '
            f'-c:v libx264 -preset fast -pix_fmt yuv420p -r 30 "{raw_video}"'
        )

        # 4. Mixar áudio (voiceover + música de fundo)
        video_duration = _get_duration(raw_video)
        music_path = _select_music()

        final_video = str(output_dir / f"video_{product_id}_{os.getpid()}.mp4")

        if voiceover_path and os.path.exists(voiceover_path) and music_path:
            # Voiceover + música de fundo (volume baixo)
            _run(
                f'ffmpeg -y -i "{raw_video}" -i "{voiceover_path}" -i "{music_path}" '
                f'-filter_complex '
                f'"[1:a]volume=1.0[vo];[2:a]volume=0.12,afade=t=out:st={video_duration - 2}:d=2[bg];'
                f'[vo][bg]amix=inputs=2:duration=shortest[aout]" '
                f'-map 0:v -map "[aout]" -c:v copy -c:a aac -shortest "{final_video}"'
            )
        elif voiceover_path and os.path.exists(voiceover_path):
            # Só voiceover
            _run(
                f'ffmpeg -y -i "{raw_video}" -i "{voiceover_path}" '
                f'-c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "{final_video}"'
            )
        elif music_path:
            # Só música
            _run(
                f'ffmpeg -y -i "{raw_video}" -i "{music_path}" '
                f'-filter_complex "[1:a]volume=0.2,afade=t=out:st={video_duration - 2}:d=2[bg]" '
                f'-map 0:v -map "[bg]" -c:v copy -c:a aac -shortest "{final_video}"'
            )
        else:
            # Sem áudio
            shutil.copy2(raw_video, final_video)

        # 5. Gerar thumbnail (frame do segundo 1)
        thumbnail_path = str(output_dir / "thumbnail.png")
        try:
            _run(f'ffmpeg -y -i "{final_video}" -ss 1 -vframes 1 -q:v 2 "{thumbnail_path}"')
        except Exception:
            thumbnail_path = None

        return RenderResult(
            video_path=final_video,
            thumbnail_path=thumbnail_path,
            duration=_get_duration(final_video),
            scenes_count=len(scene_files),
        )

    finally:
        # Cleanup temp
        shutil.rmtree(tmp_dir, ignore_errors=True)
