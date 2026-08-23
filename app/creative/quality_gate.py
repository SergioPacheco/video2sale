"""Video Quality Gate — Validação técnica e criativa antes de publicação.

Duas camadas:
1. Technical QA — código/FFprobe (determinístico)
2. Creative QA — OpenAI (semântico)
"""

from __future__ import annotations

import subprocess
import json
from datetime import datetime
from pathlib import Path

from app.creative.schemas import (
    TechnicalQAResult,
    CreativeQAResult,
    VideoQualityResult,
    CreativePlan,
    ProductProfile,
)
from app.openai.client import get_openai_client
from app.openai.vision import get_vision_service
from app.openai.structured import get_structured_service


class VideoQualityGate:
    """Quality gate para vídeos antes de publicação."""

    # Thresholds técnicos
    VALID_CODECS = ["h264", "hevc", "vp9"]
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    TARGET_ASPECT = 9 / 16
    MIN_DURATION = 5
    MAX_DURATION = 60

    # Thresholds criativos
    MIN_OVERALL_SCORE = 80
    MIN_HOOK_SCORE = 80
    MIN_PRODUCT_FIDELITY = 90
    MIN_PRODUCT_VISIBILITY = 80

    def __init__(self):
        self.vision = get_vision_service()
        self.structured = get_structured_service()
        self.client = get_openai_client()

    async def validate(
        self,
        video_path: str,
        creative_plan: CreativePlan,
        product_profile: ProductProfile | None = None,
        original_product_image: str | None = None,
    ) -> VideoQualityResult:
        """Executa validação completa do vídeo.

        Args:
            video_path: Path do vídeo a validar
            creative_plan: CreativePlan usado na geração
            product_profile: ProductProfile opcional
            original_product_image: Imagem original para validar fidelidade

        Returns:
            VideoQualityResult com resultado completo
        """
        # 1. Validação técnica
        technical = self._validate_technical(video_path)

        # 2. Validação criativa
        creative = await self._validate_creative(
            video_path=video_path,
            creative_plan=creative_plan,
            product_profile=product_profile,
            original_product_image=original_product_image,
        )

        # 3. Determinar aprovação geral
        overall_approved = technical.passed and creative.approved

        # 4. Identificar componentes para regenerar
        components_to_regenerate = self._identify_regeneration_needs(
            technical, creative
        )

        return VideoQualityResult(
            video_id=creative_plan.id,
            creative_plan_id=creative_plan.id,
            technical=technical,
            creative=creative,
            overall_approved=overall_approved,
            can_publish=overall_approved,
            components_to_regenerate=components_to_regenerate,
            validated_at=datetime.utcnow(),
        )

    def _validate_technical(self, video_path: str) -> TechnicalQAResult:
        """Validação técnica com FFprobe."""
        issues = []

        # Verificar se arquivo existe
        if not Path(video_path).exists():
            return TechnicalQAResult(
                file_exists=False,
                codec_valid=False,
                resolution_valid=False,
                aspect_ratio_valid=False,
                duration_valid=False,
                has_audio=False,
                audio_normalized=False,
                no_black_frames=True,
                no_frozen_frames=True,
                file_not_corrupted=False,
                passed=False,
                issues=["Arquivo não encontrado"],
            )

        # Obter info do vídeo
        video_info = self._get_video_info(video_path)

        if not video_info:
            return TechnicalQAResult(
                file_exists=True,
                codec_valid=False,
                resolution_valid=False,
                aspect_ratio_valid=False,
                duration_valid=False,
                has_audio=False,
                audio_normalized=False,
                no_black_frames=True,
                no_frozen_frames=True,
                file_not_corrupted=False,
                passed=False,
                issues=["Não foi possível ler informações do vídeo"],
            )

        # Validar codec
        codec = video_info.get("codec_name", "").lower()
        codec_valid = codec in self.VALID_CODECS
        if not codec_valid:
            issues.append(f"Codec inválido: {codec}")

        # Validar resolução
        width = video_info.get("width", 0)
        height = video_info.get("height", 0)
        resolution_valid = width == self.TARGET_WIDTH and height == self.TARGET_HEIGHT
        if not resolution_valid:
            issues.append(f"Resolução incorreta: {width}x{height} (esperado {self.TARGET_WIDTH}x{self.TARGET_HEIGHT})")

        # Validar aspect ratio
        if height > 0:
            actual_aspect = width / height
            aspect_ratio_valid = abs(actual_aspect - self.TARGET_ASPECT) < 0.01
        else:
            aspect_ratio_valid = False
        if not aspect_ratio_valid:
            issues.append(f"Aspect ratio incorreto")

        # Validar duração
        duration = video_info.get("duration", 0)
        duration_valid = self.MIN_DURATION <= duration <= self.MAX_DURATION
        if not duration_valid:
            issues.append(f"Duração fora do range: {duration:.1f}s")

        # Verificar áudio
        has_audio = video_info.get("has_audio", False)
        if not has_audio:
            issues.append("Vídeo sem áudio")

        # Normalização de áudio (verificação simples)
        audio_normalized = has_audio  # Por ora, assumir normalizado se tem áudio

        # Frames pretos/congelados (verificação básica)
        no_black_frames = True  # TODO: implementar detecção
        no_frozen_frames = True  # TODO: implementar detecção

        # Determinar se passou
        passed = (
            codec_valid
            and resolution_valid
            and aspect_ratio_valid
            and duration_valid
            and has_audio
        )

        return TechnicalQAResult(
            file_exists=True,
            codec_valid=codec_valid,
            resolution_valid=resolution_valid,
            aspect_ratio_valid=aspect_ratio_valid,
            duration_valid=duration_valid,
            has_audio=has_audio,
            audio_normalized=audio_normalized,
            no_black_frames=no_black_frames,
            no_frozen_frames=no_frozen_frames,
            file_not_corrupted=True,
            passed=passed,
            issues=issues,
        )

    def _get_video_info(self, video_path: str) -> dict | None:
        """Obtém informações do vídeo via FFprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)

            # Extrair informações relevantes
            video_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                None,
            )

            audio_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "audio"),
                None,
            )

            format_info = data.get("format", {})

            return {
                "codec_name": video_stream.get("codec_name") if video_stream else "",
                "width": int(video_stream.get("width", 0)) if video_stream else 0,
                "height": int(video_stream.get("height", 0)) if video_stream else 0,
                "duration": float(format_info.get("duration", 0)),
                "has_audio": audio_stream is not None,
            }

        except Exception:
            return None

    async def _validate_creative(
        self,
        video_path: str,
        creative_plan: CreativePlan,
        product_profile: ProductProfile | None,
        original_product_image: str | None,
    ) -> CreativeQAResult:
        """Validação criativa com OpenAI Vision."""
        # Extrair frames representativos
        frames = self._extract_qa_frames(video_path)

        if not frames:
            return CreativeQAResult(
                overall=0,
                hook_score=0,
                clarity_score=0,
                product_visibility=0,
                demonstration_score=0,
                pacing_score=0,
                authenticity_score=0,
                cta_score=0,
                product_fidelity=0,
                reasons=["Não foi possível extrair frames do vídeo"],
                problems=["Falha na extração de frames"],
                suggested_fixes=["Verificar integridade do vídeo"],
                approved=False,
            )

        # Construir contexto
        plan_summary = f"""
