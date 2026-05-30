# MVP — Affiliate Video Factory Local

## Objetivo

Criar uma automação local em Docker para gerar vídeos de alta qualidade para afiliados, começando por produtos candidatos para TikTok Shop, afiliados e outros canais.

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
DEFAULT_VIDEO_DURATION_SECONDS=30
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
id,name,category,product_url,price,commission_estimate,pain_score,visual_score,trend_score,competition_score,availability_score,notes
1,Organizador de cozinha,Casa,https://produto-ou-afiliado/...,19.99,3,9,8,7,5,8,Produto bom para piso pequeno
2,Cortador de legumes,Cozinha,https://produto-ou-afiliado/...,14.99,3,8,9,8,7,8,Visual forte para demonstração
3,Suporte notebook,Home office,https://produto-ou-afiliado/...,24.99,3,7,7,6,6,9,Bom para remoto
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
| Duração | 30 segundos |
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
Você é um estrategista de vídeos curtos para afiliados/TikTok Shop.

Crie um pacote criativo para um vídeo vertical de 30 segundos.

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
- Incluir CTA para link do produto / TikTok Shop.
- Incluir aviso de afiliado.
- Dividir em cenas de 2 a 5 segundos.
- Gerar texto na tela para cada cena.
- Gerar narração curta para cada cena.
- Gerar descrição visual de cada cena.
- Gerar legenda para Instagram, TikTok Shop, TikTok, Reels e Shorts.

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
    product_url TEXT,
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


---

# Pesquisa de custos e tecnologias — preferência por gratuitas/trial

## Premissas de volume

Este MVP foi ajustado para a meta operacional de:

```text
30 vídeos/dia
30 segundos por vídeo
900 vídeos/mês
27.000 segundos de vídeo final/mês
```

A decisão principal de custo é:

```text
Gerar vídeo completo por IA
vs
Montar vídeo localmente com template + usar IA apenas em partes específicas
```

Para 900 vídeos/mês, a recomendação é:

> Usar **template local com Remotion/FFmpeg** para o vídeo inteiro e reservar IA de vídeo paga apenas para takes curtos ou produto vencedor.

---

## Estratégia de custo recomendada

### Regra principal

```text
Vídeos comuns:
Remotion local + FFmpeg + assets do produto + texto animado + TTS local/barato

Vídeos intermediários:
Remotion local + 1 take IA curto de 3 a 5 segundos

Produto vencedor:
Versão premium com Seedance, Runway, Veo, Luma ou Pika
```

### Mix recomendado para 30 vídeos/dia

| Tipo | Quantidade/dia | Tecnologia | Objetivo |
|---|---:|---|---|
| Template local gratuito/barato | 24 | Remotion + FFmpeg + assets | Volume e teste |
| Template com take IA curto | 5 | Remotion + Seedance/Wan/Runway curto | Melhorar retenção |
| Premium do vencedor | 1 | Seedance/Runway/Veo/Luma/Pika | Escalar produto validado |

---

## Matriz de tecnologias do MVP

| Camada | Opção preferida | Custo | Gratuito/trial? | API? | Recomendação |
|---|---|---:|---:|---:|---|
| Orquestração | n8n self-hosted | €0 | Sim | Sim | Usar no MVP |
| Banco | PostgreSQL | €0 | Sim | Sim | Usar no MVP |
| Render local | Remotion | €0 para indivíduo/empresa pequena | Sim | Via CLI/código | Usar no MVP |
| Encoding | FFmpeg | €0 | Sim | CLI | Usar no MVP |
| API interna | FastAPI | €0 | Sim | Sim | Usar no MVP |
| Texto/roteiro | OpenAI API ou LLM local | Baixo/variável | OpenAI pode ter créditos/trial; local é grátis | Sim | Usar modelo barato |
| Voz | Piper/Coqui local | €0 | Sim | API local própria | Prioridade para custo zero |
| Voz premium | ElevenLabs/OpenAI TTS | Baixo/médio | Plano grátis/créditos limitados | Sim | Usar só se melhorar conversão |
| Vídeo IA local | Wan 2.1/CogVideoX | €0 API, exige GPU | Sim | API própria | Testar localmente |
| Vídeo IA pago | Seedance/Runway/Veo/Luma/Pika | Médio/alto | Trial/créditos limitados | Depende da plataforma | Só para vencedores |

---

# Tecnologias gratuitas ou com custo quase zero

## 1. n8n self-hosted

Uso no MVP:

```text
Orquestrar workflow:
CSV → ranking → roteiro → compliance → TTS → render → output
```

Status:

```text
Grátis para self-hosted/community edition.
```

