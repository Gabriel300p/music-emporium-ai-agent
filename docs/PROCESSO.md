# Como este projeto foi construído

> Texto em primeira pessoa, redigido com apoio do Claude Code a partir do histórico real do trabalho. Cada afirmação sobre decisões e sobre o que foi encontrado corresponde a algo que aconteceu e pode ser verificado nos commits, nos testes ou nos números de [`AVALIACAO.md`](AVALIACAO.md).

## Em resumo

O enunciado pedia um agente que decida quando consultar dados e quando consultar políticas. O primeiro código veio do ChatGPT, de uma vez. O meu trabalho foi **auditar esse código com medições, decidir o que manter e o que mudar, e transformá-lo em algo que qualquer pessoa consiga testar**, sem me apropriar de decisões que o assistente tomou antes de eu revisá-las.

## Quem fez o quê

| Parte | ChatGPT | Claude Code (sob minha direção) | Eu |
|---|:--:|:--:|:--:|
| Código inicial: ferramentas, busca de políticas, laço do agente, CLI, testes, dados de demonstração | ● | | revisão posterior |
| Auditoria independente: testes, integridade das tabelas, regras de desconto, privacidade, busca de políticas | | ● | direção, leitura dos resultados |
| Bateria de avaliação com o modelo real e análise dos resultados | | ● | autorização de gasto, escolha dos cenários críticos |
| Interface web, lançador de um comando, streaming, otimizações | | ● | escopo, decisões de produto, **testes manuais** |
| Estratégia, prioridades, o que entra e o que sai | | | ● |
| Documentação | ● (versão inicial) | ● (versão atual) | revisão e aprovação |

## Linha do tempo (02/11/2026)

| Quando | O que | Commits |
|---|---|---|
| 11:22 a 11:23 | Baseline inteiro gerado pelo ChatGPT e commitado em seguida | 5 |
| 11:38 a 14:47 | Nome do projeto, dados públicos sanitizados com script e testes, primeiros documentos de decisão | 3 |
| 15:05 a 15:26 | Documentação do processo de desenvolvimento assistido por IA | 6 |
| Tarde | **Auditoria independente** (relatório privado) e primeira bateria com o modelo real | |
| 17:28 | Interface web, lançador, ajuste de prompt e bateria no repositório | 3 |
| 18:58 | Streaming, dados compartilhados, índice de políticas, conexão mantida, interface redesenhada | 2 |
| Noite | Regras finais de prompt (pedido e descontinuado), exemplos regravados, consolidação dos documentos | |

**Sobre o histórico.** Os 5 primeiros commits foram feitos em 90 segundos, porque o baseline foi gerado de uma vez e commitado em seguida. Não reescrevi o histórico. O trabalho posterior está em commits incrementais, cada um dizendo o que mudou e por quê.

## O que a medição e o teste manual encontraram

| # | Problema | Como apareceu | Causa | Correção | Proteção para não voltar |
|---|---|---|---|---|---|
| 1 | O pedido não era consultado **depois de outra pergunta** (0 de 6 execuções) | Meu teste manual na interface; reproduzido pelo mesmo caminho | O modelo ignorava o número do pedido quando já havia histórico. A bateria só testava conversa nova | Exemplo explícito no prompt: 32 de 32 em 4 contextos | 3 cenários multi-turno na bateria |
| 2 | Uma instrução de formato derrubou o pedido de 9/10 para 2/10 | Comparando o prompt antigo e o novo em 10 repetições | "Termine com uma pergunta de acompanhamento" fazia o modelo perguntar em vez de consultar | Instrução removida; formato só na resposta final | Regra: mudança de prompt só entra comparada ao anterior, em várias repetições |
| 3 | Botões sem efeito na interface | Meu teste manual | Texto truncado antes de chegar à tela; um ouvinte de "clique fora" fechava o menu no mesmo clique | Corrigidos | Testes que **clicam** nos botões, não só conferem que existem |
| 4 | Informação repetida na tela (lista no texto e a mesma lista em cartões) | Revisão da tela, a partir da minha captura | Duas fontes mostrando o mesmo dado | Cartões removidos (decisão 8 em [`DECISOES.md`](DECISOES.md)) | |
| 5 | Resposta lenta | Meu uso local | Duas chamadas em série e, na minha rede, custo de abrir a conexão | Dados e conexão reaproveitados, aquecimento em segundo plano; medição por chamada na tela | Painel com o tempo de cada chamada |
| 6 | Chamadas indo para um proxy herdado do ambiente | Aviso na tela ao integrar a interface | A variável `OPENAI_BASE_URL` do ambiente redirecionava o endpoint | Variável ignorada; só `--base-url` muda o endpoint | Teste dedicado |
| 7 | Dois clientes de API criados ao mesmo tempo (aquecimento × primeira pergunta) | Revisão ao implementar o aquecimento | Corrida entre duas *threads* | Trava na criação do cliente | Suíte repetida 3 vezes sem falha |
| 8 | O modelo dizia que o e-mail "não corresponde" ao pedido **sem consultar a ferramenta** (0 de 10) | Leitura crítica do exemplo regravado | Com um e-mail que parecia falso, o modelo julgava sozinho | Regra no prompt: só a ferramenta sabe se confere; 10 de 10 | 2 cenários novos na bateria |
| 9 | A regra nova de pedido enfraqueceu a do produto descontinuado (10/10 para 5/10) | Bateria de controle depois da mudança | Prompt mais longo diluiu a instrução anterior | Regra reforçada ("OBRIGATÓRIO"): 10 de 10 | Regra: depois de mexer no prompt, rodar a bateria inteira, não só o cenário alvo |

Dois dos achados (1 e 3) vieram de testes **manuais** e o 8 da leitura de um exemplo gravado, não da avaliação automática: um limite conhecido de qualquer rubrica escrita pelo próprio autor. O 9 mostra o outro lado: a bateria só serviu porque foi rodada inteira depois de cada mudança.

## Decisões que tomei

- **Estratégia:** equilíbrio entre engenharia confiável e IA aplicada, sem aumentar a complexidade só para mostrar tecnologia.
- **Qualidade medida antes de mudar:** chamadas reais ao modelo, com teto de gasto definido por mim, e só sobre dados públicos.
- **Produto:** interface web local sem dependência nova; dados públicos por padrão e originais só por escolha explícita; chave colada na tela; um comando para instalar e abrir.
- **Interface:** tema escuro, painel redimensionável, progresso em tempo real, texto em streaming; **cartões testados e removidos**.
- **Ordem do trabalho:** velocidade e clareza das respostas antes da documentação final.

## Contexto

Já exploro orquestração de agentes em um projeto pessoal separado (Pandora). Isso influenciou as perguntas que fiz ao projeto (ferramentas controladas, evidência, falhas observáveis), mas **nenhum código dele foi reaproveitado aqui**.

## Limites

Não afirmo que escrevi o código inicial, que o modelo é o melhor para este caso (só medi latência entre modelos, não acertos) nem que a avaliação cobre o manual original de 8 páginas com o modelo real. O que está documentado é o que foi executado.
