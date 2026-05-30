# MVP — Affiliate Video Factory Local

## Objetivo

Criar uma automação local em Docker para gerar vídeos de alta qualidade para afiliados, começando por produtos da Amazon Espanha.

O MVP deve permitir:

1. Importar uma lista de produtos candidatos.
2. Avaliar os produtos e escolher o **produto vencedor da semana**.
3. Gerar roteiro, gancho, CTA, legenda e prompts visuais.
4. Gerar narração com IA/TTS.
5. Montar vídeo vertical 9:16 em alta qualidade.
6. Salvar o vídeo final e os arquivos de apoio localmente.
7. Preparar a base para futura postagem automática em Instagram, TikTok e YouTube Shorts.

Neste MVP, o foco principal é:

> Gerar vídeos bons, de forma repetível, local, com Docker, a partir de produtos candidatos.

---

## Escopo do MVP

### Incluído

- Docker Compose local.
- n8n local como orquestrador.
- PostgreSQL para persistência inicial.
- API interna para ranking de produtos e geração criativa.
- Seleção do produto vencedor da semana.
- Geração de pacote criativo.
- Geração de narração.
- Renderização de vídeo vertical 9:16.
- Salvamento local dos vídeos e metadados.
- Workflow básico no n8n.

### Fora do escopo inicial

- Publicação automática.
- Scraping agressivo da Amazon.
- Dashboard web completo.
- Login de usuários.
- SaaS.
- TikTok API.
- Instagram API.
- YouTube API.
- Pagamento.
- Controle multiusuário.

---

## Visão geral da arquitetura

```text
Produtos CSV/JSON
   ↓
n8n local
   ↓
Creative API
   ↓
Product Ranker
   ↓
Script Agent
   ↓
Compliance Agent
   ↓
TTS Service
   ↓
Remotion Renderer
   ↓
Output local
```

---

## Stack sugerida

| Componente | Tecnologia |
|---|---|
| Orquestração | n8n |
| Banco | PostgreSQL |
| API interna | Python + FastAPI |
| Renderização | Remotion |
| Encoding | FFmpeg |
| Narração | OpenAI TTS, ElevenLabs ou serviço compatível |
| Armazenamento inicial | Volume local |
| Entrada de produtos | CSV/JSON |
| Saída | MP4 + Markdown + JSON |

---

## Estrutura de pastas

```text
affiliate-video-factory/
├── docker-compose.yml
├── .env
├── data/
│   ├── products.csv
│   ├── weekly-metrics.csv
│   └── winners/
├── output/
├── n8n/
│   └── workflows/
├── services/
│   ├── creative-api/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py
│   │       ├── agents/
│   │       │   ├── product_ranker.py
│   │       │   ├── script_agent.py
│   │       │   ├── compliance_agent.py
│   │       │   └── visual_agent.py
│   │       └── prompts/
│   │           ├── script-agent.md
│   │           ├── compliance-agent.md
│   │           └── visual-agent.md
│   ├── tts-service/
│   │   ├── Dockerfile
│   │   └── app/
│   └── remotion-renderer/
│       ├── Dockerfile
│       ├── package.json
│       ├── render.js
│       └── src/
│           ├── Video.tsx
│           ├── templates/
│           └── assets/
└── docs/
    ├── MVP.md
    └── product-scoring.md
```

---

## Docker Compose inicial

