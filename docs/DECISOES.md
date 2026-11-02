# Decisões técnicas

Cada decisão traz: o que foi escolhido, as alternativas, **a evidência medida** e **o que faria mudar a escolha**. A coluna "Origem" diz quem propôs: o baseline gerado pelo ChatGPT ou uma decisão tomada durante a revisão. As escolhas do baseline foram mantidas só depois de medidas; nenhuma delas é apresentada como projeto original do autor.

| # | Decisão | Origem | Estado |
|---|---|---|---|
| 1 | Equilíbrio entre engenharia confiável e IA aplicada | Revisão (autor) | Adotada |
| 2 | *Function calling* direto | Baseline | Mantida, medida |
| 3 | Dados estruturados em funções Python | Baseline | Mantida, medida |
| 4 | Políticas por busca lexical | Baseline | Mantida como linha de base; **limite conhecido** |
| 5 | Modelo `gpt-4.1-mini` | Baseline | Mantido; só latência comparada |
| 6 | Interface web local + CLI | Revisão | Adotada |
| 7 | Chave de API colada na tela | Revisão | Adotada |
| 8 | Respostas só em texto (sem cartões) | Revisão (autor) | Adotada após experimento |
| 9 | Dados públicos sanitizados e originais fora do Git | Baseline, reforçada na revisão | Adotada |

## 1. Equilíbrio entre engenharia confiável e IA aplicada

**Escolha:** manter o escopo pequeno e só acrescentar técnica (frameworks, embeddings, SQL) quando uma medição mostrar um problema que ela resolve.
**Por quê:** o enunciado avalia lógica, clareza e iniciativa, e diz que o foco é o agente funcionando. Complexidade sem ganho medido seria difícil de defender.
**Mudaria se:** uma falha medida na bateria só pudesse ser resolvida por uma técnica mais pesada.

## 2. *Function calling* direto

**Como funciona:** 4 ferramentas só de leitura com esquema estrito; o modelo escolhe, Python executa, o resultado volta ao modelo; laço de até 6 voltas; histórico só em memória.
**Alternativas:** ReAct em texto (exige interpretar a saída do modelo; os modelos atuais já chamam ferramentas nativamente); LangGraph (estado e checkpoints que este fluxo, sem ramificações, não usa).
**Evidência:** na bateria, a ferramenta certa foi escolhida em todos os cenários de dados e de políticas; as únicas falhas de roteamento vieram de **prompt**, não da arquitetura (veja [`AVALIACAO.md`](AVALIACAO.md)).
**Mudaria se:** surgissem falhas de encadeamento de vários passos ou necessidade de aprovação humana no meio do fluxo.

## 3. Dados estruturados em funções Python

**Como funciona:** CSVs carregados em memória; preço promocional com `Decimal` e arredondamento comercial; desconto de PIX nunca acumula com promoção; produto descontinuado, "em breve" ou sem estoque nunca aparece como disponível.
**Alternativas:** SQLite (nenhum ganho com 65 produtos); agente de SQL (daria ao modelo acesso à tabela de clientes e resultados não reproduzíveis).
**Evidência:** as 4 promoções ativas bateram com um cálculo independente; as integrações entre as 6 tabelas não têm registros órfãos. Medida de escala: `search_products` cresce linearmente (65 → 6.500 produtos: 2 ms → 196 ms); `search_promotions` e `order_status` ficam constantes.
**Mudaria se:** as consultas ficassem relacionais demais ou os dados passassem de milhares de linhas.

## 4. Políticas por busca lexical