Observações:

- Ideal para rodar local em Docker.
- Bom para visualizar e ajustar o fluxo sem criar tudo em código.
- A versão Cloud é paga, mas não é necessária no MVP local.

Recomendação:

> Usar n8n self-hosted no Docker Compose.

---

## 2. PostgreSQL

Uso no MVP:

```text
Salvar produtos, vídeos, vencedores, status e métricas.
```

Status:

```text
100% gratuito e open-source.
```

Recomendação:

> Usar desde o início, mesmo que o CSV continue existindo para entrada simples.

---

## 3. Remotion

Uso no MVP:

```text
Criar vídeos programaticamente com React:
- template 9:16
- textos animados
- legendas
- imagens
- CTA
- barras de progresso
- transições
```

Status:

```text
Gratuito para indivíduos e empresas pequenas elegíveis.
```

Atenção:

- Se o projeto virar empresa maior/equipe maior, revisar licença.
- Para o MVP local e individual, é a melhor opção de custo/qualidade.

Recomendação:

> Renderizar todos os vídeos finais com Remotion + FFmpeg.

---

## 4. FFmpeg

Uso no MVP:

```text
Encoding, corte, concatenação, conversão e compressão.
```

Status:

```text
Gratuito e open-source.
```

Recomendação:

> Usar como motor final de exportação MP4.

---

## 5. TTS local — Piper / Coqui

Uso no MVP:

```text
Gerar narração sem pagar API.
```

Status:

```text
Gratuito se rodar localmente.
```

Pontos de atenção:

- Qualidade pode ser inferior ao ElevenLabs.
- Licenças dos modelos/vozes devem ser verificadas individualmente.
- Pode ser suficiente para vídeos em massa, principalmente quando a força principal for texto na tela.

Recomendação:

> Começar com TTS local. Usar ElevenLabs/OpenAI TTS apenas para vídeos premium.

---

## 6. Vídeo IA local — Wan 2.1 / CogVideoX

Uso no MVP:

```text
Gerar takes curtos de 3 a 5 segundos localmente.
```

Status:

```text
Sem custo de API, mas exige GPU/VRAM e tempo de render.
```

Pontos de atenção:

- Não é “grátis” em termos de hardware/energia.
- Pode ser lento para 30 vídeos/dia.
- Mais indicado para gerar alguns takes de apoio ou testar produto vencedor.

Recomendação:

> Incluir como serviço opcional no Docker, não como dependência obrigatória do MVP.

---

# Tecnologias pagas ou com trial limitado

## 1. OpenAI API — texto, roteiro, compliance e possível TTS

Uso no MVP:

```text
- geração de roteiro
- variações de gancho
- compliance
- legenda
- CTA
- descrição de cenas
```

Custo:

```text
Baixo para texto.
Variável para TTS/imagem.
```

Grátis/trial:

```text
Pode haver créditos iniciais dependendo da conta/região, mas não deve ser assumido como base permanente.
```

Recomendação:

> Usar para texto, porque o custo por roteiro tende a ser baixo. Para reduzir custo, usar modelo barato para roteiros em massa e modelo melhor apenas no produto vencedor.

---

## 2. ElevenLabs — voz premium

Uso no MVP:

```text
Narração mais natural para vídeos com maior potencial.
```

Custo:

```text
Plano grátis com créditos limitados.
Planos pagos conforme volume.
```

Para 900 vídeos/mês:

```text
900 vídeos × ~500 caracteres = ~450.000 caracteres/mês
```

Conclusão:

> O plano grátis não sustenta 900 vídeos/mês. Usar TTS local para massa e ElevenLabs para os melhores vídeos.

---

## 3. Runway

Uso no MVP:

```text
Gerar takes de vídeo IA premium.
```

Custo:

```text
Paga por créditos.
API cobra créditos por geração.
Plano free tem créditos limitados.
```

Observação operacional:

```text
30 vídeos × 30s × 30 dias = 27.000 segundos/mês.
Gerar tudo no Runway é caro.
```

Recomendação:

> Não usar para todos os vídeos. Usar apenas para produto vencedor ou cenas curtas.

---

## 4. Seedance

Uso no MVP:

```text
Gerar takes curtos de 3 a 5 segundos.
```

Custo:

```text
Geralmente por créditos/segundo, variando por modelo e resolução.
```

Cenários:

```text
3 segundos IA por vídeo:
900 × 3s = 2.700 segundos/mês

5 segundos IA por vídeo:
900 × 5s = 4.500 segundos/mês

30 segundos IA por vídeo:
900 × 30s = 27.000 segundos/mês
```

Recomendação:

