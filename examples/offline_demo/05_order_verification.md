# 05 Order Verification

> **Execution mode:** offline deterministic demonstration. **Data:** 100% synthetic `demo_data/`. This is NOT a live LLM response.

**Customer:** Qual o status do pedido 1001?

**Assistant:** Qual é o e-mail utilizado na compra? Preciso dele para verificar o pedido.

**Executed tools (name/status only):** []

**Customer:** Meu email é wrong@example.test

**Assistant:** Não consegui confirmar o número do pedido e o e-mail. Para sua segurança, não posso apresentar dados deste pedido.

**Executed tools (name/status only):** [{"tool": "order_status", "status": "not_verified"}]

**Customer:** Qual o status do pedido 1001?

**Assistant:** Qual é o e-mail utilizado na compra? Preciso dele para verificar o pedido.

**Executed tools (name/status only):** []

**Customer:** Meu email é ana@example.test

**Assistant:** Pedido 1001: status 'shipped'. Rastreamento cadastrado: DEMO0001. Previsão registrada: 2026-10-10. Informações do arquivo local, não de uma consulta em tempo real.

**Executed tools (name/status only):** [{"tool": "order_status", "status": "verified"}]