**Como funciona:** uma unidade por página do PDF, normalização sem acento, sinônimos e um reforço por tema. Os termos do manual são indexados **uma vez**.
**Alternativas:** BM25 por parágrafo (próximo passo barato); embeddings ou busca híbrida (infraestrutura, chave extra e envio do manual a um terceiro, difícil de justificar para 8 páginas).
**Evidência e limite:** em 17 perguntas parafraseadas sobre o manual original, a página certa ficou em 1º em 10 e entre as 3 primeiras em 14; 3 voltaram vazias ("Vocês abrem aos domingos?"). Com o modelo real, o cenário de paráfrase oscilou entre 0 de 3 e 3 de 3 de uma rodada para outra, porque depende do texto que o modelo manda para a busca. **É a principal fragilidade conhecida.**
**Mudaria se:** o BM25 por parágrafo, medido nas mesmas 17 perguntas, não eliminasse as falhas; só então embeddings.

## 5. Modelo `gpt-4.1-mini`

**Escolha:** modelo pequeno com chamada de ferramentas, configurável (`OPENAI_MODEL` e campo na tela).
**Evidência:** a mediana por resposta, com as mesmas 6 perguntas, foi de 2,24 s (`gpt-4.1-mini`), 2,27 s (`gpt-4o-mini`) e 1,91 s (`gpt-4.1`). O `gpt-4.1-nano` foi descontinuado pela OpenAI. **A qualidade só foi medida no `gpt-4.1-mini`**, então não há comparação de acertos entre modelos.
**Mudaria se:** a bateria rodada em outro modelo mostrasse mais acertos ou menos tokens com latência semelhante.

## 6. Interface web local + CLI

**Escolha:** página única servida só em `127.0.0.1`, com a biblioteca padrão do Python, sem dependência nova. Mostra o que o agente consultou, o tempo de cada chamada ao modelo, o texto em streaming e a saída bruta de cada ferramenta.
**Alternativas:** Streamlit/Gradio (framework novo); API sem tela (não mostra o comportamento); só CLI (difícil para um avaliador explorar).
**Por quê:** o recrutador precisa testar sem conhecer o projeto, mas o foco continua sendo o agente.

## 7. Chave de API colada na tela

**Escolha:** a pessoa que avalia traz a própria chave e cola na interface; ela fica só na memória, é mascarada em mensagens de erro e nunca é exportada. Sem chave, o modo Offline e as [conversas gravadas](../examples/) mostram o agente.
**Alternativa descartada:** demo hospedada com a chave do autor (custo, abuso e risco de vazamento).
**Detalhe:** a variável de ambiente `OPENAI_BASE_URL` é ignorada de propósito. Só `--base-url` muda o endpoint; sem isso, um proxy herdado do ambiente redirecionava as chamadas sem aviso.

## 8. Respostas só em texto, sem cartões

**O que foi tentado:** cartões de produto e de pedido e um cartão com o trecho do manual, montados na página a partir da saída bruta das ferramentas.
**Por que saiu:** (a) existiam **só na interface**: o terminal, o modo offline, o `.md` exportado e os exemplos do repositório não os teriam; (b) repetiam a lista que o próprio texto já trazia; (c) o cartão do manual só fazia sentido para perguntas específicas. O texto do agente precisa se sustentar sozinho em qualquer canal.
**O que ficou:** uma linha **Fonte** com selos clicáveis sob cada resposta; ao clicar, abre a saída bruta da consulta (no caso do manual, o trecho, página a página).

## 9. Dados públicos sanitizados, originais fora do Git

**Escolha:** `data_public/` preserva catálogo, categorias, promoções e itens originais, e **substitui** nomes, telefones, e-mails, rastreios e notas por valores fictícios; o manual de 8 páginas é interno e fica fora do repositório (a pasta pública traz um PDF sintético de uma página). `data/` é ignorada pelo Git.
**Evidência:** uma busca por todos os valores pessoais originais (nomes, e-mails, telefones, rastreios, notas) na árvore versionada e nos blobs de texto do histórico não achou nenhum; nenhum PDF versionado é igual ao manual original.
**Limite:** os testes com o modelo usam o PDF sintético; o desempenho com o manual original foi verificado só na busca local, não com o modelo.
