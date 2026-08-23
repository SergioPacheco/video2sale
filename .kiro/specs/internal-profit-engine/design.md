# Design - Refatoração para ferramenta interna orientada a lucro

## 1. Decisão arquitetural

Construir um monólito local simples:

```text
Vue 3
  -> FastAPI
      -> PostgreSQL
      -> OpenAI (geração estruturada)
      -> armazenamento local de referências/exportações
```

O caminho principal não usará renderização paga. A montagem de vídeo será local
e gratuita, baseada em assets reais, cortes simples e FFmpeg.

## 2. Único fluxo de aplicação

```text
Produto -> Briefing -> 3 conceitos -> Revisão -> Aprovação -> Exportação
                                                     |
                                                     v
                                  Publicação manual -> Resultado
```

Rotas e telas antigas não devem oferecer caminhos alternativos para gerar o
mesmo conteúdo.

## 3. Modelo de domínio reduzido

### Product

- `id`, `name`, `product_url`, `affiliate_url`
- `price`, `offer_text`
- `pain`, `audience`
- `verified_benefits[]`
- `visual_restrictions[]`
- `active`, timestamps

### ProductAsset

- `id`, `product_id`, `type`, `path_or_url`, `label`, `position`
- `is_primary`, `active`

Usar uma única representação de asset. Eliminar a duplicidade atual entre
`Product.assets` JSON e a tabela `assets`.

### ContentJob

- `id`, `product_id`, `duration_seconds`, `format`, `goal`
- `cta`, `offer_text`, `presence_mode`, `extra_constraints[]`
- `status`, `estimated_cost`, `actual_cost`, timestamps

### CreativeConcept

- `id`, `content_job_id`, `variant`, `angle`, `hook`
- `scenes` JSON validado, `caption`, `cta`, `hashtags`
- `generation_prompt_version`, `selected`, `rejection_reason`

### PublicationResult

- `id`, `content_job_id`, `tiktok_url`, `published_at`
- métricas de alcance e conversão
- `commission`, `generation_cost`, `production_minutes`
- valores calculados: `profit`, `profit_per_hour`

## 4. API-alvo

- `POST /products`, `GET /products`, `PUT /products/{id}`
- `POST /products/{id}/assets`, `DELETE /assets/{id}`
- `POST /content-jobs`
- `POST /content-jobs/{id}/concepts`
- `PUT /concepts/{id}`
- `POST /concepts/{id}/approve`
- `POST /concepts/{id}/regenerate`
- `GET /content-jobs/{id}/export`
- `POST /content-jobs/{id}/publication-result`
- `PUT /publication-results/{id}`
- `GET /content-jobs?status=...`

O endpoint antigo `/pipeline/full` será substituído após a migração do frontend.

## 5. Geração criativa

Usar uma única chamada estruturada para gerar três conceitos e validação local
determinística para:

- schema obrigatório;
- duração total;
- presença de hook entre 0 e 2 segundos;
- idioma `es-ES`;
- ausência de preço/oferta não fornecidos;
- presença das restrições de preservação em cada prompt visual.

Compliance não deve ser um segundo agente genérico. Regras determinísticas são
aplicadas localmente; somente casos linguísticos que não possam ser validados
localmente justificam uma segunda chamada.

## 6. Interface

### Tela Produzir

Stepper curto, em uma única jornada:

1. Produto e materiais.
2. Briefing.
3. Comparação de três propostas.
4. Edição e aprovação.
5. Exportação.

### Tela Fila

Lista operacional com próxima ação, estado e idade do trabalho.

### Tela Resultados

Tabela comparativa simples por vídeo, produto, hook e formato. Não criar dashboard
antes de existirem dados suficientes.

## 7. Migração do código existente

### Reaproveitar

- shell Vue/PrimeVue e cliente HTTP;
- CRUD básico de produtos;
- conceitos de assets, creative packs e eventos;
- prompt de roteiro, após reescrita;
- exportação JSON/texto;
- Docker Compose, FastAPI e PostgreSQL.

### Congelar e retirar da aplicação

- `trending.py`, `amazon_search.py`, `product_ranker.py`;
- `tiktok.py`, `integrations.py`, `publications.py` antigos;
- `projects.py`, `presets.py`, `renders.py`, `metrics.py`, `stats.py`;
- `renderer_seedance.py` e `services/remotion-renderer`;
- batch e seleção semanal;
- fluxo manual concorrente existente em `videos.py`.

### Avaliar depois dos 30 vídeos

- TTS automático;
- TTS gratuito/local se houver ganho claro na velocidade de produção;
- montagem FFmpeg;
- importação automatizada de métricas;
- integração direta com um provedor de vídeo;
- publicação assistida.

## 8. Estratégia segura de transição

1. Criar novas tabelas e rotas sem apagar dados existentes.
2. Migrar produtos e assets úteis.
3. Construir o novo fluxo e seus testes.
4. Trocar a navegação para o novo fluxo.
5. Executar smoke test completo.
6. Remover routers antigos de `main.py`.
7. Somente depois excluir código morto e tabelas legadas em migração separada.

## 9. Testes mínimos

- geração estruturada com provedor mockado;
- rejeição de saída inválida;
- nenhuma alegação/oferta inventada;
- duração correta de 8 e 16 segundos;
- aprovação explicitamente humana;
- exportação completa e reproduzível;
- cálculo de lucro e lucro por hora;
- teste end-to-end do cadastro à exportação.
- teste end-to-end do cadastro à exportação com montagem gratuita.
