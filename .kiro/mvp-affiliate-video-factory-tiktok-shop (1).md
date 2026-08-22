> **LEGADO - NÃO USAR COMO PLANO ATUAL.** Este documento registra uma exploração
> anterior. O direcionamento canônico está em `.kiro/README.md`, no steering
> `.kiro/steering/product-focus.md` e na spec
> `.kiro/specs/internal-profit-engine/`.

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

---

# Atualização — Estratégia específica para TikTok Shop

## Decisão de negócio

O MVP será direcionado para **TikTok Shop**, não apenas para afiliados genéricos.

Isso muda a prioridade do sistema:

1. O vídeo precisa parecer conteúdo nativo de TikTok.
2. O produto precisa ser demonstrável visualmente.
3. O CTA deve levar ao produto vinculado no TikTok Shop.
4. O sistema deve priorizar produtos com força visual, prova rápida e potencial de compra por impulso.
5. A automação deve evitar conteúdo repetitivo, enganoso ou não original.
6. A geração de vídeo por IA deve ser usada com cuidado, porque vídeos muito artificiais podem performar pior e elevar muito o custo.

---

## Premissa principal para TikTok Shop

Para TikTok Shop, o vídeo ideal não é um vídeo cinematográfico.

O melhor formato é:

```text
Produto real ou asset do produto
+
gancho forte
+
demonstração rápida
+
texto grande na tela
+
narração ou música
+
prova visual
+
CTA para produto no TikTok Shop
```

O sistema deve gerar vídeos com aparência de:

```text
review rápido
achadinho útil
teste de produto
antes/depois
problema e solução
demonstração prática
```

E não com aparência de:

```text
propaganda corporativa
vídeo institucional
vídeo 100% IA genérico
animação sem produto real
```

---

## Mudança na entrada dos produtos

Substituir a coluna `amazon_url` por uma entrada mais genérica:

```csv
id,name,category,source,product_url,shop_url,price,commission_estimate,pain_score,visual_score,trend_score,competition_score,availability_score,demo_score,impulse_buy_score,notes
```

Exemplo:

```csv
id,name,category,source,product_url,shop_url,price,commission_estimate,pain_score,visual_score,trend_score,competition_score,availability_score,demo_score,impulse_buy_score,notes
1,Cortador de legumes,Cozinha,TikTok Shop,https://...,https://...,14.99,3,8,9,8,7,8,10,8,Produto forte para demonstração
2,Organizador de cozinha,Casa,TikTok Shop,https://...,https://...,19.99,3,9,8,7,5,8,8,7,Bom para pisos pequenos
```

---

## Nova fórmula de scoring para TikTok Shop

A fórmula anterior continua útil, mas para TikTok Shop o peso visual deve ser maior.

```text
score =
  pain_score * 0.20
+ visual_score * 0.25
+ demo_score * 0.20
+ impulse_buy_score * 0.15
+ trend_score * 0.10
+ availability_score * 0.05
+ commission_estimate * 0.05
- competition_score * 0.05
```

### Explicação dos novos campos

| Campo | Peso | Motivo |
|---|---:|---|
| `visual_score` | 25% | TikTok vende pelo impacto visual rápido |
| `demo_score` | 20% | Produtos demonstráveis tendem a converter melhor |
| `pain_score` | 20% | A dor precisa ser entendida em poucos segundos |
| `impulse_buy_score` | 15% | TikTok Shop favorece compra por impulso |
| `trend_score` | 10% | Ajuda a surfar interesse atual |
| `availability_score` | 5% | Evita divulgar produto indisponível |
| `commission_estimate` | 5% | Importante, mas não deve mandar sozinho |
| `competition_score` | -5% | Produtos saturados exigem diferenciação |

---

## Templates locais específicos para TikTok Shop

O MVP deve começar com 5 templates locais.

### 1. Template — Problema → Solução

Uso:

```text
produtos de cozinha
organização
limpeza
home office
itens para casa pequena
```

Estrutura:

```text
0–3s      Gancho
3–7s      Problema
7–15s     Produto em destaque
15–24s    Benefício/demonstração
24–30s    CTA TikTok Shop
```

---

### 2. Template — Antes e Depois

Uso:

```text
limpeza
organização
beleza
cozinha
arrumação
```

Estrutura:

```text
0–2s      Antes impactante
2–8s      Problema visual
8–18s     Produto em uso
18–25s    Depois
25–30s    CTA
```

---

### 3. Template — Review honesto

Uso:

```text
produto útil
produto viral
achadinho
comparação rápida
```

Estrutura:

```text
0–3s      “Probé esto de TikTok Shop...”
3–10s     O que o produto promete
10–20s    Demonstração
20–26s    Veredito
26–30s    CTA
```

---

### 4. Template — 3 motivos

Uso:

```text
produtos com múltiplos benefícios
kits
organizadores
utensílios
```

Estrutura:

```text
0–3s      Gancho
3–9s      Motivo 1
9–15s     Motivo 2
15–22s    Motivo 3
22–30s    CTA
```

---

### 5. Template — Produto vencedor da semana

Uso:

```text
melhor produto da semana
produto com melhor score
produto com melhor performance
```

Estrutura:

```text
0–3s      “El producto ganador de la semana...”
3–8s      Dor principal
8–18s     Demonstração
18–24s    Por que venceu
24–30s    CTA TikTok Shop
```

---

## Como o vídeo será gerado no MVP

### Entrada

```json
{
  "product_name": "Cortador de legumes",
  "source": "TikTok Shop",
  "shop_url": "https://...",
  "category": "Cozinha",
  "audience": "pessoas que moram em pisos pequenos na Espanha",
  "pain": "perde tempo cortando legumes",
  "benefits": [
    "ajuda a preparar legumes mais rápido",
    "facilita o preparo diário",
    "produto visualmente demonstrável"
  ],
  "assets": [
    "/data/assets/cortador-01.jpg",
    "/data/assets/cortador-demo-01.mp4"
  ]
}
```

### Processo

```text
1. Product Ranker escolhe o produto vencedor.
2. Script Agent gera 3 roteiros.
3. Compliance Agent remove exageros e riscos.
4. Visual Agent escolhe template.
5. TTS Service gera narração ou marca o vídeo como “sem voz”.
6. Remotion monta o vídeo final.
7. FFmpeg exporta MP4 vertical 1080x1920.
8. Sistema salva thumbnail, legenda e metadata.
```

### Saída

```text
output/
└── tiktok-shop/
    └── 2026-W21/
        └── 001-cortador-de-legumes/
            ├── video-final.mp4
            ├── thumbnail.png
            ├── caption.txt
            ├── creative-pack.json
            ├── roteiro.md
            ├── metadata.json
            └── cost-estimate.json
```

---

# Estratégia de geração para 30 vídeos por dia

## Volume

```text
30 vídeos/dia
900 vídeos/mês
30 segundos por vídeo
27.000 segundos/mês de vídeo final
```

Gerar **27.000 segundos/mês inteiros com IA de vídeo paga** não é recomendado para o MVP.

A estratégia recomendada é:

```text
Vídeo final de 30s
=
25–30s montados localmente com Remotion/FFmpeg
+
0–5s opcionais de IA de vídeo apenas nos vídeos melhores
```

---

## Distribuição recomendada

```text
24 vídeos/dia — template local sem IA de vídeo
5 vídeos/dia — template local + 3 a 5 segundos de IA de vídeo
1 vídeo/dia — vídeo premium para produto vencedor
```

Em escala mensal:

```text
720 vídeos/mês — locais/baratos
150 vídeos/mês — com take curto de IA
30 vídeos/mês — premium
```

---

# Pesquisa de tecnologias e custos

> Observação: preços mudam com frequência. Estes valores devem ser tratados como referência operacional para o MVP e precisam ser revisados antes de contratação.

## 1. Orquestração

| Tecnologia | Uso no MVP | Grátis/trial | Pago? | Recomendação |
|---|---|---:|---:|---|
| n8n self-hosted | Orquestrar workflows locais | Sim | Cloud é pago | **Usar no MVP** |
| Make | Automação cloud | Trial/plano limitado | Sim | Evitar no início |
| Zapier | Automação cloud simples | Trial/plano limitado | Sim | Evitar no início |

### Decisão

Usar **n8n self-hosted em Docker**.

Custo esperado:

```text
€0/mês
```

---

## 2. Banco e armazenamento

| Tecnologia | Uso | Grátis/trial | Pago? | Recomendação |
|---|---|---:|---:|---|
| PostgreSQL | Banco local | Sim | Não | Usar |
| SQLite | MVP mínimo | Sim | Não | Alternativa simples |
| MinIO | Storage S3 local | Sim | Não | Opcional |
| Google Drive | Backup/manual | Plano grátis limitado | Pode pagar | Usar apenas se necessário |

### Decisão

Usar:

```text
PostgreSQL + volumes locais
```

Custo esperado:

```text
€0/mês
```

---

## 3. Renderização de vídeo local

