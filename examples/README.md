# Exemplos de conversa

## Conversas reais com o modelo (as 5 pedidas no desafio)

Gravadas em 2026-11-02 com o agente final (`gpt-4.1-mini`, OpenAI Responses API), o modelo decidindo sozinho quais ferramentas chamar. Usam só `data_public/`: clientes anonimizados e um manual de políticas **sintético** de uma página. Cada arquivo diz o modelo, a data, as ferramentas executadas e o uso real de tokens e de tempo.

| Arquivo | O que mostra | Ferramentas |
|---|---|---|
| [`real_01_preco_do_modelo.md`](real_01_preco_do_modelo.md) | Preço do Takamine GD20, com o preço no PIX | `search_products` |
| [`real_02_faixa_de_preco.md`](real_02_faixa_de_preco.md) | Violões disponíveis até R$ 1.000, no máximo 5 itens e aviso de que há mais | `search_products` |
| [`real_03_promocao_e_pix.md`](real_03_promocao_e_pix.md) | **Caso não trivial:** promoção do catálogo e regra de que o desconto de PIX não soma com ela | `search_products`, `search_promotions` |
| [`real_04_arrependimento_de_compra.md`](real_04_arrependimento_de_compra.md) | Devolução por arrependimento, com a página do manual citada | `search_policies` |
| [`real_05_status_de_pedido.md`](real_05_status_de_pedido.md) | Pedido: e-mail errado primeiro (a ferramenta nega), depois o correto | `order_status` |

**Como ler:** são amostras de uma execução, não uma medição. A medição está em [`docs/AVALIACAO.md`](../docs/AVALIACAO.md) e em `scripts/eval_live.py`. O manual usado aqui é o sintético; no manual original a regra de devolução está na página 4, e o exemplo 4 cita a página 1 porque o documento de teste tem uma só.

Para gerar conversas novas, use a interface (`./run.sh`) e o botão **Exportar .md**.

## Demonstração offline, sem API (`offline_demo/`)

Cinco conversas geradas pelo agente por regras (sem modelo de linguagem) sobre dados 100% sintéticos de `demo_data/`. Servem para rodar o projeto sem chave e **não representam respostas do modelo**. Para regerar:

```bash
python scripts/record_examples.py --data-dir demo_data --out-dir examples/offline_demo
```
