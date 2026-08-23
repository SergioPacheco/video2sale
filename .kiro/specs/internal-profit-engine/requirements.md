# Requirements - Internal TikTok Shop Profit Engine

## 1. Contexto e objetivo

O Video2Sale será refatorado como ferramenta interna para um único operador. Seu
resultado esperado é reduzir o tempo e aumentar a qualidade da produção de vídeos
de TikTok Shop, acumulando dados que permitam identificar produtos e ângulos
criativos lucrativos.

O sistema não será tratado como SaaS nem como plataforma de automação genérica.
O caminho principal deve ser gratuito: usar assets reais, montagem local e
renderização com FFmpeg; integração paga fica fora do fluxo padrão.

## 2. Persona

Operador que:

- seleciona produtos manualmente no TikTok Shop;
- possui fotos, vídeos ou imagens oficiais do fornecedor;
- usa ferramentas externas de IA para gerar cenas ou vídeos;
- publica manualmente no TikTok;
- precisa criar conteúdo em espanhol da Espanha;
- quer aprender rapidamente quais produtos, hooks e ângulos geram comissão.

## 3. Jornada principal

### R1 - Cadastro mínimo de produto

O sistema deve permitir registrar:

- nome;
- URL do produto e link de afiliado;
- preço e texto de oferta/cupom informado pelo operador;
- benefícios e características comprováveis;
- dor principal;
- público;
- fotos/vídeos/referências;
- observações e restrições visuais.

#### Aceitação

- Campos de marketing nunca são inventados a partir de uma URL.
- O produto pode ser salvo apenas com nome, dor, benefício e uma referência.
- Materiais podem ser adicionados, removidos e ordenados.

### R2 - Briefing por conteúdo

O operador deve escolher:

- duração de 8 ou 16 segundos;
- formato criativo: problema-solução, demonstração, viagem, review ou UGC;
- objetivo do vídeo;
- oferta/CTA a mencionar;
- presença de pessoa, mãos ou somente produto;
- restrições específicas, inclusive elementos que não podem ser alterados.
- assets reais disponíveis para montagem;

#### Aceitação

- O briefing fica associado ao conteúdo gerado.
- Valores padrão refletem o fluxo mais usado: espanhol da Espanha, vertical 9:16
  e hook nos primeiros dois segundos.

### R3 - Geração de três conceitos

O sistema deve gerar três propostas semanticamente distintas, cada uma contendo:

- hook;
- sequência temporal de cenas;
- ação/movimento em cada cena;
- fala em espanhol;
- texto em tela opcional;
- prompt de vídeo;
- legenda, CTA e hashtags;
- lista de fatos/referências utilizados.

#### Aceitação

- As três propostas não podem ser apenas paráfrases.
- A soma das cenas deve respeitar a duração escolhida.
- Produto e personagem devem ser explicitamente preservados nos prompts.
- Alegações, preço e cupom devem vir somente dos dados fornecidos.
- A saída da IA deve ser validada por schema antes de persistir.

### R4 - Revisão e aprovação humana

O sistema deve exibir as propostas lado a lado e permitir:

- editar qualquer campo;
- regenerar somente uma proposta;
- aprovar exatamente uma proposta;
- registrar o motivo opcional da escolha ou rejeição.

#### Aceitação

- Nenhuma proposta recebe estado de seleção humana automaticamente.
- Nenhuma geração de vídeo paga ou publicação ocorre antes da aprovação.

### R5 - Exportação do pacote

O sistema deve permitir copiar ou baixar:

- prompt completo;
- prompts por cena;
- fala;
- legenda, CTA e hashtags;
- referências utilizadas;
- arquivo JSON estruturado.

#### Aceitação

- A exportação funciona sem integração com TikTok ou provedor de vídeo.
- A exportação funciona sem integração com TikTok ou provedor de vídeo pago.
- O pacote indica duração, proporção 9:16 e restrições de preservação.

### R6 - Registro de publicação e resultado

Após publicar manualmente, o operador deve poder registrar:

- URL do TikTok;
- data;
- produto e conceito usado;
- visualizações, curtidas e comentários;
- cliques, pedidos, comissão e custo de geração;
- tempo aproximado de produção.

#### Aceitação

- O sistema calcula lucro e lucro por hora.
- Métricas podem ser atualizadas manualmente.
- Deve ser possível comparar produto, hook, formato e conceito.

### R7 - Histórico operacional mínimo

O sistema deve listar conteúdos por estado:

- rascunho;
- propostas geradas;
- aprovado;
- produzido;
- publicado;
- resultado registrado.

#### Aceitação

- O operador encontra rapidamente trabalhos incompletos.
- A listagem prioriza ação operacional, não KPIs decorativos.

## 4. Requisitos não funcionais

- Execução local com Docker Compose.
- Uma instalação e um operador; sem autenticação.
- Um único backend FastAPI e um frontend Vue.
- PostgreSQL pode ser mantido para reduzir o risco da refatoração.
- Migrações versionadas devem substituir a dependência exclusiva de `init.sql`.
- Segredos permanecem fora do Git.
- Toda chamada paga deve exibir custo estimado antes e custo real depois.
- Falhas da IA não podem deixar registros em estados falsos ou inconsistentes.

## 5. Fora do escopo

- descoberta automática de produtos;
- ranking automático por notas subjetivas;
- Amazon PA-API e scraping de marketplaces;
- trending do TikTok;
- publicação automática;
- TikTok OAuth;
- geração em lote;
- Remotion e n8n;
- múltiplos idiomas;
- multiusuário, SaaS, cobrança e permissões;
- renderização paga integrada antes da validação do pacote criativo.
- renderização paga integrada antes da validação do pacote criativo.

## 6. Critérios de validação do MVP

Executar um ciclo real com pelo menos 30 vídeos publicados.

O MVP é considerado útil quando:

- pelo menos 70% dos pacotes aprovados são publicados;
- a mediana de cadastro até pacote exportado é inferior a 10 minutos;
- o operador consegue produzir conteúdo sem reescrever o prompt do zero;
- custo, tempo e comissão são conhecidos por vídeo;
- existe evidência de quais combinações de produto, hook e formato geram melhor lucro por hora.
- o vídeo final pode ser gerado sem custo recorrente obrigatório.
