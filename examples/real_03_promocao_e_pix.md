# Exemplo real 3 · Promoção e regra do PIX (caso não trivial)

> **Execução: LLM real** (`gpt-4.1-mini`, OpenAI Responses API) em 2026-11-02 19:21. Não é simulação.
> **Dados:** `data_public/` (clientes anonimizados; o manual de políticas desta pasta é um documento **sintético** de uma página, com endereço e horário fictícios).
> **O que mostra:** caso não trivial. O preço promocional vem do catálogo (calculado com `Decimal`) e a regra de que o desconto de PIX **não** soma com promoção está embutida no cálculo em Python, não no texto do modelo.
> **Uso:** 2 chamadas · 3219 tokens de entrada · 143 de saída · 5.7 s.

**Cliente:** O violão Crafter HT-100 está em promoção? Se eu pagar no PIX, ganho mais algum desconto?

**Assistente:** O violão Crafter HT-100 Folk Aço Natural está em promoção com preço por R$ 1967,18, que é um desconto de 18% sobre o preço original de R$ 2399,00. O desconto do PIX de 5% não é acumulativo com essa promoção. Quer que eu veja outras opções de violões em promoção para você?

**Ferramentas executadas (nome/status):** [{"tool": "search_products", "status": "ok"}, {"tool": "search_promotions", "status": "ok"}]
