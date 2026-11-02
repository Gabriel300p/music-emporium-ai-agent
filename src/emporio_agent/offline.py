"""Small no-LLM demonstration of the SAME read-only business tools.

This is not the production assistant or an LLM accuracy test. It exists to make
reproducible end-to-end demonstrations possible without API credentials.
"""
from __future__ import annotations

import re
from pathlib import Path

from .policies import PolicyIndex, load_policies
from .store import CSVStore, textnorm, price_number


def brl(value: float | int | None) -> str:
    if value is None:
        return "preço indisponível"
    return "R$ " + f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


class OfflineAgent:
    def __init__(self, data_dir: str | Path, *, store: CSVStore | None = None, policies: PolicyIndex | None = None):
        self.store = store if store is not None else CSVStore(data_dir)
        self.policies = policies if policies is not None else load_policies(data_dir)
        self.pending_order: str | None = None

    def reply(self, message: str) -> tuple[str, list[dict[str, str]]]:
        q = textnorm(message)
        trace: list[dict[str, str]] = []
        if any(word in q for word in ("pedido", "rastreio", "rastrear")) or (self.pending_order and "@" in message):
            match = re.search(r"(?:pedido|numero)\s*(?:n[ºo] ?)?#?\s*(\d+)", q)
            email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", message)
            number = match.group(1) if match else self.pending_order
            if not number:
                return "Para consultar seu pedido, me diga o número do pedido e o e-mail usado na compra.", trace
            if not email:
                self.pending_order = number
                return "Qual é o e-mail utilizado na compra? Preciso dele para verificar o pedido.", trace
            self.pending_order = None
            result = self.store.order_status(order_number=number, customer_email=email.group(0))
            trace.append({"tool": "order_status", "status": result["status"]})
            if result["status"] != "verified":
                return "Não consegui confirmar o número do pedido e o e-mail. Para sua segurança, não posso apresentar dados deste pedido.", trace
            details = f"Pedido {result['order_number']}: status '{result['order_status']}'."
            if result["tracking_code"]:
                details += f" Rastreamento cadastrado: {result['tracking_code']}."
            if result["estimated_delivery"]:
                details += f" Previsão registrada: {result['estimated_delivery']}."
            return details + " Informações do arquivo local, não de uma consulta em tempo real.", trace

        if "promoc" in q or "descontos ativos" in q:
            result = self.store.search_promotions()
            trace.append({"tool": "search_promotions", "status": result["status"]})
            if result["status"] != "ok" or not result["products"]:
                return "Não encontrei promoções ativas confirmadas nos dados disponíveis.", trace
            lines = [f"{p['name']}: {brl(p['regular_price_brl'])} → {brl(p['current_price_brl'])} ({p['promotion_discount_percent']:g}% OFF)." for p in result["products"]]
            policy = self.policies.search("O desconto PIX acumula com promoções?")
            trace.append({"tool": "search_policies", "status": policy["status"]})
            page = next((p["page"] for p in policy.get("results", []) if "nao" in textnorm(p["excerpt"]) and "promoc" in textnorm(p["excerpt"])), None)
            policy_note = f" (Manual, p. {page})." if page else "."
            return "O arquivo local marca estas promoções como ativas:\n" + "\n".join(lines) + "\nO desconto PIX não é cumulativo com promoções" + policy_note, trace

        if "devol" in q or "arrepend" in q or "troca" in q:
            result = self.policies.search(message)
            trace.append({"tool": "search_policies", "status": result["status"]})
            hit = next((x for x in result.get("results", []) if "7 (sete)" in x["excerpt"] or "7 dias" in x["excerpt"]), None)
            if hit:
                return ("Conforme o manual, compras online podem ser devolvidas por arrependimento em até 7 dias corridos após o recebimento. "
                        "Existem condições de embalagem e conservação; a equipe precisa confirmar seu caso. "
                        f"(Manual, p. {hit['page']})."), trace
            return "Não localizei uma regra suficiente no manual disponível. Consulte a equipe.", trace

        if "horario" in q or "endereco" in q or "abre" in q:
            result = self.policies.search(message)
            trace.append({"tool": "search_policies", "status": result["status"]})
            if result.get("results"):
                return "As informações oficiais de horário e endereço estão no manual consultado. " \
                       + "Confira o trecho da página " + str(result["results"][0]["page"]) + " antes de confirmar. (Modo offline limitado.)", trace
            return "Não consegui confirmar o funcionamento da loja.", trace

        if "viol" in q or "takamine" in q or "yamaha" in q or "guitarr" in q or "quanto custa" in q:
            budget = re.search(r"(?:até|ate|abaixo de|menos de)\s*(?:R\$\s*)?(\d[\d.,]*)", message, re.IGNORECASE)
            parsed = price_number(budget.group(1)) if budget else None
            price_max = float(parsed) if parsed is not None else None
            category = "violões" if "viol" in q else "guitarras" if "guitarr" in q else None
            query = "Takamine GD20" if "takamine gd20" in q else "Yamaha" if "yamaha" in q else None
            result = self.store.search_products(query=query, category=category, max_price=price_max, in_stock_only=("dispon" in q or "estoque" in q))
            trace.append({"tool": "search_products", "status": result["status"]})
            if result["status"] != "ok" or not result["products"]:
                return "Não encontrei instrumentos que atendam a esses filtros no arquivo local.", trace
            lines = []
            for p in result["products"]:
                status = "em estoque" if p["availability"] == "in_stock" else p["availability"]
                price = brl(p["current_price_brl"])
                if p["promotion_discount_percent"]:
                    price += f" (antes {brl(p['regular_price_brl'])}, -{p['promotion_discount_percent']:g}%)"
                lines.append(f"- {p['name']}: {price}, {status}")
            suffix = f"\n(Exibindo {len(lines)} de {result['matches']} registros.)" if result["truncated"] else ""
            return "Estas são as opções no catálogo local:\n" + "\n".join(lines) + suffix, trace

        return "Este canal atende assuntos sobre instrumentos musicais da Empório da Música. Posso ajudar com o catálogo, compras e políticas da loja.", trace
