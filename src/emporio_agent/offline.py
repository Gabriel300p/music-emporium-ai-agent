"""Rule-based store assistant that answers WITHOUT a language model, using the same read-only tools.

It exists so the project can be explored without API credentials. It is not an LLM and does not demonstrate model
quality: intent is detected with keyword rules and every answer is a template filled with data from the tools.
"""
from __future__ import annotations

import re
from pathlib import Path

from .policies import PolicyIndex, load_policies, terms
from .store import CATEGORY_ALIASES, CSVStore, GuardedStore, price_number, textnorm

GREETING_TOKENS = {"oi", "ola", "opa", "eai", "salve"}
GREETING_PHRASES = ("bom dia", "boa tarde", "boa noite", "tudo bem", "e ai")
THANKS_STEMS = ("obrigad", "valeu", "agradec")
RETURN_STEMS = ("devol", "arrepend", "troca", "trocar")
ORDER_STEMS = ("pedido", "rastreio", "rastrear", "rastreamento")
POLICY_STEMS = ("horario", "endereco", "funciona", "pagament", "pagar", "cartao", "parcel", "boleto", "frete", "entrega", "prazo",
                "garantia", "contato", "telefone", "whatsapp", "privacidade", "lgpd", "defeito", "retirada", "retirar")
POLICY_WORDS = {"abre", "abrem", "fecha", "onde", "fica", "pix", "credito", "debito"}
ACCESSORY_STEMS = ("cabo", "palheta", "amplificador", "pedal", "acessor", "capa", "afinador", "suporte")
PRODUCT_WORDS = {"preco", "valor", "custa", "custam", "estoque", "disponivel", "disponiveis"}
STATUS_PT = {
    "pending": "pendente, aguardando confirmação",
    "confirmed": "confirmado",
    "shipped": "enviado",
    "delivered": "entregue",
    "cancelled": "cancelado",
}
AVAILABILITY_PT = {
    "in_stock": "em estoque",
    "out_of_stock": "esgotado no momento",
    "discontinued": "descontinuado",
    "coming_soon": "ainda não foi lançado",
    "unknown": "sem informação de estoque",
}
MAX_ITEMS = 5
FOLLOW_UP = "Posso ajudar com mais alguma coisa?"


def brl(value: float | int | None) -> str:
    if value is None:
        return "preço indisponível"
    return "R$ " + f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def br_date(value: str | None) -> str:
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", value or "")
    return f"{match.group(3)}/{match.group(2)}/{match.group(1)}" if match else (value or "")


def best_sentences(text: str, question: str, limit: int = 3) -> list[str]:
    """The sentences of `text` that share the most terms with the question, kept in their original order."""
    wanted = set(terms(question))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    scored = [(len(wanted & set(terms(sentence))), index, sentence) for index, sentence in enumerate(sentences)]
    top = sorted((row for row in scored if row[0] > 0), key=lambda row: (-row[0], row[1]))[:limit]
    return [sentence for _, _, sentence in sorted(top, key=lambda row: row[1])]


def _has_stem(tokens: set[str], stems: tuple[str, ...]) -> bool:
    return any(token.startswith(stem) for token in tokens for stem in stems)


def _availability(product: dict) -> str:
    return AVAILABILITY_PT.get(product["availability"], product["availability"])


