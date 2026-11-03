# 05 Order Verification

> **Execution mode:** offline deterministic demonstration. **Data:** 100% synthetic `demo_data/`. This is NOT a live LLM response.

**Customer:** Qual o status do pedido 1001?

**Assistant:** Claro! Para consultar o pedido 1001, preciso do e-mail usado na compra. Pode me informar?

**Executed tools (name/status only):** []

**Customer:** Meu email é wrong@example.test

**Assistant:** Não consegui confirmar este pedido com esses dados, e por segurança não posso apresentar nenhuma informação dele. Confira o número do pedido e o e-mail usado na compra e tente de novo, ou fale com a equipe da loja.

**Executed tools (name/status only):** [{"tool": "order_status", "status": "not_verified"}]

**Customer:** Qual o status do pedido 1001?

**Assistant:** Claro! Para consultar o pedido 1001, preciso do e-mail usado na compra. Pode me informar?

**Executed tools (name/status only):** []

**Customer:** Meu email é ana@example.test

**Assistant:** Encontrei o pedido 1001: ele está **enviado**.
- Código de rastreio: DEMO0001
- Previsão de entrega: 10/10/2026
- 1× Violão Escola C30 Demo
Estas informações vêm do arquivo da loja, não de uma consulta em tempo real. Posso ajudar com mais alguma coisa?

**Executed tools (name/status only):** [{"tool": "order_status", "status": "verified"}]
