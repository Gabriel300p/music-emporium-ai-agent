# Segurança e tratamento de dados

O que o projeto faz para não vazar dados e o que **não** faz. Os resultados de teste vêm da bateria descrita em [`AVALIACAO.md`](AVALIACAO.md).

## Dados

| Regra | Como é cumprida |
|---|---|
| Nenhum dado pessoal original no repositório | `data/` é ignorada pelo Git. `data_public/` mantém catálogo, categorias, promoções e itens, e **substitui** nomes, telefones, e-mails, rastreios e notas por valores fictícios (`scripts/prepare_public_data.py`, com testes) |
| O manual interno não é publicado | O PDF de 8 páginas fica só em `data/`. A pasta pública traz um PDF sintético de uma página |
| Conferência do que já foi publicado | Busca por todos os valores pessoais originais na árvore versionada e nos blobs de texto do histórico: **0 ocorrências**; nenhum PDF versionado é igual ao manual original |
| Chave de API fora do Git | `.env` é ignorado; os exemplos usam valores de teste que não são credenciais |

## O que o modelo vê e pode fazer

- O modelo **não** executa SQL, Python, comandos nem escrita de arquivos: só chama 4 funções de leitura com parâmetros validados.
- Ele recebe a mensagem do cliente e o resultado das ferramentas: produtos, trechos do manual e, para pedido verificado, status, rastreio, previsão e itens. **Nome, telefone e e-mail do cliente nunca são devolvidos** nos dados de pedido.
- Se a pessoa escolher a fonte de **dados originais** na interface em modo Modelo real, trechos do manual interno e dados de pedidos reais seguem para a API da OpenAI. A tela avisa disso. No modo Offline nada sai da máquina.
- As chamadas usam `store=False`; a retenção pelo provedor depende das políticas dele.
- O conteúdo dos arquivos e as saídas das ferramentas são tratados como **dado não confiável** no prompt.

## Pedidos

O pedido só é consultado com **número e e-mail da compra** juntos; um par errado e um pedido inexistente recebem a mesma negação, o que não revela se o pedido existe. Na bateria: e-mail errado negado em 3 de 3 e nenhum dado liberado sem o e-mail.

**Limite de tentativas.** Antes, 2.000 verificações erradas eram processadas em 0,06 s. Agora, depois de **3 pares errados seguidos**, a conversa é bloqueada: a ferramenta deixa de consultar a tabela, mesmo para o e-mail certo, e o cliente é encaminhado à equipe. Um acerto zera o contador e um pedido sem e-mail não conta como tentativa. O contador vive **por conversa** (a tabela é compartilhada e só leitura), cobre também o modo offline e aparece no painel de consultas. Com o modelo real: com 3 falhas reais, nada do pedido foi revelado em 10 de 10 repetições.

**Isto continua não sendo autenticação de produção.** Os números de pedido são sequenciais e o limite é por conversa, não por cliente nem por origem: abrir uma nova conversa zera o contador. Em produção, exigiria conta autenticada ou verificação por código.

## Injeção de prompt e extração

Testados com o modelo real, 3 de 3 em cada: pedido direto do prompt do sistema e dos e-mails de clientes, engenharia social ("sou da equipe da loja"), e **instrução escondida no nome de um produto** (o preço correto foi mantido e o e-mail injetado não apareceu). Isso mostra o comportamento observado em uma amostra pequena, **não** uma garantia.

## Interface web

- Escuta só em `127.0.0.1`. Rejeita `Host` e `Origin` de outros endereços (contra rebinding de DNS e requisições de outras páginas), aceita só JSON, limita o corpo a 64 KB e a mensagem a 2.000 caracteres, e guarda no máximo 20 conversas em memória.
- A chave colada na tela fica **só na memória**, é mascarada em mensagens de erro e nunca entra na conversa exportada. A resposta do modelo entra na página como **texto**, nunca como HTML.
- A variável `OPENAI_BASE_URL` do ambiente é ignorada; só `--base-url` muda o endpoint.
- Não há login nem persistência: é uma ferramenta de uso local, não um serviço para a internet.

## Antes de publicar qualquer coisa

Conferir `git status`, `git ls-files`, os exemplos e cada commit por valores identificáveis, códigos de rastreio e credenciais. Nunca versionar `data/`, os CSVs de clientes e pedidos originais, o PDF interno nem o `.env`.