> Seedance pode ser interessante para takes curtos, não para gerar 30s completos de todos os vídeos.

---

## 5. Google Veo / Gemini API

Uso no MVP:

```text
Vídeos premium do produto vencedor.
```

Custo:

```text
Pago por segundo na API.
Não há free tier de produção para Veo.
```

Observação:

- Muito bom para qualidade.
- Custo sobe rápido se usado em massa.
- Melhor para produto validado.

Recomendação:

> Não usar no MVP em massa. Usar só para vídeos premium.

---

## 6. Luma Dream Machine

Uso no MVP:

```text
Gerar vídeos criativos ou cenas premium.
```

Custo:

```text
Planos pagos, geralmente com trial/créditos.
```

Recomendação:

> Testar como alternativa visual, mas não como base de 30 vídeos/dia.

---

## 7. Pika

Uso no MVP:

```text
Cenas criativas, efeitos, variações.
```

Custo:

```text
Plano free para teste e planos pagos.
API pode depender de integração/provedor.
```

Recomendação:

> Boa para testar estilos, mas não usar como dependência central do MVP.

---

# Comparação de custo por vídeo — 30 segundos

## Cenário 1 — Gratuito/quase gratuito

Vídeo gerado com:

```text
Remotion + FFmpeg + assets do produto + texto animado + música gratuita + TTS local opcional
```

Custo estimado:

```text
€0 a €0,05 por vídeo
€0 a €45/mês para 900 vídeos
```

Melhor para:

```text
Validação em massa.
```

Limitações:

```text
- Depende de bons assets.
- Pode parecer repetitivo se os templates não variarem.
- Voz local pode não ser tão natural.
```

---

## Cenário 2 — Baixo custo com IA de texto + voz melhor

Vídeo gerado com:

```text
Remotion + FFmpeg + IA para roteiro + TTS pago/barato
```

Custo estimado:

```text
€0,03 a €0,20 por vídeo
€27 a €180/mês para 900 vídeos
```

Melhor para:

```text
Operação inicial com boa qualidade.
```

---

## Cenário 3 — Template local + take IA curto

Vídeo gerado com:

```text
Remotion + FFmpeg + TTS + 3 a 5 segundos de vídeo IA
```

Custo estimado:

```text
€0,10 a €0,70 por vídeo
€90 a €630/mês para 900 vídeos
```

Melhor para:

```text
Vídeos com maior potencial ou categorias mais competitivas.
```

---

## Cenário 4 — 30 segundos inteiros de IA de vídeo

Vídeo gerado com:

```text
Runway / Seedance / Veo / Luma / Pika para o vídeo inteiro
```

Custo estimado:

```text
€1,50 a €10+ por vídeo
€1.350 a €9.000+/mês para 900 vídeos
```

Conclusão:

> Não recomendado para o MVP. O custo destrói a margem antes de validar produto.

---

# Plano financeiro recomendado para o MVP

## Fase 1 — Zero ou quase zero

Objetivo:

```text
Provar que a fábrica local gera 30 vídeos/dia.
```

Tecnologias:

```text
n8n self-hosted
PostgreSQL
FastAPI
Remotion
FFmpeg
TTS local
CSV/JSON
```

Orçamento:

```text
€0 a €20/mês
```

---

## Fase 2 — Baixo custo

Objetivo:

```text
Melhorar qualidade da narração e roteiro.
```

Adicionar:

```text
OpenAI API para roteiro/compliance
TTS pago apenas nos melhores vídeos
```

Orçamento:

```text
€30 a €150/mês
```

---

## Fase 3 — Premium controlado

Objetivo:

```text
Criar vídeos premium só para produtos vencedores.
```

Adicionar:

```text
Seedance / Runway / Veo / Luma / Pika apenas para takes curtos
```

Orçamento:

```text
€150 a €500/mês
```

---

# Alteração na arquitetura do MVP

A arquitetura passa a ter dois caminhos de renderização:

## Caminho A — barato/padrão

```text
Produto
↓
Roteiro
↓
TTS local/barato
↓
Assets do produto
↓
Remotion
↓
FFmpeg
↓
video-final.mp4
```

## Caminho B — premium/opcional

```text
Produto vencedor
↓
Roteiro premium
↓
Prompt de take IA
↓
Seedance/Runway/Veo/Wan
↓
Remotion
↓
FFmpeg
↓
video-premium.mp4
```

---

# Novo serviço opcional no Docker

## `local-video-ai-service`

Serviço opcional para rodar Wan 2.1 ou CogVideoX localmente.

