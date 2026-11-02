# Exemplo real 5 · Status de pedido com verificação de e-mail

> **Execução: LLM real** (`gpt-4.1-mini`, OpenAI Responses API) em 2026-11-02 19:21. Não é simulação.
> **Dados:** `data_public/` (clientes anonimizados; o manual de políticas desta pasta é um documento **sintético** de uma página, com endereço e horário fictícios).
> **O que mostra:** Verificação de identidade antes de revelar o pedido (e-mail errado, depois o correto).
> **Uso:** 4 chamadas · 5179 tokens de entrada · 118 de saída · 3.2 s.

**Cliente:** Qual o status do pedido 8? Meu e-mail é outra.pessoa@example.com

**Assistente:** Não consegui verificar o pedido com esse e-mail. Se quiser, posso ajudar com outras informações ou você pode tentar outro e-mail.

**Ferramentas executadas (nome/status):** [{"tool": "order_status", "status": "not_verified"}]

**Cliente:** Desculpe, o e-mail certo é customer002@example.test

**Assistente:** Seu pedido 8 foi enviado e contém um Kala KA-C Concert Mogno. A entrega está prevista para até 28/02/2026. Posso ajudar com mais alguma coisa?

**Ferramentas executadas (nome/status):** [{"tool": "order_status", "status": "verified"}]