PLANO CRIATIVO:
- Ângulo: {creative_plan.angle.value}
- Hook: {creative_plan.hook.text}
- Duração alvo: {creative_plan.target_duration_ms // 1000}s
- Narração: {creative_plan.full_narration[:200]}...
- CTA: {creative_plan.cta_text}
"""

        product_context = ""
        if product_profile:
            product_context = f"""
PRODUTO:
- Problemas que resolve: {', '.join(product_profile.problems[:3])}
- Benefícios: {', '.join(product_profile.functional_benefits[:3])}
- Características visuais: {product_profile.visual_characteristics.shape}, {', '.join(product_profile.visual_characteristics.colors)}
"""

        system_prompt = """Você é um especialista em qualidade de vídeos para TikTok Shop.

Avalie o vídeo em relação ao plano criativo e dê scores de 0-100 para cada dimensão.

CRITÉRIOS:
- HOOK (0-2s): Interrompe scroll? É específico, não genérico?
- CLARIDADE: A mensagem é clara?
- VISIBILIDADE DO PRODUTO: Produto aparece cedo e claramente?
- DEMONSTRAÇÃO: Mostra o produto em ação?
- PACING: Ritmo adequado para TikTok?
- AUTENTICIDADE: Parece UGC, não comercial de TV?
- CTA: Call-to-action claro e natural?
- FIDELIDADE: Produto está representado corretamente?

Seja rigoroso. Score 80+ significa que está BOM para publicar.
Score abaixo de 70 em qualquer dimensão é problema."""

        user_prompt = f"""Avalie este vídeo:

{plan_summary}
{product_context}

Os frames mostram momentos-chave do vídeo.
O primeiro frame é do hook (0-2s) - seja especialmente crítico com ele.

Analise cada dimensão e dê feedback específico."""

        result = await self.vision.analyze_structured(
            schema=CreativeQAResult,
            images=frames,
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        # Aplicar regras de aprovação
        result.approved = self._check_creative_approval(result)

        # Cleanup frames temp
        for f in frames:
            Path(f).unlink(missing_ok=True)

        return result

    def _extract_qa_frames(self, video_path: str, count: int = 6) -> list[str]:
        """Extrai frames para QA."""
        import tempfile

        tmp_dir = tempfile.mkdtemp(prefix="v2s_qa_")
        frames = []

        # Obter duração
        info = self._get_video_info(video_path)
        duration = info.get("duration", 30) if info else 30

        # Definir timestamps (hook + distribuídos)
        times = [
            0.5,           # Hook início
            1.5,           # Hook fim
            duration * 0.25,
            duration * 0.5,
            duration * 0.75,
            duration - 1,  # Final/CTA
        ]

        for i, t in enumerate(times[:count]):
            output = Path(tmp_dir) / f"qa_{i}.jpg"
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(max(0, t)),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                str(output),
            ]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0 and output.exists():
                frames.append(str(output))

        return frames

    def _check_creative_approval(self, result: CreativeQAResult) -> bool:
        """Verifica se scores criativos passam."""
        if result.overall < self.MIN_OVERALL_SCORE:
            return False

        if result.hook_score < self.MIN_HOOK_SCORE:
            return False

        if result.product_fidelity < self.MIN_PRODUCT_FIDELITY:
            return False

        if result.product_visibility < self.MIN_PRODUCT_VISIBILITY:
            return False

        return True

    def _identify_regeneration_needs(
        self,
        technical: TechnicalQAResult,
        creative: CreativeQAResult,
    ) -> list[str]:
        """Identifica quais componentes precisam ser regenerados."""
        components = []

        # Problemas técnicos geralmente requerem re-render completo
        if not technical.passed:
            components.append("full_render")
            return components

        # Problemas criativos podem ser corrigidos parcialmente
        if creative.hook_score < 70:
            components.append("hook")

        if creative.product_visibility < 70:
            components.append("product_scenes")

        if creative.demonstration_score < 70:
            components.append("demonstration")

        if creative.cta_score < 70:
            components.append("cta")

        if creative.product_fidelity < 80:
            components.append("product_assets")

        # Se muitos componentes, melhor refazer tudo
        if len(components) >= 3:
            return ["full_render"]

        return components

    async def quick_check(self, video_path: str) -> bool:
        """Verificação rápida só técnica.

        Args:
            video_path: Path do vídeo

        Returns:
            True se passa na validação técnica
        """
        result = self._validate_technical(video_path)
        return result.passed


# Singleton
_gate: VideoQualityGate | None = None


def get_quality_gate() -> VideoQualityGate:
    """Retorna instância singleton do quality gate."""
    global _gate
    if _gate is None:
        _gate = VideoQualityGate()
    return _gate