class OfflineAgent:
    def __init__(self, data_dir: str | Path, *, store: CSVStore | None = None, policies: PolicyIndex | None = None):
        self.store = GuardedStore(store if store is not None else CSVStore(data_dir))
        self.policies = policies if policies is not None else load_policies(data_dir)
        self.pending_order: str | None = None
        self._vocabulary: set[str] | None = None

    # ------------------------------------------------------------------ entry point
    def reply(self, message: str) -> tuple[str, list[dict[str, str]]]:
        q = textnorm(message)
        tokens = set(q.split())
        trace: list[dict[str, str]] = []

        if self.pending_order and "@" in message:
            return self._order(message, q, trace)
        if _has_stem(tokens, RETURN_STEMS):
            return self._policy(message, trace, "Sobre troca e devolução, o manual da loja diz:")
        if _has_stem(tokens, ORDER_STEMS):
            return self._order(message, q, trace)
        if _has_stem(tokens, ACCESSORY_STEMS):
            return ("Por aqui trabalhamos só com instrumentos musicais, então não vendemos acessórios como cabos, palhetas, amplificadores "
                    "ou pedais. Posso te ajudar a encontrar um instrumento, ver promoções ou consultar um pedido?"), trace
        if "promoc" in q or "descontos ativos" in q:
            return self._promotions(trace)
        if _has_stem(tokens, POLICY_STEMS) or tokens & POLICY_WORDS:
            return self._policy(message, trace, "Pelo manual de políticas da loja:")
        category, query = self._product_filters(tokens)
        if category or query or tokens & PRODUCT_WORDS:
            return self._products(message, q, category, query, trace)
        if tokens & GREETING_TOKENS or any(phrase in q for phrase in GREETING_PHRASES):
            return ("Olá! Eu sou o atendente virtual da Empório da Música. Posso ajudar com preço e estoque de instrumentos, "
                    "promoções, o andamento do seu pedido e as regras de troca, pagamento e entrega. Como posso ajudar?"), trace
        if _has_stem(tokens, THANKS_STEMS):
            return "Por nada! Se precisar de mais alguma coisa, é só chamar.", trace
        return ("Esse assunto foge do que consigo ajudar por aqui. Sou o atendente virtual da Empório da Música, uma loja de "
                "instrumentos musicais, e posso falar de preços, estoque e promoções, do andamento de um pedido e das regras da loja, "
                "como troca, pagamento e horário. O que você gostaria de saber?"), trace

    # ------------------------------------------------------------------ orders
    def _order(self, message: str, q: str, trace: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
        match = re.search(r"(?:pedido|numero)\s*(?:n[ºo] ?)?#?\s*(\d+)", q)
        email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", message)
        number = match.group(1) if match else self.pending_order
        if not number:
            return "Claro! Para consultar um pedido, me diga o número dele e o e-mail usado na compra.", trace
        if not email:
            self.pending_order = number
            return f"Claro! Para consultar o pedido {number}, preciso do e-mail usado na compra. Pode me informar?", trace
        self.pending_order = None
        result = self.store.order_status(order_number=number, customer_email=email.group(0))
        trace.append({"tool": "order_status", "status": result["status"]})
        if result["status"] == "locked":
            return result["message"], trace
        if result["status"] != "verified":
            return ("Não consegui confirmar este pedido com esses dados, e por segurança não posso apresentar nenhuma informação dele. "
                    "Confira o número do pedido e o e-mail usado na compra e tente de novo, ou fale com a equipe da loja."), trace
        status = STATUS_PT.get(result["order_status"], result["order_status"])
        lines = [f"Encontrei o pedido {result['order_number']}: ele está **{status}**."]
        if result["tracking_code"]:
            lines.append(f"- Código de rastreio: {result['tracking_code']}")
        if result["estimated_delivery"]:
            lines.append(f"- Previsão de entrega: {br_date(result['estimated_delivery'])}")
        for item in result["items"]:
            lines.append(f"- {item['quantity']}× {item['name']}")
        lines.append("Estas informações vêm do arquivo da loja, não de uma consulta em tempo real. " + FOLLOW_UP)
        return "\n".join(lines), trace

    # ------------------------------------------------------------------ promotions
    def _promotions(self, trace: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
        result = self.store.search_promotions()
        trace.append({"tool": "search_promotions", "status": result["status"]})
        if result["status"] != "ok" or not result["products"]:
            return "No momento não encontrei promoções ativas confirmadas nos dados da loja. Quer que eu procure algum produto específico?", trace
        shown = result["products"][:MAX_ITEMS]
        lines = ["Estas são as promoções ativas que encontrei:"]
        lines += [
            f"- **{p['name']}**: de {brl(p['regular_price_brl'])} por **{brl(p['current_price_brl'])}** (-{p['promotion_discount_percent']:g}%)"
            for p in shown
        ]
        if result["matches"] > len(shown):
            lines.append(f"Tenho mais {result['matches'] - len(shown)} promoções, é só pedir.")
        policy = self.policies.search("O desconto PIX acumula com promoções?")
        trace.append({"tool": "search_policies", "status": policy["status"]})
        page = next((p["page"] for p in policy.get("results", []) if "nao" in textnorm(p["excerpt"]) and "promoc" in textnorm(p["excerpt"])), None)
        lines.append("O desconto de PIX não se soma às promoções" + (f" (Manual, p. {page})." if page else "."))
        lines.append("Quer detalhes de algum desses instrumentos?")
        return "\n".join(lines), trace

    # ------------------------------------------------------------------ store policies
    def _policy(self, message: str, trace: list[dict[str, str]], intro: str) -> tuple[str, list[dict[str, str]]]:
        result = self.policies.search(message)
        trace.append({"tool": "search_policies", "status": result["status"]})
        for hit in result.get("results", []):
            sentences = best_sentences(hit["excerpt"], message, 3)
            if sentences:
                body = " ".join(sentences)
                return (f"{intro}\n\n{body} (Manual, p. {hit['page']})\n\nPara casos específicos, a equipe da loja confirma os detalhes. "
                        f"{FOLLOW_UP}"), trace
        return ("Não encontrei essa informação no manual da loja e prefiro não arriscar uma resposta. "
                "Posso passar para a equipe de atendimento, ou ajudar com preços, estoque e pedidos?"), trace

    # ------------------------------------------------------------------ catalogue
    def _vocab(self) -> set[str]:
        if self._vocabulary is None:
            rows = self.store.products.rows if self.store.products else []
            words = {w for row in rows for w in textnorm(row.get("name", "")).split() if len(w) > 1 and not w.isdigit()}
            self._vocabulary = words
        return self._vocabulary

    def _product_filters(self, tokens: set[str]) -> tuple[str | None, str | None]:
        category = next((t for t in sorted(tokens) if t in CATEGORY_ALIASES), None)
        named = sorted(tokens & self._vocab() - set(CATEGORY_ALIASES))
        return category, (" ".join(named) if named else None)

    def _products(self, message: str, q: str, category: str | None, query: str | None,
                  trace: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
        budget = re.search(r"(?:até|ate|abaixo de|menos de)\s*(?:R\$\s*)?(\d[\d.,]*)", message, re.IGNORECASE)
        parsed = price_number(budget.group(1)) if budget else None
        price_max = float(parsed) if parsed is not None else None
        result = self.store.search_products(query=query, category=category, max_price=price_max,
                                            in_stock_only=("dispon" in q or "estoque" in q))
        trace.append({"tool": "search_products", "status": result["status"]})
        if result["status"] != "ok" or not result["products"]:
            return "Não encontrei instrumentos com esses filtros nos dados da loja. Quer tentar outra faixa de preço ou outra categoria?", trace
        products = result["products"]
        if result["matches"] == 1:
            return self._one_product(products[0]), trace
        shown = products[:MAX_ITEMS]
        lines = [f"Claro! Encontrei {result['matches']} opções que atendem ao seu pedido:"]
        for p in shown:
            price = f"**{brl(p['current_price_brl'])}**"
            if p["promotion_discount_percent"]:
                price += f" (de {brl(p['regular_price_brl'])}, -{p['promotion_discount_percent']:g}%)"
            note = "" if p["availability"] == "in_stock" else f", {_availability(p)}"
            lines.append(f"- **{p['name']}** por {price}{note}")
        if result["matches"] > len(shown):
            lines.append(f"Tenho mais {result['matches'] - len(shown)} opções, é só pedir que eu mostro.")
        lines.append("Quer detalhes de algum modelo ou ver outra faixa de preço?")
        return "\n".join(lines), trace

    @staticmethod
    def _one_product(p: dict) -> str:
        text = f"O **{p['name']}** custa **{brl(p['current_price_brl'])}** e está {_availability(p)}"
        if p["availability"] == "in_stock" and p.get("stock_units") is not None:
            text += f" ({p['stock_units']} unidades)"
        text += "."
        if p["promotion_discount_percent"]:
            text += f" Ele está em promoção: de {brl(p['regular_price_brl'])}, com {p['promotion_discount_percent']:g}% de desconto, e o PIX não soma com a promoção."
        elif p.get("pix_price_brl_if_not_promotional"):
            text += f" No PIX sai por {brl(p['pix_price_brl_if_not_promotional'])}."
        return text + " Quer ver outros modelos?"
