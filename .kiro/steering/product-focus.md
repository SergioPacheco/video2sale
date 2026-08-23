---
inclusion: always
---

# Direção de produto — Creative Intelligence para TikTok Shop

## Missão

O Video2Sale é uma ferramenta interna para gerar vídeos de TikTok Shop com
máxima capacidade de conversão, usando:

- Produtos reais com fotos e dados verificados
- Referências de vídeos vencedores como fonte de padrões
- OpenAI como motor principal de inteligência criativa
- FFmpeg/Remotion para composição determinística
- Aprendizado baseado em performance real (vendas/GMV/comissão)

O objetivo não é vender o software. O objetivo é maximizar vendas no TikTok Shop.

## Métrica principal

**vendas / GMV / comissão gerada pelos vídeos**

Enquanto não houver dados suficientes de vendas, usar nesta ordem:

1. vídeos publicados com Quality Gate aprovado
2. CTR e retenção nos primeiros 2 segundos
3. visualizações e engajamento
4. custo por criativo aprovado

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

## Princípios obrigatórios

### Fidelidade do Produto (CRÍTICO)
- Nunca redesenhar ou reinterpretar o produto
- Preservar cor, forma, logo, bolsos, zíperes, alças, costuras
- Não adicionar nem remover componentes
- Validar automaticamente: original vs gerado

### Inteligência Criativa
- Aprender COM vídeos vencedores, não COPIAR
- Extrair estrutura, ritmo, mecanismo do hook, tipo de demonstração
- Adaptar estratégia ao nosso produto
- Hook é entidade de primeira classe (rastrear CTR por hook)

### OpenAI como motor principal
- Usar Structured Outputs sempre (não regex em texto)
- Centralizar modelos em configuração
- Cachear análises caras (ProductProfile, CreativeDNA)
- Usar modelo caro só quando melhora resultado

### Qualidade antes de volume
- Quality Gate obrigatório antes de publicação
- Não publicar conteúdo genérico só porque JSON é válido
- Cada vídeo deve ter hook específico, prova visual, CTA coerente

### Simplicidade arquitetural
- 1 aplicação, 1 banco, 1 worker/job
- FFmpeg para composição determinística
- Remotion quando precisar de animação complexa
- Sora/gpt-image quando precisar de geração

## Fluxo de decisão para geração

```
Cena precisa de geração?
    ├─► NÃO → usar asset real do produto
    │
    └─► SIM → É movimento simples?
              ├─► SIM → FFmpeg (zoom, pan, fade)
              │
              └─► NÃO → É composição com texto/efeitos?
                        ├─► SIM → Remotion
                        │
                        └─► NÃO → É cena complexa de lifestyle?
                                  └─► Sora/gpt-image
```

## Escopo atual (MVP)

Implementar e validar:

1. ProductAnalyzer → ProductProfile estruturado
2. CompetitorVideoAnalyzer → CreativeDNA de referências
3. CreativePlanner → 5 conceitos diferentes por produto
4. ProductFidelityValidator → QA multimodal de assets
5. VideoQualityGate → Technical + Creative QA
6. Pipeline integrado com rastreabilidade

## Escopo bloqueado até validação

Não implementar até ter 30+ vídeos publicados com métricas:

- Publicação automática TikTok (OAuth, upload)
- Multi-idioma além de pt-BR
- Dashboard de analytics
- SaaS/multiusuário
- Integrações com marketplaces

## Definição de pronto

Uma mudança está pronta quando:

- Usa Structured Outputs (não regex)
- Preserva fidelidade do produto
- Passa no Quality Gate
- Tem rastreabilidade (qual referência inspirou qual criativo)
- Produz resultado que pode ser publicado