```yaml
services:
  postgres:
    image: postgres:16
    container_name: avf-postgres
    environment:
      POSTGRES_USER: avf
      POSTGRES_PASSWORD: avf
      POSTGRES_DB: avf
    ports:
      - "5433:5432"
    volumes:
      - ./docker-data/postgres:/var/lib/postgresql/data

  n8n:
    image: n8nio/n8n:latest
    container_name: avf-n8n
    ports:
      - "5678:5678"
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: avf
      DB_POSTGRESDB_USER: avf
      DB_POSTGRESDB_PASSWORD: avf
      N8N_SECURE_COOKIE: "false"
      GENERIC_TIMEZONE: Europe/Madrid
    volumes:
      - ./docker-data/n8n:/home/node/.n8n
      - ./data:/data
      - ./output:/output
    depends_on:
      - postgres

  creative-api:
    build: ./services/creative-api
    container_name: avf-creative-api
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/data
      - ./output:/output

  remotion-renderer:
    build: ./services/remotion-renderer
    container_name: avf-remotion-renderer
    env_file:
      - .env
    volumes:
      - ./data:/data
      - ./output:/output
    depends_on:
      - creative-api
```

---

## Arquivo `.env`

```env
OPENAI_API_KEY=coloque_sua_chave_aqui
TTS_PROVIDER=openai
DEFAULT_LANGUAGE=es-ES
DEFAULT_VIDEO_WIDTH=1080
DEFAULT_VIDEO_HEIGHT=1920
DEFAULT_VIDEO_FPS=30
DEFAULT_VIDEO_DURATION_SECONDS=25
```

---

## Comandos iniciais

```bash
docker compose up -d --build
```

Acessos locais:

```text
n8n: http://localhost:5678
creative-api: http://localhost:8000/docs
```

---

## Entrada de produtos

Arquivo: `data/products.csv`

```csv
id,name,category,amazon_url,price,commission_estimate,pain_score,visual_score,trend_score,competition_score,availability_score,notes
1,Organizador de cozinha,Casa,https://amazon.es/...,19.99,3,9,8,7,5,8,Produto bom para piso pequeno
2,Cortador de legumes,Cozinha,https://amazon.es/...,14.99,3,8,9,8,7,8,Visual forte para demonstração
3,Suporte notebook,Home office,https://amazon.es/...,24.99,3,7,7,6,6,9,Bom para remoto
```

---

## Critérios para escolher o produto vencedor da semana

O sistema deve calcular um score para cada produto.

### Fórmula inicial

```text
score =
  pain_score * 0.25
+ visual_score * 0.25
+ trend_score * 0.20
+ availability_score * 0.15
+ commission_estimate * 0.10
- competition_score * 0.05
```

### Critérios

| Critério | Peso | Motivo |
|---|---:|---|
| Dor clara | 25% | Produto vende melhor quando resolve problema real |
| Força visual | 25% | Vídeo curto precisa mostrar transformação |
| Tendência | 20% | Ajuda na distribuição e interesse |
| Disponibilidade | 15% | Evita divulgar produto indisponível |
| Comissão estimada | 10% | Importante, mas não deve ser o critério principal |
| Concorrência | -5% | Produto saturado exige maior diferenciação |

---

## Saída esperada do produto vencedor

```json
{
  "week": "2026-W21",
  "winner": {
    "id": "2",
    "name": "Cortador de legumes",
    "score": 8.15,
    "reason": "Alta força visual, dor clara e bom potencial para vídeos demonstrativos."
  }
}
```

---

## Endpoints da Creative API

### 1. Selecionar vencedor da semana

```http
POST /weekly-winner
```

Payload:

```json
{
  "week": "2026-W21",
  "source": "/data/products.csv"
}
```

Resposta:

```json
{
  "week": "2026-W21",
  "winner": {
    "id": "2",
    "name": "Cortador de legumes",
    "score": 8.15,
    "reason": "Alta força visual, dor clara e bom potencial para vídeos demonstrativos."
  }
}
```

---

### 2. Gerar pacote criativo

```http
POST /creative-pack
```

Payload:

```json
{
  "product_id": "2",
  "name": "Cortador de legumes",
  "category": "Cozinha",
  "pain": "Pessoa perde tempo cortando legumes no dia a dia",
  "audience": "Pessoas que moram em pisos pequenos na Espanha",
  "language": "es-ES"
}
```

Resposta esperada:

