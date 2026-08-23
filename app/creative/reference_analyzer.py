"""Competitor Video Analyzer — Extrai CreativeDNA de vídeos de referência.

Pipeline:
1. FFmpeg extrai frames e áudio
2. OpenAI Transcription processa áudio
3. OpenAI Vision analisa frames
4. Combina tudo em CreativeDNA estruturado
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal

from app.creative.schemas import (
    CreativeDNA,
    HookAnalysis,
    HookType,
    PacingLevel,
    ReferenceScene,
    ScenePurpose,
    WinningPatterns,
)
from app.openai.client import get_openai_client
from app.openai.transcription import get_transcription_service, TranscriptionResult
from app.openai.vision import get_vision_service
from app.openai.structured import get_structured_service


# Cache de análises
ANALYSIS_CACHE_DIR = Path("/data/cache/reference_analysis")
FRAMES_CACHE_DIR = Path("/data/cache/reference_frames")


class CompetitorVideoAnalyzer:
    """Analisa vídeos de referência para extrair CreativeDNA."""

    # Sampling de frames: mais denso no início (hook)
    DEFAULT_FRAME_TIMES = [
        0.0, 0.5, 1.0, 1.5, 2.0,  # Hook - cada 0.5s
        3.0, 4.0, 5.0,            # Desenvolvimento - cada 1s
        7.0, 9.0, 11.0,           # Meio - cada 2s
        13.0, 15.0,               # Final - cada 2s
    ]

    def __init__(self):
        self.transcription = get_transcription_service()
        self.vision = get_vision_service()
        self.structured = get_structured_service()
        self.client = get_openai_client()

        ANALYSIS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        FRAMES_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_video_hash(self, video_path: str) -> str:
        """Gera hash SHA-256 do vídeo para cache."""
        sha256 = hashlib.sha256()
        with open(video_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]

    def _check_cache(self, video_hash: str) -> CreativeDNA | None:
        """Verifica se análise está em cache."""
        cache_path = ANALYSIS_CACHE_DIR / f"{video_hash}.json"
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text())
                return CreativeDNA.model_validate(data)
            except Exception:
                pass
        return None

    def _save_cache(self, video_hash: str, dna: CreativeDNA) -> None:
        """Salva análise no cache."""
        cache_path = ANALYSIS_CACHE_DIR / f"{video_hash}.json"
        cache_path.write_text(dna.model_dump_json(indent=2))

    def _get_video_duration(self, video_path: str) -> float:
        """Obtém duração do vídeo em segundos."""
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                video_path,
            ],
            capture_output=True,
            text=True,
        )
        try:
            return float(result.stdout.strip())
        except (ValueError, TypeError):
            return 30.0  # Default

    def _extract_frames(
        self,
        video_path: str,
        output_dir: str,
        times: list[float] | None = None,
    ) -> list[str]:
        """Extrai frames do vídeo nos tempos especificados.

        Args:
            video_path: Path do vídeo
            output_dir: Diretório para salvar frames
            times: Lista de tempos em segundos (ou usa default)

        Returns:
            Lista de paths dos frames extraídos
        """
        times = times or self.DEFAULT_FRAME_TIMES
        duration = self._get_video_duration(video_path)

        # Filtrar tempos que excedem duração
        valid_times = [t for t in times if t < duration]

        # Garantir que pegamos frame do final
        if duration > 2 and (duration - 1) not in valid_times:
            valid_times.append(duration - 1)

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        frame_paths = []

        for i, t in enumerate(sorted(valid_times)):
            output_path = Path(output_dir) / f"frame_{i:02d}_{t:.1f}s.jpg"

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(t),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                str(output_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0 and output_path.exists():
                frame_paths.append(str(output_path))

        return frame_paths

    def _extract_audio(self, video_path: str, output_path: str) -> bool:
        """Extrai áudio do vídeo."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-q:a", "4",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0 and Path(output_path).exists()

    async def analyze(
        self,
        video_path: str,
        reference_id: str | None = None,
        source_url: str | None = None,
        language: str = "es",
        use_cache: bool = True,
    ) -> CreativeDNA:
        """Analisa vídeo de referência e extrai CreativeDNA.

        Args:
            video_path: Path do vídeo a analisar
            reference_id: ID opcional para identificação
            source_url: URL de origem se disponível
            language: Idioma esperado do áudio
            use_cache: Se deve usar cache

        Returns:
            CreativeDNA com análise completa
        """
        # Verificar cache
        video_hash = self._get_video_hash(video_path)

        if use_cache:
            cached = self._check_cache(video_hash)
            if cached:
                return cached

        # Criar diretório temporário para extração
        with tempfile.TemporaryDirectory(prefix="v2s_ref_") as tmp_dir:
            # 1. Extrair frames
            frame_paths = self._extract_frames(
                video_path=video_path,
                output_dir=f"{tmp_dir}/frames",
            )

            if not frame_paths:
                raise RuntimeError("Não foi possível extrair frames do vídeo")

            # 2. Extrair e transcrever áudio
            audio_path = f"{tmp_dir}/audio.mp3"
            transcript = None

            if self._extract_audio(video_path, audio_path):
                try:
                    transcript = await self.transcription.transcribe(
                        audio_path=audio_path,
                        language=language,
                    )
                except Exception as e:
                    print(f"[TRANSCRIPTION] Falhou: {e}")

            # 3. Analisar frames com Vision
            duration = self._get_video_duration(video_path)

            dna = await self._analyze_with_vision(
                frame_paths=frame_paths,
                transcript=transcript,
                duration=duration,
                reference_id=reference_id or video_hash,
                source_url=source_url,
            )

            # Salvar cache
            if use_cache:
                self._save_cache(video_hash, dna)

            return dna

    async def _analyze_with_vision(
        self,
        frame_paths: list[str],
        transcript: TranscriptionResult | None,
        duration: float,
        reference_id: str,
        source_url: str | None,
    ) -> CreativeDNA:
        """Analisa frames e transcrição para gerar CreativeDNA."""
        # Construir contexto
        transcript_text = transcript.text if transcript else "Áudio não disponível"
        transcript_language = transcript.language if transcript else "unknown"

        system_prompt = """Você é um especialista em análise de vídeos virais de TikTok.

Seu objetivo é descobrir POR QUE este vídeo funciona, não O QUE ele mostra.

Analise:
1. HOOK (0-2s): O que faz alguém parar de scrollar?
2. ESTRUTURA: Qual a sequência narrativa?
3. PACING: Qual o ritmo? Quantos cortes?
4. TÉCNICAS: Quais técnicas visuais são usadas?
5. EMOÇÃO: Quais gatilhos emocionais?
6. DEMONSTRAÇÃO: Como o produto é mostrado?
7. CTA: Como fecha a venda?

IMPORTANTE: Não queremos copiar o vídeo. Queremos aprender os PADRÕES que funcionam."""

        user_prompt = f"""Analise este vídeo de referência.

Duração total: {duration:.1f} segundos

Transcrição do áudio:
{transcript_text}

Os frames mostram momentos-chave do vídeo em ordem cronológica.
Os primeiros frames (0-2s) são do hook - analise-os com atenção especial.

Retorne um JSON com a estrutura CreativeDNA completa."""

        # Usar Vision para análise
        result = await self.vision.analyze_structured(
            schema=CreativeDNA,
            images=frame_paths,
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        # Preencher campos adicionais
        result.reference_id = reference_id
        result.source_url = source_url
        result.duration_seconds = duration
        result.transcript = transcript_text if transcript else None
        result.language = transcript_language
        result.analyzed_at = datetime.utcnow()
        result.model_used = self.client.config.creative_model

        return result

    async def analyze_multiple(
        self,
        video_paths: list[str],
        language: str = "es",
    ) -> tuple[list[CreativeDNA], WinningPatterns]:
        """Analisa múltiplos vídeos e extrai padrões vencedores.

        Args:
            video_paths: Lista de paths de vídeos
            language: Idioma esperado

        Returns:
            Tupla com lista de CreativeDNA e WinningPatterns consolidado
        """
        # Analisar cada vídeo
        dnas = []
        for i, path in enumerate(video_paths):
            try:
                dna = await self.analyze(
                    video_path=path,
                    reference_id=f"ref_{i}",
                    language=language,
                )
                dnas.append(dna)
            except Exception as e:
                print(f"[ANALYSIS] Vídeo {i} falhou: {e}")

        if not dnas:
            raise RuntimeError("Nenhum vídeo foi analisado com sucesso")

        # Extrair padrões
        patterns = await self._extract_patterns(dnas)

        return dnas, patterns

    async def _extract_patterns(self, dnas: list[CreativeDNA]) -> WinningPatterns:
        """Extrai padrões comuns de múltiplos CreativeDNAs."""
        # Preparar resumo dos DNAs
        dna_summaries = []
        for i, dna in enumerate(dnas):
            summary = {
                "ref": i,
                "duration": dna.duration_seconds,
                "hook_type": dna.hook.type.value,
                "hook_duration": dna.hook.duration_seconds,
                "structure": [s.value for s in dna.structure],
                "pacing": dna.pacing.value,
                "techniques": dna.techniques[:5],
                "reasons": dna.reasons_it_works[:3],
            }
            dna_summaries.append(summary)

        result = await self.structured.generate(
            schema=WinningPatterns,
            system_prompt="""Você é um analista de padrões em vídeos virais.

Analise os resumos de múltiplos vídeos de sucesso e identifique:
1. Padrões que aparecem em mais de um vídeo
2. Tipos de hook mais comuns
3. Estruturas narrativas recorrentes
4. Recomendações baseadas nos dados

Foque em padrões REPLICÁVEIS, não em conteúdo específico.""",
            user_prompt=f"""Analise estes {len(dnas)} vídeos de referência:

{json.dumps(dna_summaries, indent=2, ensure_ascii=False)}

Extraia os padrões vencedores comuns.""",
        )

        return result


# Singleton
_analyzer: CompetitorVideoAnalyzer | None = None


def get_competitor_analyzer() -> CompetitorVideoAnalyzer:
    """Retorna instância singleton do analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = CompetitorVideoAnalyzer()
    return _analyzer
