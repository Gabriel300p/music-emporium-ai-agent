# Dados públicos (cópia sanitizada do caso)

Versão do material do desafio que pode ser publicada: roda o agente com a mesma estrutura de tabelas, **sem dados pessoais**. Não é o pacote original completo.

| Arquivo | Linhas | Origem e alterações |
|---|---:|---|
| `categories.csv` | 9 | Tabela original, sem campos de cliente |
| `products.csv` | 65 | Tabela original, sem campos de cliente |
| `promotions.csv` | 25 | Tabela original, sem campos de cliente |
| `order_items.csv` | 22 | Tabela original; identificadores mantidos para as junções |
| `customers.csv` | 50 | **Sanitizada:** nomes, telefones, e-mails e cidades trocados por valores fictícios; identificadores mantidos |
| `orders.csv` | 20 | **Sanitizada:** rastreios trocados por valores `DEMO`, notas livres removidas; identificadores mantidos |
| `políticas_da_loja.pdf` | 1 página | Documento **totalmente sintético**; não é o manual interno de 8 páginas |

O manual original e os dados pessoais **não** estão no histórico do Git. Esta cópia não contém todas as regras do manual real; a avaliação com o modelo usa o PDF sintético, o que está dito em [`docs/AVALIACAO.md`](../docs/AVALIACAO.md).

## Como usar

```bash
python -m emporio_agent inspect --data-dir data_public
python -m emporio_agent serve                # interface web; data_public é a fonte padrão
python -m emporio_agent chat --data-dir data_public --offline --trace
```

## Como reproduzir a sanitização

Com os CSVs originais na pasta local `data/` (ignorada pelo Git):

```bash
python scripts/prepare_public_data.py --source-dir data --out-dir data_public
```

O script usa pseudônimos determinísticos e confere chaves estrangeiras e a redação dos campos. Nunca versione `data/`, identidades de clientes, códigos de rastreio, chaves de API nem o PDF interno. A verificação de e-mail e número de pedido do protótipo **não** é autenticação forte.

Os pedidos e clientes desta pasta são dados de teste: valores de catálogo e de transações foram mantidos para que as consultas sejam realistas, mas nada aqui representa um sistema de negócio real.