```json
{
  "hook": "¿Sigues cortando verduras así?",
  "script": "...",
  "scenes": [],
  "caption": "...",
  "hashtags": [],
  "affiliate_disclaimer": "Como afiliado de Amazon, puedo recibir una comisión por compras que cumplan los requisitos."
}
```

---

### 3. Gerar narração

```http
POST /tts/generate
```

Payload:

```json
{
  "text": "¿Sigues cortando verduras así? Si preparas comida todos los días...",
  "language": "es-ES",
  "voice": "female-natural"
}
```

Resposta:

```json
{
  "status": "OK",
  "audio_path": "/output/2026-W21/2/voiceover.mp3"
}
```

---

### 4. Renderizar vídeo

```http
POST /render-video
```

Payload:

```json
{
  "week": "2026-W21",
  "product_id": "2",
  "template": "premium-product-demo",
  "creative_pack_path": "/output/2026-W21/2/creative-pack.json",
  "voiceover_path": "/output/2026-W21/2/voiceover.mp3"
}
```

Resposta:

```json
{
  "status": "OK",
  "video_path": "/output/2026-W21/2/video-final.mp4",
  "thumbnail_path": "/output/2026-W21/2/thumbnail.png"
}
```

---

## Saída final do MVP

```text
output/
└── 2026-W21/
    └── 2-cortador-de-legumes/
        ├── creative-pack.json
        ├── roteiro.md
        ├── legenda.txt
        ├── voiceover.mp3
        ├── video-final.mp4
        ├── thumbnail.png
        ├── metadata.json
        └── relatorio.md
```

---

## Modelo de vídeo

### Especificações

| Item | Valor |
|---|---|
| Formato | Vertical 9:16 |
| Resolução | 1080x1920 |
| FPS | 30 |
| Duração | 20 a 30 segundos |
| Narração | Sim |
| Legenda | Sim |
| CTA | Sim |
| Aviso afiliado | Sim |
| Thumbnail | Sim |

### Estrutura narrativa

```text
0–2s      Gancho forte
2–5s      Dor visual
5–10s     Produto/solução
10–16s    Benefícios reais
16–22s    Situação de uso
22–27s    CTA + aviso de afiliado
```

---

## Template visual de alta qualidade

Elementos recomendados:

- Fundo limpo.
- Tipografia grande.
- Legenda em destaque.
- Cortes rápidos.
- Zoom leve.
- Barra de progresso.
- CTA final.
- Thumbnail gerada automaticamente.
- Transições suaves.
- Layout consistente para criar identidade visual.

---

## Exemplo de cenas

```json
[
  {
    "start": 0,
    "end": 2,
    "text": "¿Sigues cortando verduras así?",
    "voiceover": "¿Sigues cortando verduras así?",
    "visual": "Close rápido de legumes na bancada"
  },
  {
    "start": 2,
    "end": 6,
    "text": "Pierdes tiempo todos los días",
    "voiceover": "Pierdes tiempo todos los días preparando comida.",
    "visual": "Cozinha pequena, pessoa preparando legumes"
  },
  {
    "start": 6,
    "end": 12,
    "text": "Este cortador lo hace más fácil",
    "voiceover": "Este cortador ayuda a preparar verduras de forma más rápida y uniforme.",
    "visual": "Produto genérico em uso"
  },
  {
    "start": 12,
    "end": 20,
    "text": "Ideal para cocinar rápido en casa",
    "voiceover": "No hace magia, pero para el día a día puede venir muy bien.",
    "visual": "Resultado final organizado"
  },
  {
    "start": 20,
    "end": 25,
    "text": "Link en la bio",
    "voiceover": "Te dejo el enlace en la bio. Puedo recibir comisión como afiliado.",
    "visual": "Tela final com CTA"
  }
]
```

---

## Prompt do Script Agent