```text
services/
└── local-video-ai-service/
    ├── Dockerfile
    ├── app/
    │   ├── main.py
    │   ├── wan_adapter.py
    │   └── cogvideo_adapter.py
    └── models/
```

Endpoints sugeridos:

```http
POST /generate-take
```

Payload:

```json
{
  "prompt": "Cocina pequeña, persona usando cortador de legumes, estilo realista, vertical 9:16",
  "duration_seconds": 3,
  "resolution": "720p",
  "model": "wan2.1"
}
```

Resposta:

```json
{
  "status": "OK",
  "video_path": "/output/2026-W21/2/take-ai-01.mp4"
}
```

---

# Atualização do Docker Compose — serviço opcional

```yaml
  local-video-ai-service:
    build: ./services/local-video-ai-service
    container_name: avf-local-video-ai-service
    profiles:
      - local-ai
    env_file:
      - .env
    volumes:
      - ./models:/models
      - ./output:/output
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

Uso:

```bash
docker compose --profile local-ai up -d --build
```

Observação:

```text
Este serviço só faz sentido se a máquina tiver GPU compatível.
```

---

# Atualização do `.env`

```env
# Motor principal
VIDEO_RENDER_MODE=template

# Opções:
# template
# template_plus_ai_take
# full_ai_video

# TTS
TTS_PROVIDER=local
TTS_LOCAL_ENGINE=piper

# IA de vídeo opcional
LOCAL_VIDEO_AI_ENABLED=false
LOCAL_VIDEO_AI_MODEL=wan2.1

# Provedores pagos opcionais
RUNWAY_API_KEY=
SEEDANCE_API_KEY=
GOOGLE_API_KEY=
LUMA_API_KEY=
PIKA_API_KEY=
ELEVENLABS_API_KEY=
```

---

# Decisão recomendada para o MVP

## Ordem de prioridade

1. **Remotion + FFmpeg**
2. **TTS local**
3. **OpenAI API ou LLM barato para roteiros**
4. **Wan/CogVideoX local opcional**
5. **ElevenLabs só nos melhores vídeos**
6. **Seedance/Runway/Veo/Luma/Pika só para o vencedor**

---

# Critério de sucesso atualizado

O MVP está pronto quando for possível:

1. Rodar tudo local com Docker.
2. Gerar 30 vídeos de 30 segundos em um dia.
3. Manter custo de API próximo de zero no modo template.
4. Criar pelo menos 5 templates visuais diferentes.
5. Gerar variações de roteiro para o mesmo produto.
6. Escolher produto vencedor por score.
7. Gerar uma versão premium opcional do vencedor.
8. Salvar relatório de custo por vídeo.
9. Comparar custo estimado: template vs IA curta vs IA completa.

---

# Estratégia final recomendada

```text
Não tente gerar 900 vídeos/mês com IA de vídeo.
Gere 900 vídeos/mês com template local.
Use IA paga somente onde aumenta a chance de venda.
```

Resumo:

| Necessidade | Melhor escolha |
|---|---|
| 30 vídeos/dia | Remotion + FFmpeg |
| Custo quase zero | TTS local + assets próprios |
| Melhor voz | ElevenLabs/OpenAI TTS só nos melhores |
| IA de vídeo grátis | Wan/CogVideoX local |
| IA de vídeo paga | Seedance/Runway/Veo só para vencedor |
| Escala | Template local |
| Qualidade premium | Takes curtos de IA + edição local |

---

# Fontes pesquisadas

> Preços e planos mudam frequentemente. Antes de contratar, conferir a página oficial de cada fornecedor.

- Remotion License/Pricing: https://www.remotion.pro/license
- Remotion Docs License: https://www.remotion.dev/docs/license
- n8n Pricing: https://n8n.io/pricing/
- n8n Community Edition: https://docs.n8n.io/hosting/community-edition-features/
- Runway API Pricing: https://docs.dev.runwayml.com/guides/pricing/
- Runway Pricing: https://runwayml.com/pricing
- OpenAI API Pricing: https://openai.com/api/pricing/
- Google Gemini API Pricing / Veo: https://ai.google.dev/gemini-api/docs/pricing
- ElevenLabs Pricing: https://elevenlabs.io/pricing
- Luma Pricing: https://lumalabs.ai/pricing
- Pika Pricing: https://pika.art/pricing
- Pika API: https://pika.art/api
- Wan 2.1 GitHub: https://github.com/Wan-Video/Wan2.1
- CogVideo GitHub: https://github.com/zai-org/CogVideo
- Coqui TTS GitHub: https://github.com/coqui-ai/TTS

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
TikTok Shop Video Factory
Viral Product Studio
Content Ops Affiliate
```
