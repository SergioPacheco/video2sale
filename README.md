# Video2Sale

Fábrica de conteúdo criativo para afiliados TikTok Shop. Automatiza a seleção de produtos vencedores, geração de roteiros, compliance, narração e prompts otimizados para ferramentas de vídeo (Seedance, Runway, Remotion, etc).

## Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Frontend   │────▶│ Creative API │────▶│  PostgreSQL  │
│  (Vue 3)    │     │  (FastAPI)   │     │             │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ OpenAI   │ │ TTS      │ │ Amazon   │
        │ (roteiro)│ │ (áudio)  │ │ PA-API   │
        └──────────┘ └──────────┘ └──────────┘
```

## Stack

| Serviço | Tecnologia | Porta | Status |
|---|---|---|---|
| Creative API | Python + FastAPI | :8000 | ✅ Implementado |
| TTS Service | OpenAI TTS | :8001 | ✅ Implementado |
| Banco | PostgreSQL 16 | :5433 | ✅ Configurado |
| Frontend | Vue 3 + PrimeVue + Tailwind | :3000 | 🔲 Fase 2 |
| Orquestração | n8n | :5678 | 🔲 Fase 3 |
| Remotion | Node + React | :8002 | 🔲 Fase 4 |

## Quick Start

```bash
# 1. Configurar
cp .env.example .env
# Editar .env com sua OPENAI_API_KEY

# 2. Subir
make up

# 3. Testar
make test