| Tecnologia | Uso | Grátis/trial | Pago? | Recomendação |
|---|---|---:|---:|---|
| Remotion | Templates programáticos em React | Sim para indivíduo/pequena equipe | Pode exigir licença em empresa maior | **Usar** |
| FFmpeg | Encoding e conversão | Sim | Não | **Usar** |
| MoviePy | Render simples em Python | Sim | Não | Alternativa |
| Revideo | Vídeo programático | Sim/open-source dependendo do uso | Verificar licença | Alternativa |

### Decisão

Usar:

```text
Remotion + FFmpeg
```

Custo esperado no MVP:

```text
€0/mês
```

---

## 4. IA de texto para roteiro, legenda e compliance

| Tecnologia | Uso | Grátis/trial | Pago? | Recomendação |
|---|---|---:|---:|---|
| OpenAI API | Roteiro, compliance, prompts | Não é grátis ilimitado | Sim por uso | Usar com modelo barato |
| Gemini API | Roteiro e análise | Pode ter free tier | Sim por uso | Alternativa |
| Claude API | Roteiro/compliance | Pode ter trial/créditos | Sim por uso | Alternativa |
| Ollama local | Modelos locais | Sim | Não | Usar para reduzir custo |

### Decisão recomendada

Fase 1:

```text
Ollama local para rascunhos simples
OpenAI/Gemini para roteiro final e compliance
```

Fase 2:

```text
LLM pago apenas nos produtos vencedores ou nos vídeos premium
```

### Custo estimado

Para 900 vídeos/mês:

```text
€5 a €40/mês usando modelos baratos
€0 se usar apenas modelo local, com perda de qualidade/controle
```

---

## 5. Voz / Text-to-Speech

| Tecnologia | Uso | Grátis/trial | Pago? | Recomendação |
|---|---|---:|---:|---|
| Piper TTS | Voz local | Sim | Não | Melhor custo zero |
| Coqui TTS | Voz local | Sim | Não | Alternativa local |
| Edge TTS | Voz via vozes Microsoft | Gratuito/não oficial | Não direto | Bom para teste |
| OpenAI TTS | Voz por API | Não ilimitado | Sim | Boa qualidade/custo |
| ElevenLabs | Voz premium | Plano grátis/trial limitado | Sim | Usar só nos vencedores |
| TikTok voice | Voz nativa no app | Grátis no app | Sem automação local simples | Útil manualmente |

### Decisão recomendada

Fase 1:

```text
Piper TTS ou vídeo sem narração, com música + texto na tela
```

Fase 2:

```text
OpenAI TTS para vídeos comuns
ElevenLabs para vídeos vencedores/premium
```

### Estimativa para 900 vídeos/mês

Assumindo 30s por vídeo e narração média de 400–700 caracteres:

```text
900 vídeos × 400 caracteres = 360.000 caracteres/mês
900 vídeos × 700 caracteres = 630.000 caracteres/mês
```

Custo esperado:

```text
Piper/Coqui local: €0/mês
OpenAI TTS: baixo a médio, dependendo do modelo e caracteres
ElevenLabs: pode exigir plano pago se usar em todos
```

### Recomendação de custo

```text
80% dos vídeos: sem voz ou TTS local
15% dos vídeos: TTS pago barato
5% dos vídeos: voz premium
```

---

## 6. IA de imagem

| Tecnologia | Uso | Grátis/trial | Pago? | Recomendação |
|---|---|---:|---:|---|
| Stable Diffusion local | Imagens locais | Sim | Não | Melhor custo zero |
| Flux local | Imagens locais | Sim | Não | Boa qualidade, exige máquina |
| OpenAI Images | Imagens por API | Não ilimitado | Sim | Usar pontualmente |
| Ideogram | Texto/imagem | Trial/plano grátis limitado | Sim | Bom para thumbnails |
| Canva AI | Imagens/design | Plano grátis limitado | Sim | Útil manualmente |

### Decisão recomendada

```text
Usar imagens próprias ou assets do produto
Usar Stable Diffusion/Flux local para fundos genéricos
Usar API paga só para thumbnails/vídeos premium
```

Custo esperado:

```text
€0 a €30/mês
```

---

## 7. IA de vídeo paga

| Tecnologia | Uso | Grátis/trial | Pago? | Recomendação |
|---|---|---:|---:|---|
| Runway | Vídeo premium | Free limitado | Sim/créditos | Usar só em vencedores |
| Seedance | Takes curtos de vídeo | Trial/créditos dependendo do provedor | Sim/créditos por segundo | Boa opção para takes curtos |
| Google Veo | Vídeo premium | Acesso/trial variável | Sim | Usar só em premium |
| Luma Dream Machine | Vídeo criativo | Plano/free limitado | Sim | Usar pontualmente |
| Pika | Vídeos curtos/efeitos | Free limitado | Sim | Testes |
| Hailuo/MiniMax | Vídeos curtos | Trial/plano limitado | Sim | Testes |