```text
Você é um estrategista de vídeos curtos para afiliados da Amazon Espanha.

Crie um pacote criativo para um vídeo vertical de 25 segundos.

Produto:
{{product_name}}

Categoria:
{{category}}

Público:
{{audience}}

Dor principal:
{{pain}}

Benefícios permitidos:
{{allowed_claims}}

Restrições:
{{restrictions}}

Idioma:
Espanhol da Espanha.

Regras:
- Gancho nos primeiros 2 segundos.
- Tom vendedor, rápido, natural e popular.
- Não inventar características.
- Não prometer resultado impossível.
- Não citar preço fixo.
- Não usar alegações médicas.
- Não usar "garantido", "milagroso", "o melhor".
- Incluir CTA para link na bio.
- Incluir aviso de afiliado.
- Dividir em cenas de 2 a 5 segundos.
- Gerar texto na tela para cada cena.
- Gerar narração curta para cada cena.
- Gerar descrição visual de cada cena.
- Gerar legenda para Instagram, TikTok e Shorts.

Retorne JSON válido.
```

---

## Prompt do Compliance Agent

```text
Revise o pacote criativo abaixo para conteúdo de afiliados.

Verifique:
1. Promessas exageradas.
2. Benefícios inventados.
3. Alegações médicas ou financeiras.
4. Preço fixo que pode mudar.
5. Falta de aviso de afiliado.
6. CTA enganoso.
7. Uso indevido de marca.

Se houver problema, corrija mantendo o estilo vendedor.

Retorne JSON:

{
  "status": "APROVADO|AJUSTAR|REPROVADO",
  "problems": [],
  "fixed_creative_pack": {}
}
```

---

## Workflow n8n do MVP

Nome sugerido:

```text
weekly-video-factory
```

Fluxo:

```text
Manual Trigger ou Cron semanal
   ↓
Ler /data/products.csv
   ↓
HTTP Request → creative-api /weekly-winner
   ↓
HTTP Request → creative-api /creative-pack
   ↓
HTTP Request → compliance-agent
   ↓
HTTP Request → tts-service /generate
   ↓
HTTP Request → remotion-renderer /render
   ↓
Salvar metadata em /output
   ↓
Finalizar com status OK
```

---

## Estados do produto/vídeo

```text
produto_importado
produto_avaliado
produto_vencedor
pacote_criativo_gerado
compliance_aprovado
audio_gerado
video_renderizado
video_pronto
erro
```

---

## Banco de dados inicial

### Tabela `products`

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    amazon_url TEXT,
    price NUMERIC(10,2),
    commission_estimate NUMERIC(5,2),
    pain_score INT,
    visual_score INT,
    trend_score INT,
    competition_score INT,
    availability_score INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Tabela `weekly_winners`

```sql
CREATE TABLE weekly_winners (
    id SERIAL PRIMARY KEY,
    week TEXT NOT NULL,
    product_id INT REFERENCES products(id),
    score NUMERIC(5,2),
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Tabela `videos`

```sql
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    week TEXT,
    script TEXT,
    caption TEXT,
    video_path TEXT,
    thumbnail_path TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Backlog técnico inicial

### Fase 1 — Estrutura local

- [ ] Criar repositório `affiliate-video-factory`.
- [ ] Criar `docker-compose.yml`.
- [ ] Subir PostgreSQL.
- [ ] Subir n8n.
- [ ] Criar volumes locais `data/` e `output/`.
- [ ] Criar `.env`.

### Fase 2 — Entrada de produtos

- [ ] Criar `data/products.csv`.
- [ ] Definir campos de scoring.
- [ ] Criar leitura do CSV na Creative API.
- [ ] Validar produtos obrigatórios.
- [ ] Criar endpoint `/weekly-winner`.

### Fase 3 — Seleção do vencedor

- [ ] Implementar fórmula de score.
- [ ] Ordenar produtos por score.
- [ ] Selecionar produto vencedor.
- [ ] Gerar justificativa do vencedor.
- [ ] Salvar resultado em JSON.

