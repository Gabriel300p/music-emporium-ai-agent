# Avaliação

O que foi medido, como, e o que **não** foi. Cada número aqui vem de um comando que pode ser rodado de novo.

## Quatro camadas de evidência

| Camada | O que prova | Não prova |
|---|---|---|
| **1. Testes automáticos** (`pytest -q`, sem rede e sem chave) | Junções entre tabelas, desconto, privacidade de pedido, busca de políticas, servidor da interface, otimizações | Qualidade de resposta de nenhum modelo |
| **2. Demonstração offline** (`--offline`) | O fluxo ponta a ponta sem LLM, com regras simples | Comportamento do modelo |
| **3. Bateria com o modelo real** (`scripts/eval_live.py`) | Ferramenta escolhida, valores na resposta, privacidade, escopo e injeção, com `gpt-4.1-mini` | Qualidade de redação; outros modelos; o manual original de 8 páginas |
| **4. Sondagem da busca de políticas** | Em quantas paráfrases a página certa aparece | Respostas finais do modelo |

## 1. Testes automáticos

**69 passam e 13 são pulados** num clone público do repositório. Os 13 pulados exigem os arquivos originais privados (`data/`), que não são publicados; com eles disponíveis sob os nomes esperados, todos rodam.

| Arquivo | Testes | Cobre |
|---|---:|---|
| `test_web.py` | 41 | rotas, streaming, proteções (Host, Origin, tipo de conteúdo, tamanho), chave só em memória, exportação |
| `test_performance.py` | 8 | índice do manual idêntico ao algoritmo original, dados compartilhados, conexão e aquecimento |
| `test_case_dataset.py` | 13 | junções e regras com os dados originais (pulados no clone público) |
| `test_offline_demo.py`, `test_store.py`, `test_agent.py`, `test_policies.py`, `test_public_data.py` | 5 + 5 + 3 + 3 + 4 | demonstração offline, tabelas, laço do agente com cliente falso, busca, privacidade dos dados públicos |

## 2. Bateria com o modelo real

**Método:** 27 cenários, cada um repetido 3 vezes, sobre `data_public/` (clientes anonimizados e PDF sintético; **nada do manual interno nem de clientes originais vai à API**). Uma rubrica automática checa a ferramenta chamada e o conteúdo da resposta. Os cenários multi-turno testam o pedido no **meio** de uma conversa.

| Área | Cenários | Resultado |
|---|---|---|
| Dados | preço de um modelo, faixa de preço, promoção, PIX com promoção, produto descontinuado, produto inexistente | 3/3 em todos |
| Políticas | devolução, endereço e horário | 3/3 |
| Políticas por paráfrase | "Comprei pela internet e desisti, o que faço?" | 3/3 nesta rodada, **mas oscila** (veja abaixo) |
| Pedido | e-mail errado (2 formulações), pedido sem e-mail, 6 formulações do pedido com e-mail, 2 turnos, 3 cenários após outra pergunta | 3/3 em todos |
| Escopo | pergunta fora da loja, acessório que a loja não vende | 3/3 |
| Segurança | pedido do prompt e dos e-mails, engenharia social, instrução escondida no nome de um produto | 3/3 |
| **Total** | | **81 de 81** |

Em todas as execuções: nenhum dado pessoal vazou, nenhum preço foi inventado e nenhuma instrução injetada foi obedecida. Uma rodada completa usa cerca de 230 mil tokens.

### Evolução (o que a medição mudou)

| Etapa | Resultado | O que aconteceu |
|---|---|---|
| Prompt do baseline | 54 de 66 (22 cenários) | Falhas em pedido com número e e-mail na mesma frase (0/3), produto descontinuado descrito como "sem estoque" e paráfrase de política |
| Prompt de pedido e de descontinuado | 63 de 66 | Instruções explícitas sobre número curto de pedido e sobre dizer "descontinuado" |
| Instrução de formato visual (1ª versão) | pedido com e-mail caiu de **9/10 para 2/10** | Uma frase do prompt ("termine com uma pergunta de acompanhamento") fez o modelo perguntar em vez de consultar. Detectado ao comparar o prompt anterior e o novo em 10 repetições |
| Formato restrito à resposta final | pedido de volta a **10/10** | Instrução removida; formato só depois das consultas |
| Teste manual do autor | pedido falhava **depois de outra pergunta** (0 de 6) | A bateria só testava conversa nova. Corrigido com um exemplo explícito no prompt (**32 de 32** em 4 contextos) e 3 cenários multi-turno na bateria |
| Exemplo regravado com o agente final | e-mail errado **0 de 10** | O modelo respondia que o e-mail "não corresponde" **sem chamar a ferramenta**, uma verificação que ele não fez. Achado ao ler o exemplo gravado, que a bateria não pegava por usar outra frase. Regra no prompt ("só a ferramenta sabe se confere"): **10 de 10**, com 2 cenários novos |
| Regra nova diluiu outra | descontinuado de 10/10 para **5/10** | Um prompt mais longo enfraqueceu a regra do produto descontinuado. Regra reforçada com "OBRIGATÓRIO": **10 de 10** |
| **Atual** | **81 de 81** (27 cenários) | Mesmo assim, veja "Limites": dois cenários oscilam |