### Decisão recomendada

Não usar IA de vídeo paga para todos os vídeos.

Usar apenas:

```text
3 a 5 segundos por vídeo nos melhores produtos
ou
vídeo premium para o produto vencedor da semana
```

### Estimativa de uso

Se usar 5 segundos de IA em 150 vídeos/mês:

```text
150 × 5s = 750 segundos/mês de IA de vídeo
```

Se usar IA nos 30 vídeos premium do mês com 8 segundos cada:

```text
30 × 8s = 240 segundos/mês de IA de vídeo
```

Total controlado:

```text
990 segundos/mês de IA de vídeo
```

Muito melhor do que:

```text
900 vídeos × 30s = 27.000 segundos/mês
```

---

## 8. IA de vídeo local/open-source

| Tecnologia | Uso | Grátis/trial | Pago? | Recomendação |
|---|---|---:|---:|---|
| Wan 2.1 | Geração local de vídeo | Sim | Não | Testar |
| CogVideoX | Geração local de vídeo | Sim | Não | Testar |
| AnimateDiff | Animação local | Sim | Não | Testar |
| ComfyUI | Pipeline visual local | Sim | Não | Bom para experimentação |

### Decisão recomendada

Adicionar como módulo opcional:

```text
local-video-ai-service
```

Fluxo:

```text
n8n
↓
creative-api
↓
local-video-ai-service
↓
Remotion
```

### Limitações

- Pode exigir GPU forte.
- Render pode ser lento.
- Qualidade pode variar.
- Nem sempre é adequado para produto real.
- Deve ser usado para fundos, takes genéricos ou cenas de apoio.

Custo esperado:

```text
€0 de API
custo real = hardware + energia + tempo
```

---

## 9. Publicação no TikTok Shop

### MVP

No MVP, a publicação continua manual.

Motivo:

```text
risco de erro
risco de violar política
necessidade de vincular produto corretamente
necessidade de revisar qualidade
```

### Pós-MVP

Adicionar publicação automática apenas depois de validar:

```text
produto
roteiro
criativo
compliance
qualidade
taxa de erro
```

---

# API grátis: o que realmente existe

## Grátis de verdade

| Parte | Existe grátis? | Serve para escala? |
|---|---:|---:|
| Docker | Sim | Sim |
| n8n self-hosted | Sim | Sim |
| PostgreSQL | Sim | Sim |
| Remotion | Sim no MVP | Sim |
| FFmpeg | Sim | Sim |
| Piper/Coqui TTS | Sim | Sim, se aceitar qualidade |
| Stable Diffusion/Flux local | Sim | Depende da máquina |
| Wan/CogVideo local | Sim | Depende da GPU |

## Grátis com limite/trial

| Parte | Existe grátis/trial? | Serve para 900 vídeos/mês? |
|---|---:|---:|
| Runway | Sim, limitado | Não |
| Pika | Sim, limitado | Não |
| Luma | Sim/limitado | Não |
| ElevenLabs | Sim/limitado | Não para todos |
| Canva AI | Sim/limitado | Não como motor automático |
| Veo/Gemini vídeo | Trial/acesso variável | Não como base barata |

## Pago por uso

| Parte | Pago por uso? | Recomenda usar? |
|---|---:|---:|
| OpenAI API texto | Sim | Sim, com modelos baratos |
| OpenAI TTS | Sim | Sim, se voz local não for suficiente |
| Seedance | Sim | Sim, só para takes curtos |
| Runway API | Sim | Só premium |
| Veo API | Sim | Só premium |
| ElevenLabs API | Sim | Só vencedores/premium |

---

# Estimativa de custo para 30 vídeos/dia no TikTok Shop

## Volume

```text
30 vídeos/dia
900 vídeos/mês
30 segundos por vídeo
```

---

## Cenário 1 — Quase gratuito

Composição:

```text
Remotion + FFmpeg
TTS local ou sem voz
assets próprios
sem IA de vídeo paga
LLM local/Ollama para roteiros simples
```

Custo:

```text
€0 a €20/mês
```

Custo por vídeo:

```text
€0,00 a €0,02
```

Risco:

```text
qualidade de voz menor
roteiros menos bons
mais trabalho de curadoria
```

---

## Cenário 2 — Recomendado para começar

Composição:

```text
Remotion + FFmpeg
OpenAI/Gemini para roteiro/compliance
TTS local ou OpenAI TTS barato
sem IA de vídeo em massa
poucas imagens IA
```

Custo:

