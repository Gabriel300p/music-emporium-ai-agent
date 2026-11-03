"""Read-only, deterministic queries over the supplied relational CSV snapshots.

Original joins, validated against the challenge dataset:
products.category_id -> categories.category_id
promotions.product_id -> products.product_id
orders.customer_id -> customers.customer_id
order_items.order_id -> orders.order_id
order_items.product_id -> products.product_id

Nothing writes to source data. Personal customer fields are never returned by tools.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def textnorm(value: Any) -> str:
    return norm(value).replace("_", " ")


def price_number(value: Any) -> Decimal | None:
    if value is None:
        return None
    s = re.sub(r"[^0-9,.\-]", "", str(value).strip())
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s and re.fullmatch(r"\d{1,3}(?:\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def amount(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def quantity(value: Any) -> int | None:
    s = norm(value)
    if s in {"true", "yes", "sim", "disponivel", "em_estoque"}:
        return 1
    if s in {"false", "no", "nao", "indisponivel", "esgotado"}:
        return 0
    try:
        return int(float(str(value).replace(",", ".")))
    except (TypeError, ValueError, OverflowError):
        return None


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def first(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(norm(key), "")
        if str(value).strip():
            return str(value).strip()
    return ""


def read_csv(path: Path) -> Table:
    raw = None
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            raw = path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        raise ValueError(f"Could not decode {path.name}")
    try:
        dialect = csv.Sniffer().sniff(raw[:4096], delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if raw[:4096].count(";") > raw[:4096].count(",") else ","
    reader = csv.DictReader(raw.splitlines(), delimiter=delimiter)
    if not reader.fieldnames:
        return Table(path.stem, (), ())
    mapping = {key: norm(key) for key in reader.fieldnames if key is not None}
    rows = []
    for row in reader:
        if not row or not any(str(v or "").strip() for v in row.values()):
            continue
        rows.append({mapping[key]: str(value or "").strip() for key, value in row.items() if key in mapping})
    return Table(path.stem, tuple(mapping.values()), tuple(rows))


# Portuguese morphological variants: "violão" vs "violões" cannot be matched with
# simple substring logic, so canonicalize user category requests before matching.
CATEGORY_ALIASES = {
    "violao": "viol", "violoes": "viol", "viol": "viol",
    "guitarra": "guitarr", "guitarras": "guitarr",
    "baixo": "baix", "baixos": "baix",
    "bateria": "bateri", "baterias": "bateri", "percussao": "percuss",
    "teclado": "teclad", "teclados": "teclad", "piano": "piano", "pianos": "piano",
    "ukulele": "ukulel", "ukuleles": "ukulel",
    "sopro": "sopro", "madeiras": "madeira", "metais": "metais",
    "cordas_orquestrais": "cordas_orquestrais",
}


def category_matches(requested: str, label: str) -> bool:
    search = norm(requested)
    hay = norm(label)
    if not search:
        return True
    key = CATEGORY_ALIASES.get(search, search)
    return key in hay or search in hay


class CSVStore:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.tables = {path.stem: read_csv(path) for path in sorted(self.data_dir.glob("*.csv"))}
        self.products = self._find(("products", "produtos", "product", "produto"), {"product_id", "price_brl", "price"})
        self.orders = self._find(("orders", "pedidos", "order", "pedido"), {"order_id", "status"})
        self.customers = self._find(("customers", "clientes", "customer", "cliente"), {"customer_id", "email"})
        self.categories = self._find(("categories", "categorias", "category", "categoria"), {"category_id"})
        self.promotions = self._find(("promotions", "promocoes", "promotion", "promocao"), {"promotion_id"})
        self.order_items = self._find(("order_items", "itens_pedido", "itens_pedidos"), {"order_id", "product_id", "quantity"})
        self.categories_by_id = {first(r, "category_id", "id_categoria"): first(r, "name", "nome") for r in (self.categories.rows if self.categories else [])}
        self.products_by_id = {first(r, "product_id", "id_produto"): r for r in (self.products.rows if self.products else [])}
        self.customers_by_id = {first(r, "customer_id", "id_cliente"): r for r in (self.customers.rows if self.customers else [])}
        self.active_promotions: dict[str, dict[str, str]] = {}
        for r in (self.promotions.rows if self.promotions else []):
            if norm(first(r, "is_active", "ativo")) in {"1", "true", "sim", "yes"}:
                pid = first(r, "product_id", "id_produto")
                percent = price_number(first(r, "discount_percent", "desconto_percentual"))
                if percent is not None and 0 < percent < 100:
                    # If duplicates exist, don't stack percentages; first valid active record wins.
                    self.active_promotions.setdefault(pid, r)

    def _find(self, filename_tokens: tuple[str, ...], column_hints: set[str]) -> Table | None:
        # Prefer exact table names ("orders" must never resolve to "order_items").
        for part in filename_tokens:
            for t in self.tables.values():
                if norm(t.name) == part:
                    return t
        for part in filename_tokens:
            for t in self.tables.values():
                if norm(t.name).startswith(part + "_"):
                    return t
        for t in self.tables.values():
            if t.columns and column_hints.issubset(set(t.columns)):
                return t
        return None

    def inspect(self) -> dict[str, Any]:
        """Never display customer rows; only schema and counts."""
        return {
            "data_dir": str(self.data_dir),
            "tables": [{"file": t.name + ".csv", "rows": len(t.rows), "columns": list(t.columns)} for t in self.tables.values()],
            "recognized": {label: table.name if table else None for label, table in (
                ("products", self.products), ("categories", self.categories),
                ("promotions", self.promotions), ("orders", self.orders),
                ("order_items", self.order_items), ("customers", self.customers))},
            "active_promotions": len(self.active_promotions),
        }

    def _product_details(self, row: dict[str, str]) -> dict[str, Any]:
        title = first(row, "name", "nome_produto", "produto", "nome", "product_name", "modelo")
        pid = first(row, "product_id", "id_produto", "sku", "codigo")
        category_id = first(row, "category_id", "id_categoria")
        cat = self.categories_by_id.get(category_id) or first(row, "categoria", "tipo", "category")
        regular = price_number(first(row, "price_brl", "preco_venda", "preco_atual", "preco", "price", "valor"))
        stock = quantity(first(row, "stock_quantity", "quantidade_em_estoque", "qtd_estoque", "estoque", "stock"))
        catalog_status = norm(first(row, "status", "situacao") or "active")
        available = catalog_status in {"active", "ativo"} and stock is not None and stock > 0
        promo = self.active_promotions.get(pid) if available else None
        discount = price_number(first(promo, "discount_percent", "desconto_percentual")) if promo else None
        effective = regular * (Decimal(100) - discount) / Decimal(100) if regular is not None and discount else regular
        # Store manual p.6: PIX -5% only on non-promotional products.
        pix_price = amount(regular * Decimal("0.95")) if regular is not None and not discount else None
        return {
            "product_id": pid or None, "name": title, "category": cat or None,
            "catalog_status": catalog_status, "availability": (
                "discontinued" if catalog_status in {"discontinued", "descontinuado"} else
                "coming_soon" if catalog_status in {"coming_soon", "em_breve"} else
                "in_stock" if available else "out_of_stock" if stock is not None else "unknown"),
            "stock_units": stock,
            "regular_price_brl": amount(regular) if regular is not None else None,
            "current_price_brl": amount(effective) if effective is not None else None,
            "price_brl": amount(effective) if effective is not None else None,  # backward compatibility with early demo
            "promotion_discount_percent": amount(discount) if discount is not None else None,
            "promotion_name": first(promo, "description", "descricao") if promo else None,
            "pix_price_brl_if_not_promotional": pix_price,
            "note": "PIX 5% does not stack with active promotions" if discount else None,
        }

    def search_products(self, *, query: str | None = None, category: str | None = None,
                        max_price: float | None = None, in_stock_only: bool = False) -> dict[str, Any]:
        if not self.products:
            return {"status": "unavailable", "reason": "Product table not loaded"}
        if max_price is not None and (not isinstance(max_price, (int, float)) or not 0 <= max_price <= 10_000_000):
            return {"status": "invalid", "reason": "Invalid max_price filter"}
        query_terms = [w for w in textnorm(query).split() if len(w) > 1] if query else []
        result: list[dict[str, Any]] = []
        for row in self.products.rows:
            product = self._product_details(row)
            if not product["name"]:
                continue
            cat = product["category"] or ""
            hay = textnorm(product["name"] + " " + cat + " " + first(row, "description", "descricao"))
            if query_terms and not all(w in hay for w in query_terms):
                continue
            if category and not category_matches(category, cat):
                continue
            if in_stock_only and product["availability"] != "in_stock":
                continue
            current = product["current_price_brl"]
            if max_price is not None and (current is None or Decimal(str(current)) > Decimal(str(max_price))):
                continue
            result.append(product)
        result.sort(key=lambda p: (p["current_price_brl"] is None, p["current_price_brl"] or 0, p["name"]))
        return {"status": "ok", "source": self.products.name + ".csv", "matches": len(result),
                "products": result[:8], "truncated": len(result) > 8,
                "note": "Local CSV snapshot (not live). Price filter uses active promotional prices, not PIX."}

    def search_promotions(self) -> dict[str, Any]:
        """Show currently flagged promotions in the CSV snapshot (no date guarantees)."""
        if not self.products or not self.promotions:
            return {"status": "unavailable", "reason": "Products or promotions unavailable"}
        rows = []
        for pid in self.active_promotions:
            product_row = self.products_by_id.get(pid)
            if not product_row:
                continue
            product = self._product_details(product_row)
            if product["availability"] == "in_stock":
                rows.append(product)
        rows.sort(key=lambda item: (item["current_price_brl"] is None, item["current_price_brl"] or 0))
        return {"status": "ok", "matches": len(rows), "products": rows[:12],
                "source": self.promotions.name + ".csv + " + self.products.name + ".csv",
                "note": "Only CSV is_active flag is known; no promotion start/end dates. No PIX stacking."}

    def order_status(self, *, order_number: str, customer_email: str) -> dict[str, Any]:
        """Prototype-only identity check. Never return PII; unknown/wrong email indistinguishable."""
        if not str(order_number).strip() or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(customer_email).strip()):
            return {"status": "verification_required", "message": "Provide order number and purchase email."}
        if not self.orders or (not self.customers and not {"email_cliente", "customer_email", "email"}.intersection(set(self.orders.columns))):
            return {"status": "unavailable", "message": "Order verification unavailable; human support required."}
        submitted = str(order_number).strip().lower()
        mail = str(customer_email).strip().casefold()
        for row in self.orders.rows:
            order_id = first(row, "order_id", "numero_pedido", "id_pedido", "pedido_id", "id")
            if order_id.strip().lower() != submitted:
                continue
            client_id = first(row, "customer_id", "cliente_id", "id_cliente")
            client = self.customers_by_id.get(client_id, {})
            actual_mail = (first(row, "email_cliente", "customer_email", "email") or
                           first(client, "email", "email_cliente", "customer_email")).casefold()
            if not actual_mail or actual_mail != mail:
                continue
            order_status = first(row, "status", "status_pedido", "situacao", "order_status")
            items = []
            for item in self.order_items.rows if self.order_items else []:
                if first(item, "order_id", "id_pedido") != order_id:
                    continue
                p = self.products_by_id.get(first(item, "product_id", "id_produto"))
                if p:
                    items.append({"name": first(p, "name", "nome", "nome_produto"),
                                  "quantity": quantity(first(item, "quantity", "quantidade"))})
            return {
                "status": "verified", "order_number": order_id,
                "order_status": order_status or "not_provided",
                "tracking_code": first(row, "tracking_code", "codigo_rastreio") or None,
                "estimated_delivery": first(row, "estimated_delivery", "previsao_entrega") or None,
                "items": items[:10],
                "source": self.orders.name + ".csv",
                "note": "Historical local snapshot. Email comparison is not production-grade authentication.",
            }
        return {"status": "not_verified", "message": "Could not verify order and purchase email. No order information disclosed."}


class GuardedStore:
    """Read-only view of a shared `CSVStore` for ONE conversation, with a limit on failed order verifications.

    The tables are loaded once and shared by every conversation, so the attempt counter must not live in them.
    After `max_failures` wrong order/e-mail pairs in a row the conversation is locked: `order_status` stops
    consulting the tables, even for a correct pair, and sends the customer to the human team. A success resets
    the counter; a request with missing fields is not an attempt. This is a prototype safeguard per conversation,
    not per customer or per IP.
    """

    LOCKED_MESSAGE = ("Muitas tentativas de verificação nesta conversa. Por segurança, não vou consultar mais pedidos aqui. "
                      "Fale com a equipe da loja para continuar.")

    def __init__(self, inner: CSVStore, max_failures: int = 3):
        self.inner = inner
        self.max_failures = max_failures
        self.failures = 0

    def order_status(self, *, order_number: str, customer_email: str) -> dict[str, Any]:
        if self.failures >= self.max_failures:
            return {"status": "locked", "message": self.LOCKED_MESSAGE}
        result = self.inner.order_status(order_number=order_number, customer_email=customer_email)
        if result.get("status") == "verified":
            self.failures = 0
        elif result.get("status") == "not_verified":
            self.failures += 1
        return result

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)