### Fase 4 — Pacote criativo

- [ ] Criar Script Agent.
- [ ] Criar Visual Agent.
- [ ] Criar Caption Agent.
- [ ] Criar Compliance Agent.
- [ ] Criar endpoint `/creative-pack`.
- [ ] Salvar `creative-pack.json`.
- [ ] Salvar `roteiro.md`.
- [ ] Salvar `legenda.txt`.

### Fase 5 — Narração

- [ ] Criar TTS Service.
- [ ] Receber texto da narração.
- [ ] Gerar `voiceover.mp3`.
- [ ] Salvar áudio no diretório do produto.
- [ ] Retornar caminho do áudio.

### Fase 6 — Renderização

- [ ] Criar projeto Remotion.
- [ ] Criar template `premium-product-demo`.
- [ ] Ler `creative-pack.json`.
- [ ] Ler `voiceover.mp3`.
- [ ] Renderizar vídeo 1080x1920.
- [ ] Exportar `video-final.mp4`.
- [ ] Gerar `thumbnail.png`.

### Fase 7 — Workflow n8n

- [ ] Criar workflow `weekly-video-factory`.
- [ ] Configurar Manual Trigger.
- [ ] Chamar `/weekly-winner`.
- [ ] Chamar `/creative-pack`.
- [ ] Chamar TTS.
- [ ] Chamar renderer.
- [ ] Registrar status final.
- [ ] Testar fluxo completo.

### Fase 8 — Qualidade

- [ ] Criar 3 variações de roteiro para o mesmo produto.
- [ ] Criar 3 estilos de thumbnail.
- [ ] Criar template com barra de progresso.
- [ ] Melhorar legenda na tela.
- [ ] Gerar relatório final do vídeo.
- [ ] Criar checklist visual.

---

## Roadmap pós-MVP

### Próxima versão

- Publicação automática no YouTube Shorts.
- Publicação automática no Instagram Reels.
- Publicação automática no TikTok.
- Coleta de métricas.
- Ranking com dados reais.
- Geração de múltiplas variações A/B.
- Dashboard de performance.
- Sistema de recomendação de novos produtos.

### Evolução para produto real

- Transformar em micro SaaS.
- Adicionar autenticação.
- Criar painel web.
- Permitir múltiplos nichos.
- Permitir múltiplas contas sociais.
- Criar templates visuais configuráveis.
- Criar biblioteca de ganchos vencedores.
- Criar sistema de aprendizado baseado em performance.

---

## Estratégia recomendada

A ordem mais segura é:

```text
1. Gerar vídeos localmente.
2. Melhorar qualidade visual.
3. Criar variações A/B.
4. Publicar manualmente.
5. Medir resultados.
6. Automatizar publicação.
7. Automatizar coleta de métricas.
8. Escalar produtos e nichos.
```

A primeira meta não é criar uma plataforma completa.

A primeira meta é criar uma máquina local que consiga responder:

> Este produto tem potencial?  
> Qual roteiro vende melhor?  
> Consigo gerar um vídeo bom em poucos minutos?  
> Consigo repetir isso toda semana?

---

## Critério de sucesso do MVP

O MVP está pronto quando for possível:

1. Rodar `docker compose up -d --build`.
2. Colocar 10 a 20 produtos em `products.csv`.
3. Executar o workflow no n8n.
4. Escolher automaticamente o produto vencedor.
5. Gerar pacote criativo.
6. Gerar narração.
7. Renderizar vídeo vertical 9:16.
8. Encontrar o MP4 final em `/output`.
9. Revisar o vídeo manualmente.
10. Publicar manualmente nas redes sociais.

---

## Nome sugerido do projeto

```text
Affiliate Video Factory
```

Outras opções:

```text
AI Affiliate Studio
Product Video Factory
Amazon Shorts Factory
Viral Product Studio
Content Ops Affiliate
```
