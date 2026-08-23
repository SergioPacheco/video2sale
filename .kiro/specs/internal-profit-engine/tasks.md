# Tasks - Refatoração orientada a lucro

Cada fase deve terminar utilizável. Não iniciar a fase seguinte com testes
vermelhos ou dois fluxos ativos para a mesma tarefa.

## Fase 0 — Baseline e segurança

- [ ] Criar branch de refatoração e tag do estado atual.
- [ ] Documentar como iniciar o sistema atual e registrar falhas reproduzíveis.
- [ ] Adicionar um smoke test do fluxo principal atual.
- [ ] Introduzir Alembic e gerar baseline sem destruir o banco existente.
- [ ] Declarar e implementar o fluxo gratuito como padrão no caminho principal.
- [ ] Corrigir imediatamente o erro de `thumbnail_path` no Seedance enquanto o
      fluxo legado ainda estiver acessível.

**Saída:** estado atual reproduzível e banco protegido por migrações.

## Fase 1 - Corte de superfície

- [ ] Retirar da navegação Dashboard, Trending, Settings genérico e ações de publicação.
- [ ] Desabilitar batch, escolha automática de produto e renderização Seedance no frontend.
- [ ] Remover Seedance do fluxo principal; manter apenas como legado fora do fluxo.
- [ ] Marcar endpoints legados como deprecated na OpenAPI.
- [ ] Criar feature flags somente se forem necessárias para preservar dados durante a transição.
- [ ] Atualizar README para declarar ferramenta interna e novo fluxo.

**Saída:** interface mostra apenas Produtos, Produzir, Fila e Resultados.

## Fase 2 - Domínio mínimo

- [ ] Criar/migrar `Product`, `ProductAsset`, `ContentJob`, `CreativeConcept` e
      `PublicationResult` conforme o design.
- [ ] Unificar `Product.assets` e tabela `assets` em `ProductAsset`.
- [ ] Migrar produtos e referências existentes.
- [ ] Implementar validação de benefícios, oferta e restrições.
- [ ] Criar testes de persistência e migração.

**Saída:** dados necessários ao processo criativo sem entidades paralelas.

## Fase 3 - Geração criativa utilizável

- [ ] Definir schema Pydantic da saída de três conceitos.
- [ ] Reescrever o prompt com fatos verificados, restrições e diversidade entre conceitos.
- [ ] Implementar geração em uma chamada e validações determinísticas.
- [ ] Garantir timelines exatas para 8 e 16 segundos.
- [ ] Persistir versão do prompt, custo, entrada e saída normalizada.
- [ ] Implementar regeneração de somente uma proposta.
- [ ] Cobrir provedor com mocks e casos de saída inválida.

**Saída:** três propostas distintas e confiáveis para um briefing real.

## Fase 4 - Revisão, edição e exportação

- [ ] Criar jornada Produto -> Briefing -> Propostas.
- [ ] Implementar comparação lado a lado.
- [ ] Permitir editar cenas, fala, prompt, legenda e CTA.
- [ ] Exigir ação humana para aprovação.
- [ ] Implementar copiar por campo, copiar pacote e baixar JSON/Markdown.
- [ ] Incluir referências e restrições em toda exportação.
- [ ] Criar teste end-to-end do cadastro à exportação.

**Saída:** pacote que o operador consegue usar sem reescrever do zero.

## Fase 5 - Aprendizado econômico

- [ ] Criar registro manual de publicação e métricas.
- [ ] Calcular custo, lucro e lucro por hora.
- [ ] Criar fila por próxima ação.
- [ ] Criar tabela comparativa por produto, hook, formato e conceito.
- [ ] Exportar dados para CSV.

**Saída:** decisões de produção baseadas em retorno, não em score subjetivo.

## Fase 6 - Remoção do legado

- [ ] Confirmar que dados úteis foram migrados e criar backup.
- [ ] Remover routers antigos de `app/main.py`.
- [ ] Excluir componentes frontend sem rota.
- [ ] Remover dependências e serviços não usados.
- [ ] Remover tabelas legadas em migração separada e reversível.
- [ ] Atualizar README, diagrama e comandos.
- [ ] Executar testes e smoke test em instalação limpa e banco migrado.

**Saída:** um único produto coerente, sem código morto operacional.

## Gate de validação - 30 vídeos

- [ ] Publicar 30 vídeos usando pacotes do sistema.
- [ ] Registrar tempo, custo e resultado de cada vídeo.
- [ ] Medir taxa de publicação dos pacotes e tempo até exportação.
- [ ] Revisar as rejeições e ajustar prompt/UX.
- [ ] Identificar o gargalo real antes de escolher a próxima feature.

Somente após esse gate avaliar TTS, renderização, importação de métricas,
integração com provedor de vídeo ou publicação assistida.
