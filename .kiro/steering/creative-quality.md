---
inclusion: always
---

# Qualidade criativa — Creative Intelligence Engine

## Problema que esta regra evita

Vídeos genéricos que listam características sobre fotos estáticas não vendem.
O sistema deve aprender COM vídeos vencedores e adaptar suas estratégias ao
nosso produto, não copiar conteúdo nem gerar slideshow.

## Princípio central

Cada vídeo deve:

1. Interromper o scroll em 0-2 segundos com hook específico
2. Criar tensão ou desejo reconhecível
3. Demonstrar o produto resolvendo um problema real
4. Mostrar prova visual do benefício
5. Fechar com CTA que continua a história

Um vídeo não é uma lista de características narrada sobre fotos.

## Pipeline de Inteligência Criativa

### 1. Análise de Produto
```
Fotos do produto + descrição
        ↓
OpenAI Vision + Structured Output
        ↓
ProductProfile:
- problemas que resolve
- desejos relacionados
- benefícios demonstráveis
- objeções comuns
- claims permitidos vs proibidos
- características visuais invariáveis
```

### 2. Análise de Referência
```
Vídeo vencedor
        ↓
FFmpeg extrai (frames + áudio)
        ↓
OpenAI Transcrição + Vision
        ↓
CreativeDNA:
- tipo e duração do hook
- estrutura narrativa
- pacing e ritmo
- técnicas de demonstração
- gatilhos emocionais
- mecanismos de curiosidade
- estratégia de CTA
- POR QUE funciona (não O QUE faz)
```

### 3. Reconhecimento de Padrões
```
CreativeDNA[] de múltiplas referências
        ↓
Análise OpenAI
        ↓
WinningPatterns:
- padrões recorrentes
- tempos comuns
- estruturas que repetem
- elementos que variam
```

### 4. Planejamento Criativo
```
ProductProfile + WinningPatterns + Performance anterior
        ↓
OpenAI Structured Output
        ↓
CreativePlan[]:
- 5 conceitos DIFERENTES (não variações do mesmo)
- Hook como entidade rastreável
- Cenas com modo de geração
- Rastreabilidade de origem
```

## Regras do Hook

O hook é entidade de primeira classe porque:
- É o que determina se alguém para de scrollar
- É mensurável (CTR nos primeiros 2s)
- É reutilizável entre criativos
- É a principal fonte de aprendizado

```
Tipos de Hook:
- problem     → "Cansou de pagar taxa de bagagem?"
- desire      → "Se você ama viajar..."
- price       → "Por menos de R$150..."
- curiosity   → "O que ninguém te conta sobre..."
- demonstration → [visual do produto em ação]
- surprise    → resultado inesperado
```

Cada hook deve ter:
- ID único para rastreamento
- Tipo classificado
- Texto/conceito visual
- Duração alvo (< 2s)
- Insight de origem (de qual referência aprendeu)

## Regras de fidelidade do produto (CRÍTICO)

A IA NÃO pode redesenhar o produto. Ao gerar/editar imagens:

PRESERVAR EXATAMENTE:
- formato e proporções
- cor e materiais
- logo e marcas
- zíperes, bolsos, alças, costuras
- quantidade de itens/acessórios
- textura aparente

PODE ALTERAR:
- fundo/cenário
- iluminação
- enquadramento
- qualidade fotográfica
- contexto de uso

VALIDAÇÃO OBRIGATÓRIA:
```
Original + Gerado → OpenAI Vision
        ↓
ProductFidelityResult:
- score >= 90
- sameProduct = true
- inventedFeatures = []
```

## Quality Gate

### QA Técnico (código/FFprobe)
```
- arquivo existe e não está corrompido
- codec H.264, resolução 1080x1920
- aspect ratio 9:16
- duração 8-30s
- áudio presente e normalizado
- sem frames pretos/congelados
```

### QA Criativo (OpenAI)
```
Frames + Transcrição + CreativePlan → OpenAI
        ↓
CreativeQualityScore:
- overall >= 80
- hook >= 80 (específico, não genérico)
- productFidelity >= 90
- productVisibility >= 80
- demonstration >= 70
- pacing (ritmo adequado)
- authenticity (parece UGC, não comercial)
- cta (coerente com história)
```

Se reprovar:
- Identificar componente ruim
- Regenerar APENAS esse componente
- Máximo 2 retries por asset

## Estruturas narrativas

### 8 segundos
```
0-2s: hook (problema/desejo + visual)
2-4s: tensão/custo do problema
4-6.5s: produto em ação + prova
6.5-8s: payoff + CTA curto
```

### 16 segundos
```
0-2s: interrupção + promessa específica
2-5s: situação/dor reconhecível
5-10s: demonstração resolvendo
10-13s: benefício visível + reação
13-16s: oferta + CTA
```

## O que NÃO copiar de referências

NUNCA reutilizar:
- áudio/música original
- voz do creator
- rosto/identidade
- texto literal
- marca d'água
- composição frame-a-frame

APRENDER e adaptar:
- estrutura narrativa
- tipo de hook
- ritmo e pacing
- mecanismo de demonstração
- estratégia de CTA

## Experimentação

Testar profundidade antes de variedade:

1. Escolher produto com materiais adequados
2. Criar 5 ângulos REALMENTE diferentes
3. Manter produto, variar uma hipótese: hook, dor, demo, CTA
4. Publicar e registrar resultados
5. Iterar sobre vencedor antes de trocar produto

Alocação sugerida:
```
70% → variações de estratégias vencedoras
20% → estratégias secundárias
10% → experimentos novos
```
