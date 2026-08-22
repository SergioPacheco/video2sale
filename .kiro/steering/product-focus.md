---
inclusion: always
---

# Direção de produto - lucro com TikTok Shop

## Missão

O Video2Sale é uma ferramenta interna e single-user para ajudar seu proprietário
a produzir, testar e aprender com vídeos de TikTok Shop que gerem comissão.

O objetivo principal não é vender o software. O objetivo é aumentar o lucro do
operador com TikTok Shop.

## Métrica principal

Otimizar **lucro por hora de produção**:

`(comissões atribuídas - custos variáveis de geração) / horas de trabalho`

Enquanto ainda não houver comissão atribuída suficiente, usar estas métricas
intermediárias, nesta ordem:

1. vídeos efetivamente publicados por semana;
2. tempo mediano entre cadastrar um produto e obter um pacote publicável;
3. percentual de pacotes gerados que o operador decide publicar;
4. visualizações, retenção inicial e cliques no produto;
5. pedidos, comissão e lucro por vídeo/produto/ângulo criativo.

Quantidade de endpoints, agentes, integrações ou vídeos gerados não é métrica de
sucesso.

## Fluxo essencial

Toda alteração deve melhorar diretamente pelo menos uma etapa deste fluxo:

1. registrar produto, fatos comprováveis, oferta e materiais reais;
2. informar briefing e restrições criativas;
3. gerar três conceitos realmente diferentes para 8 ou 16 segundos;
4. revisar e editar antes de aprovar;
5. exportar prompt, roteiro, fala, legenda e referências;
6. produzir/publicar externamente;
7. registrar URL e resultado econômico para aprender o que funciona.

## Princípios obrigatórios

- Preservar fielmente produto, pessoa e imagens de referência.
- Não inventar características, preços, cupons ou resultados.
- Priorizar dor -> solução, demonstração visual e gancho nos dois primeiros segundos.
- Gerar espanhol natural da Espanha por padrão.
- Fazer revisão humana antes de qualquer geração cara ou publicação.
- Preferir entrada manual confiável a scraping frágil.
- Preferir exportação para a ferramenta que já produz vídeo com qualidade a uma
  integração prematura com provedores.
- Implementar uma única jornada vertical completa antes de ampliar o sistema.
- Toda feature nova precisa declarar qual métrica principal ou intermediária melhora.

## Escopo atual

Manter e simplificar:

- produtos e materiais de referência;
- briefing criativo;
- geração estruturada de conceitos, cenas, fala, legenda e CTA;
- revisão/edição e aprovação humana;
- exportação/cópia do pacote de produção;
- histórico mínimo de conteúdos e resultados reais.

## Escopo proibido até validação

Não implementar ou expandir sem evidência obtida após pelo menos 30 vídeos
publicados e resultados registrados:

- SaaS, cadastro, login, multiusuário, cobrança ou planos;
- publicação automática e OAuth do TikTok;
- Amazon PA-API, scraping genérico e descoberta automática de produtos;
- dashboard executivo, múltiplos projetos, presets genéricos ou administração de integrações;
- geração em lote;
- múltiplos idiomas além de `es-ES`;
- múltiplos agentes LLM para tarefas que cabem em uma única geração estruturada;
- Remotion, n8n ou microserviços;
- renderização direta paga via Seedance/Runway/Kling;
- seleção automática de “produto vencedor” com scores subjetivos;
- funcionalidades de aparência profissional que não aumentem publicação, aprendizado ou lucro.

## Gate para nova feature

Antes de implementar qualquer feature fora do fluxo essencial, responder:

1. Qual problema observado em uso real ela resolve?
2. Qual métrica deve melhorar?
3. Qual é a solução manual atual e por que ela já não basta?
4. Qual é a menor implementação testável?
5. O que será removido ou adiado para compensar a complexidade adicionada?

Se as respostas não forem concretas, registrar a ideia no backlog e não implementar.

## Definição de pronto

Uma mudança só está pronta quando:

- existe teste do comportamento crítico;
- o fluxo pode ser executado do início ao fim;
- erros são apresentados de forma acionável;
- a documentação ativa corresponde ao código;
- não adiciona um segundo caminho concorrente para a mesma tarefa;
- produz um resultado que o operador consegue usar na criação/publicação real.