```text
€50 a €150/mês
```

Custo por vídeo:

```text
€0,05 a €0,17
```

Este é o melhor ponto inicial.

---

## Cenário 3 — TikTok Shop com qualidade melhor

Composição:

```text
Remotion + FFmpeg
LLM pago para roteiro/compliance
OpenAI TTS ou ElevenLabs em parte dos vídeos
Seedance/Runway/Veo apenas em vídeos selecionados
thumbnails melhores
```

Custo:

```text
€150 a €400/mês
```

Custo por vídeo:

```text
€0,17 a €0,44
```

---

## Cenário 4 — Todos os vídeos com IA de vídeo paga

Composição:

```text
900 vídeos/mês
30s cada
27.000 segundos/mês gerados por IA de vídeo
```

Custo:

```text
€1.000 a €9.000+/mês
```

Custo por vídeo:

```text
€1,10 a €10+
```

Decisão:

```text
Não recomendado para MVP.
```

---

# Estratégia final de custo

## Prioridade 1 — Gratuito/local

Usar primeiro:

```text
Docker
n8n self-hosted
PostgreSQL
Remotion
FFmpeg
Piper/Coqui TTS
Stable Diffusion/Flux local
Ollama local
```

## Prioridade 2 — Pago barato

Usar quando melhorar qualidade:

```text
OpenAI/Gemini para roteiro
OpenAI TTS para voz
Seedance Lite/Fast só em takes curtos
```

## Prioridade 3 — Pago premium

Usar apenas nos vencedores:

```text
ElevenLabs
Runway
Veo
Luma
Pika
```

---

# Arquitetura final recomendada para TikTok Shop

```text
products.csv
   ↓
n8n
   ↓
Product Ranker TikTok Shop
   ↓
Script Agent
   ↓
Compliance Agent
   ↓
Template Selector
   ↓
TTS local ou pago
   ↓
Remotion Renderer
   ↓
Opcional: take curto com IA de vídeo
   ↓
FFmpeg
   ↓
video-final.mp4
   ↓
revisão manual
   ↓
upload manual no TikTok Shop
```

---

# Novo backlog específico para TikTok Shop

## Fase 1 — MVP local sem custo

- [ ] Ajustar `products.csv` para TikTok Shop.
- [ ] Criar campos `shop_url`, `source`, `demo_score`, `impulse_buy_score`.
- [ ] Alterar fórmula do Product Ranker.
- [ ] Criar 5 templates locais TikTok Shop.
- [ ] Criar render com Remotion e FFmpeg.
- [ ] Criar vídeos sem IA de vídeo paga.
- [ ] Usar TTS local ou vídeo sem voz.
- [ ] Exportar MP4 1080x1920.

## Fase 2 — Qualidade e variação

- [ ] Gerar 3 variações por produto.
- [ ] Criar thumbnails automáticas.
- [ ] Criar hooks diferentes.
- [ ] Criar relatório por vídeo.
- [ ] Criar controle de custo por vídeo.
- [ ] Criar template “Produto vencedor da semana”.

## Fase 3 — IA paga controlada

- [ ] Adicionar OpenAI/Gemini para roteiro final.
- [ ] Adicionar OpenAI TTS para voz comum.
- [ ] Adicionar ElevenLabs só para vídeos premium.
- [ ] Adicionar Seedance ou Runway apenas para 3–5 segundos.
- [ ] Calcular custo real por vídeo.

## Fase 4 — Pós-MVP

- [ ] Publicar manualmente no TikTok Shop.
- [ ] Coletar views, retenção, cliques e vendas manualmente.
- [ ] Atualizar `weekly-metrics.csv`.
- [ ] Recalcular ranking com dados reais.
- [ ] Só depois avaliar automação de postagem.

---

# Regra de ouro do MVP

```text
Não pagar para descobrir produto vencedor.
```

Primeiro:

```text
testar barato
publicar muito
medir
identificar vencedor
```

Depois:

```text
investir em vídeo premium
melhorar voz
gerar takes IA
escalar o que vende
```

---

# Resumo executivo

Para TikTok Shop, o MVP deve priorizar:

```text
1. Templates locais gratuitos.
2. Produto real ou asset real.
3. Texto forte na tela.
4. Roteiros rápidos.
5. Demonstração visual.
6. Custo por vídeo abaixo de €0,20 no início.
7. IA de vídeo paga apenas em vencedores.
```

A versão mais inteligente para começar é:

```text
Remotion + FFmpeg + n8n + PostgreSQL + TTS local + LLM barato/local
```

E só depois adicionar:

```text
OpenAI TTS
ElevenLabs
Seedance
Runway
Veo
```