### Limites desta bateria

- Um modelo (`gpt-4.1-mini`), 3 repetições por cenário, manual sintético de uma página.
- A rubrica é automática e foi escrita pelo autor. Foi corrigida uma vez depois de ler as respostas: exigia o código de rastreio no texto e tratava como vazamento o e-mail que o próprio usuário digitou. Antes dessa correção, a primeira passada marcava 13 de 18.
- **Dois cenários oscilam entre rodadas.** A paráfrase de política depende do texto que o modelo manda para a busca lexical: de 0/3 a 3/3 em rodadas de 3, e de 4 a 9 acertos em rodadas de 10 repetições. O de produto descontinuado ficou entre 5/10 e 10/10 conforme o tamanho do prompt. **Um 81/81 não deve ser lido como garantia.**
- Mede regressão e comportamento observável; **não** mede qualidade de redação, tom nem custo em dólares.

## 3. Sondagem da busca de políticas

Em 17 perguntas parafraseadas sobre o manual original, com as páginas esperadas definidas pelo autor a partir do próprio manual: a página certa ficou **em 1º lugar em 10** e **entre as 3 primeiras em 14**; 3 voltaram vazias ("Vocês abrem aos domingos?", "Comprei pela internet e desisti", "Vocês vendem cabo e palheta?"). As 4 perguntas fora do escopo voltaram sem evidência, como deveriam. Amostra pequena e escrita pelo autor.

## 4. Desempenho

Medido com o modelo real e com perfil local; o que mudou está em [`DECISOES.md`](DECISOES.md) e nos testes.

| O que | Antes | Depois |
|---|---|---|
| Criar uma conversa nova (ler o PDF de 8 páginas) | 327 ms **por conversa** | lido **uma vez**; as demais ficam em microssegundos |
| `policies.search()` no manual de 8 páginas | 1,087 ms | 0,022 ms (ranking idêntico em 15 de 15 perguntas e em teste contra o algoritmo original) |
| Memória por conversa (tabelas + índice) | 134 KiB, duplicados | uma cópia compartilhada |
| 1ª pergunta após iniciar o programa | 2,0 a 2,35 s | 1,74 a 1,77 s (conexão e dados aquecidos) |
| Conexão ociosa com a API | fechada após 5 s (padrão do SDK) | mantida por 120 s |

**Onde está o tempo.** Cada resposta custa **duas chamadas seguidas** à API (uma para o modelo escolher a fonte, outra para escrever o texto), de 0,8 a 1,4 s cada no ambiente de desenvolvimento (um sandbox com proxy de rede): 1,7 a 3,2 s por resposta. Cada ferramenta local leva menos de 3 ms. Trocar de modelo não mudou a ordem de grandeza (2,24 s, 2,27 s e 1,91 s por resposta). Ao rodar o programa na própria máquina, o autor observou **5 a 10 s** por resposta, com a primeira chamada de cada pergunta levando cerca de 6 s e a segunda cerca de 1,5 s; isso é compatível com custo de abertura de conexão na rede local, e a causa ainda não foi confirmada. O painel da interface mostra o tempo de cada chamada para separar as causas.

**O que não foi otimizado, de propósito:** podar o histórico (pouco ganho de tempo e risco para a qualidade) e responder preço sem a segunda chamada (cortaria a espera, mas perderia a persona e mudaria a arquitetura).

## Como reproduzir

```bash
pytest -q                                              # camada 1
python scripts/eval_live.py --rep 3                    # camada 3: usa a sua chave e gasta tokens (~230 mil)
python scripts/eval_live.py --only S07_pedido_ok --rep 10
```

A chave vem de `OPENAI_API_KEY` ou de um `.env` local. O resultado completo é gravado em `eval_results.json` (ignorado pelo Git).
