# Video2Sale

Produto → Vídeo TikTok em 1 clique. Pipeline automatizado para afiliados.

## O que faz

1. **Descobrir** produtos virais (catálogo, CSV, URL)
2. **Analisar** referências vencedoras (Creative DNA)
3. **Gerar** roteiro + narração + vídeo (GPT + TTS + FFmpeg)
4. **Validar** com Quality Gate antes de publicar
5. **Publicar** no TikTok (draft via API)

## Stack

| Componente | Tecnologia |
|---|---|
| API | Python + FastAPI |
| Frontend | Vue 3 + PrimeVue + Tailwind |
| Banco | PostgreSQL 16 |
| Render | FFmpeg (grátis) / Remotion (animações) |
| LLM | GPT-4o / GPT-4o-mini |
| TTS | OpenAI TTS-1 |
| Infra | Docker Compose |

## Setup

```bash
# 1. Clonar
git clone https://github.com/SergioPacheco/video2sale.git
cd video2sale

# 2. Configurar
cp .env.example .env
# Editar .env com sua OPENAI_API_KEY

# 3. Subir
make up

# 4. Acessar
# Frontend: http://localhost:3090
# API docs: http://localhost:8090/docs
```

## Portas

| Serviço | Porta |
|---|---|
| PostgreSQL | 5480 |
| API (FastAPI) | 8090 |
| Frontend (Vue) | 3090 |

## Uso Rápido

### Pipeline Novo (Creative Intelligence Engine)

```bash
# 1. Analisar produto
curl -X POST "http://localhost:8090/creative/analyze-product/1"

# 2. Gerar 5 planos criativos diferentes
curl -X POST "http://localhost:8090/creative/plan/1" \
  -H "Content-Type: application/json" \
  -d '{"count": 5}'

# 3. Gerar vídeo a partir de um plano
curl -X POST "http://localhost:8090/creative/generate" \
  -H "Content-Type: application/json" \
  -d '{"plan": {...}}'
```

### Pipeline Simplificado

```bash
# Gerar 1 vídeo (produto automático)
make generate

# Gerar com produto específico
curl -X POST "http://localhost:8090/pipeline/free?product_id=1&language=pt-BR"

# Health check
make health
```

## Idiomas suportados

- 🇧🇷 Português (pt-BR) — **padrão**
- 🇪🇸 Español (es-ES)
- 🇬🇧 English (en-US)
- 🇫🇷 Français (fr-FR)
- 🇩🇪 Deutsch (de-DE)

## API Endpoints (principais)

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/creative/analyze-product/{id}` | Analisa produto → ProductProfile |
| POST | `/creative/analyze-reference` | Analisa vídeo → CreativeDNA |
| POST | `/creative/plan/{id}` | Gera 5 CreativePlans diferentes |
| POST | `/creative/generate` | Gera vídeo a partir de plan |
| POST | `/pipeline/free` | Pipeline simplificado |
| GET | `/products/` | Listar produtos |
| POST | `/products/import-csv` | Importar CSV |
| GET | `/videos` | Listar vídeos |
| GET | `/videos/{id}` | Detalhe com roteiro |

Documentação completa: http://localhost:8090/docs

## Custo por vídeo

| Engine | Custo | Qualidade |
|---|---|---|
| FFmpeg | **~$0.01** (LLM + TTS) | Boa (Ken Burns + texto) |
| Remotion | **~$0.01** | Boa (animações) |
| Sora | ~$3/vídeo | Excelente (IA generativa) |

## Estrutura

```
video2sale/
├── app/                    # API FastAPI
│   ├── creative/           # Creative Intelligence Engine
│   │   ├── product_analyzer.py
│   │   ├── reference_analyzer.py
│   │   ├── planner.py
│   │   ├── fidelity_validator.py
│   │   └── quality_gate.py
│   ├── openai/             # Serviços OpenAI
│   │   ├── structured.py
│   │   ├── vision.py
│   │   ├── image.py
│   │   ├── speech.py
│   │   └── transcription.py
│   ├── routers/            # Endpoints
│   ├── renderer.py         # FFmpeg renderer
│   └── tts.py              # OpenAI TTS
├── frontend/               # Vue 3 + PrimeVue
├── services/
│   └── remotion-renderer/  # Remotion service
├── data/                   # Produtos, música, assets
├── output/                 # Vídeos gerados
├── .kiro/                  # Documentação do projeto
├── docker-compose.yml
└── init.sql                # Schema PostgreSQL
```

## Licença

MIT
