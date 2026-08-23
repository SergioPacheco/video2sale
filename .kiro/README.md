# Video2Sale - Creative Intelligence Engine

O objetivo deste repositório é aumentar o lucro com conteúdo de TikTok Shop
usando inteligência criativa baseada em OpenAI.

O aplicativo é uma ferramenta interna, local e single-user.
Não é um SaaS e não deve ser planejado como produto para terceiros.

## Objetivo Principal

**vendas / GMV / comissão gerada pelos vídeos**

## Core Loop

```
PRODUTO REAL
    ↓
REFERÊNCIAS VENCEDORAS
    ↓
CREATIVE DNA (por que funciona?)
    ↓
PRODUCT PROFILE (o que vender?)
    ↓
CREATIVE PLAN (como vender?)
    ↓
ASSETS + VERIFICAÇÃO DE FIDELIDADE
    ↓
RENDER + QUALITY GATE
    ↓
PUBLICAÇÃO
    ↓
MÉTRICAS
    ↓
PRÓXIMA GERAÇÃO
```

## Documentos ativos

- `steering/product-focus.md`: direção de produto e métricas
- `steering/creative-quality.md`: regras de qualidade criativa

## Novo Pipeline (v2.0)

### Endpoints do Creative Intelligence Engine

```bash
# 1. Analisar produto (gera ProductProfile)
curl -X POST "http://localhost:8090/creative/analyze-product/1"

# 2. Analisar referência vencedora (upload de vídeo)
curl -X POST "http://localhost:8090/creative/analyze-reference" \
  -F "video=@referencia.mp4" \
  -F "language=pt"

# 3. Gerar planos criativos (5 conceitos diferentes)
curl -X POST "http://localhost:8090/creative/plan/1" \
  -H "Content-Type: application/json" \
  -d '{"count": 5, "target_duration_ms": 16000}'

# 4. Gerar vídeo a partir de um plano
curl -X POST "http://localhost:8090/creative/generate" \
  -H "Content-Type: application/json" \
  -d '{"plan": {...}}'
```

### Pipeline antigo (ainda funciona)

```bash
# Gerar vídeo com fluxo simplificado
curl -X POST "http://localhost:8090/pipeline/free?product_id=1&language=pt-BR"
```

## Componentes do Creative Intelligence Engine

| Componente | Função |
|------------|--------|
| `ProductAnalyzer` | Analisa produto + fotos → ProductProfile |
| `CompetitorVideoAnalyzer` | Analisa vídeos vencedores → CreativeDNA |
| `CreativePlanner` | Combina produto + referências → CreativePlans |
| `ProductFidelityValidator` | Valida se imagem gerada preserva produto |
| `VideoQualityGate` | QA Técnico + QA Criativo antes de publicar |

## Serviços OpenAI

| Serviço | Uso |
|---------|-----|
| `StructuredResponseService` | Responses API com JSON Schema |
| `VisionAnalysisService` | Análise de imagens |
| `ImageService` | Geração com PRODUCT_IDENTITY_LOCK |
| `SpeechService` | TTS para narrações |
| `TranscriptionService` | Whisper para referências |

## Documentos legados

Os arquivos `mvp-affiliate-video-factory*.md` registram explorações anteriores.
Eles não definem mais o escopo atual e não devem ser usados para gerar backlog.

## Precedência

Em caso de conflito:

1. `steering/product-focus.md`
2. `steering/creative-quality.md`
3. código ativo
4. documentos legados