# 4. Acessar
# API docs: http://localhost:8000/docs
# n8n:      http://localhost:5678
```

## Comandos

```bash
make up        # Sobe todos os containers
make down      # Para tudo
make test      # Roda testes no container (PostgreSQL)
make logs      # Logs da creative-api
make rebuild   # Rebuild da creative-api
```

---

## Fases do Projeto

### Fase 1 — API de Conteúdo Criativo ✅

**Objetivo:** Backend funcional que gera pacotes criativos completos.

| Endpoint | Função | Status |
|---|---|---|
| `POST /products/import-csv` | Importa produtos de CSV | ✅ |
| `POST /products/search-amazon` | Busca na Amazon PA-API | ✅ (scaffold) |
| `GET /products` | Lista produtos com scores | ✅ |
| `GET /products/{id}` | Detalhe do produto | ✅ |
| `POST /weekly-winner` | Ranking + seleção do vencedor | ✅ |
| `POST /videos/{id}/generate-creative` | Gera 3 roteiros via OpenAI | ✅ |
| `POST /videos/{id}/compliance-check` | Valida roteiros | ✅ |
| `POST /videos/{id}/select-pack` | Humano escolhe roteiro | ✅ |
| `POST /videos/{id}/generate-tts` | Gera narração (OpenAI TTS) | ✅ |
| `POST /videos/{id}/generate-prompts` | Prompts para Seedance/Runway | ✅ |
| `GET /videos` | Lista vídeos com filtros | ✅ |
| `GET /videos/{id}` | Detalhe com packs e eventos | ✅ |

**Schema:** Normalizado com rastreabilidade (video_creative_packs, video_events).

**Testes:** Unitários (ranker) + integração (endpoints com PostgreSQL).

---

### Fase 2 — Frontend (interface humana) 🔲

**Objetivo:** Interface Vue para operar o pipeline com aprovação humana.

| Tarefa | Descrição |
|---|---|
| Scaffold Vue 3 + PrimeVue + Tailwind | Seguir layout do projeto de referência |
| Página: Produtos | Lista, importação CSV, scores editáveis |
| Página: Ranking | Visualizar scores, aprovar vencedor |
| Página: Pipeline | Roteiros gerados, compliance, seleção |
| Página: Output | Prompts + áudio para download |
| Dashboard | Métricas de custo e produção |

**Stack:** Vue 3, PrimeVue 4, Tailwind CSS 4, Pinia, Vue Router, Axios, Vite.

---

### Fase 3 — Automação (n8n) 🔲

**Objetivo:** Pipeline automatizado com trigger manual/cron.

| Tarefa | Descrição |
|---|---|
| Workflow `weekly-video-factory` | Conecta todos os endpoints em sequência |
| Trigger manual + cron semanal | Executa pipeline completo |
| Notificações | Avisa quando precisa de aprovação humana |
| Tratamento de erro | Registra falhas e para o pipeline |

---

### Fase 4 — Renderers (geração de vídeo) 🔲

**Objetivo:** Múltiplas opções de geração de vídeo, plugáveis.

| Renderer | Tipo | Descrição |
|---|---|---|
| Seedance | Principal | Gera prompt otimizado (tu renderiza manualmente) |
| Remotion | Local/gratuito | Templates de texto animado |
| Runway | API paga | Vídeo IA via API |
| Kling | API paga | Vídeo IA via API |
| Manual | Upload | Humano grava/edita e faz upload |

---

### Fase 5 — Amazon PA-API completa 🔲

**Objetivo:** Busca automática de produtos com assinatura AWS.

| Tarefa | Descrição |
|---|---|
| Implementar AWS Signature V4 | Autenticação na PA-API |
| Busca por keywords + categoria | Retorna 20-50 produtos |
| Enriquecimento via LLM | Estimar scores automaticamente |
| Agendamento | Buscar novos produtos semanalmente |

---

### Fase 6 — Métricas e Aprendizado 🔲

**Objetivo:** Feedback loop — saber o que vende e otimizar.

| Tarefa | Descrição |
|---|---|
| Registro de publicação | Marcar vídeo como publicado |
| Input de métricas | Views, cliques, vendas (manual) |
| Recalcular ranking | Usar dados reais no score |
| Relatórios | Custo por vídeo, ROI por produto |

---

## Estrutura do Projeto

```
video2sale/
├── docker-compose.yml
├── Makefile
├── .env / .env.example
├── init.sql                          ← Schema PostgreSQL v2
├── data/products.csv                 ← Produtos de exemplo
├── services/
│   ├── creative-api/                 ← FastAPI (Python)
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── models.py            ← SQLAlchemy models
│   │   │   ├── schemas.py           ← Pydantic schemas
│   │   │   ├── routers/
│   │   │   │   ├── products.py
│   │   │   │   └── videos.py
│   │   │   ├── agents/
│   │   │   │   ├── product_ranker.py
│   │   │   │   ├── script_agent.py
│   │   │   │   ├── compliance_agent.py
│   │   │   │   ├── visual_agent.py
│   │   │   │   └── amazon_search.py
│   │   │   └── prompts/
│   │   │       ├── script-agent.md
│   │   │       └── compliance-agent.md
│   │   └── tests/
│   ├── tts-service/                  ← OpenAI TTS
│   └── remotion-renderer/            ← Fase 4
├── n8n/workflows/                    ← Fase 3
├── output/                           ← Vídeos/áudios gerados
└── docs/
```

## Pipeline (fluxo com aprovação humana)

```
1. Importar produtos (CSV ou Amazon)
2. Sistema calcula ranking (score TikTok Shop)
3. 👤 Humano aprova produto vencedor
4. Sistema gera 3 variações de roteiro (OpenAI)
5. Sistema faz compliance check
6. 👤 Humano escolhe melhor roteiro
7. Sistema gera áudio (OpenAI TTS)
8. Sistema gera prompts para renderer escolhido
9. 👤 Humano gera vídeo (Seedance/Runway/manual)
10. 👤 Humano aprova vídeo final
11. Publicação manual no TikTok Shop
```

## Custo estimado

| Cenário | Custo/mês (900 vídeos) |
|---|---|
| OpenAI roteiro + compliance | ~€2.50 |
| OpenAI TTS (todos) | ~€9.50 |
| **Total Fase 1** | **~€12/mês** |

## Licença

Projeto pessoal — uso privado.
