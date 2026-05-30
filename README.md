# Video2Sale

Producto → Vídeo TikTok en 1 clic. Pipeline automatizado para afiliados.

## Qué hace

1. **Descubrir** productos virales (catálogo, CSV, URL)
2. **Generar** roteiro + narración + vídeo (GPT + TTS + ffmpeg)
3. **Exportar** prompts para Seedance/Dreamina (gratis en el app)
4. **Publicar** en TikTok (draft via API)

## Stack

| Componente | Tecnología |
|---|---|
| API | Python + FastAPI |
| Frontend | Vue 3 + PrimeVue + Tailwind |
| Banco | PostgreSQL 16 |
| Render | ffmpeg (gratis) / Seedance 2.0 (pago) |
| LLM | GPT-4.1-mini (~$0.005/vídeo) |
| TTS | OpenAI TTS-1 (~$0.002/vídeo) |
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

## Uso rápido

```bash
# Gerar 1 vídeo (produto automático)
make generate

# Gerar com produto específico
curl -X POST "http://localhost:8090/pipeline/full?product_id=1&language=es-ES"

# Gerar storyboard para Seedance
curl -X POST "http://localhost:8090/storyboard/generate/1?style=product_showcase"

# Health check
make health
```

## Idiomas suportados

- 🇬🇧 English (en-US)
- 🇪🇸 Español (es-ES)
- 🇧🇷 Português (pt-BR)
- 🇫🇷 Français (fr-FR)
- 🇩🇪 Deutsch (de-DE)

## API Endpoints (principais)

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/pipeline/full` | Pipeline completo: produto → vídeo |
| POST | `/pipeline/batch` | Gerar N vídeos |
| POST | `/storyboard/generate/{id}` | Prompts para Seedance |
| GET | `/products/` | Listar produtos |
| POST | `/products/import-csv` | Importar CSV |
| POST | `/products/import-url` | Importar de URL |
| GET | `/videos` | Listar vídeos |
| GET | `/videos/{id}` | Detalhe com roteiro |
| GET | `/stats/` | KPIs do pipeline |

Documentação completa: http://localhost:8090/docs

## Custo por vídeo

| Engine | Custo | Qualidade |
|---|---|---|
| ffmpeg | **$0.007** (só LLM + TTS) | Boa (Ken Burns + texto) |
| Seedance | ~$3/vídeo | Excelente (IA generativa) |

## Estrutura

```
video2sale/
├── app/                    # API FastAPI
│   ├── agents/             # LLM agents (script, compliance, ranker)
│   ├── routers/            # 15 routers (45+ endpoints)
│   ├── renderer.py         # ffmpeg video renderer
│   ├── renderer_seedance.py # Seedance 2.0 API
│   └── tts.py              # OpenAI TTS
├── frontend/               # Vue 3 + PrimeVue
│   └── src/pages/          # 7 páginas
├── data/                   # Produtos, música, assets
├── output/                 # Vídeos gerados
├── docker-compose.yml
└── init.sql                # Schema PostgreSQL
```

## License

MIT
