"""Read-only, deterministic lookup over CSV snapshots.

IMPORTANT: The source business schema was not provided with the assignment PDF.
Aliases and joins here are educated defaults. Validate these assumptions against
actual data before delivering the challenge.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
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
        # Brazilian thousands-only notation, e.g. R$ 1.200 (not 1.20).
        s = s.replace(".", "")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def quantity(value: Any) -> int | None:
    s = norm(value)
    if s in {"true", "yes", "sim", "disponivel", "em_estoque"}:
        return 1
    if s in {"false", "no", "nao", "indisponivel", "esgotado"}:
        return 0
    try:
        return int(float(str(value).replace(",", ".")))
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, str], ...]


def first(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        val = row.get(norm(key), "")
        if str(val).strip():
            return str(val).strip()
    return ""


def read_csv(path: Path) -> Table:
    raw: str | None = None
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            raw = path.read_text(encoding=enc)
            break
        except UnicodeDecodeError:
            pass
    if raw is None:
        raise ValueError(f"Could not decode CSV: {path.name}")
    sample = raw[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.DictReader(raw.splitlines(), delimiter=delimiter)
    if not reader.fieldnames:
        return Table(path.stem, (), ())
    mapping = {k: norm(k) for k in reader.fieldnames if k is not None}
    normalized_rows = []
    for row in reader:
        if not row or not any(str(v or "").strip() for v in row.values()):
            continue
        normalized_rows.append({mapping[k]: str(v or "").strip() for k, v in row.items() if k in mapping})
    return Table(path.stem, tuple(mapping.values()), tuple(normalized_rows))


class CSVStore:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.tables = {p.stem: read_csv(p) for p in sorted(self.data_dir.glob("*.csv"))}
        self.products = self._find(("produt", "product", "catalog", "estoque", "inventory"), {"preco", "price"})
        self.orders = self._find(("pedido", "order", "venda"), {"status", "situacao"})
        self.customers = self._find(("cliente", "customer"), {"email", "e_mail"})

    def _find(self, filename_tokens: tuple[str, ...], column_hints: set[str]) -> Table | None:
        for t in self.tables.values():
            if any(part in norm(t.name) for part in filename_tokens):
                return t
        for t in self.tables.values():
            if t.columns and any(h in t.columns for h in column_hints):
                return t
        return None

    def inspect(self) -> dict[str, Any]:
        """Only schema and row counts; never output customer records."""
        return {
            "data_dir": str(self.data_dir),
            "tables": [{"file": t.name + ".csv", "rows": len(t.rows), "columns": list(t.columns)} for t in self.tables.values()],
            "recognized": {"products": self.products.name if self.products else None,
                           "orders": self.orders.name if self.orders else None,
                           "customers": self.customers.name if self.customers else None},
        }

    def search_products(self, *, query: str | None = None,
                        category: str | None = None,
                        max_price: float | None = None,
                        in_stock_only: bool = False) -> dict[str, Any]:
        if not self.products:
            return {"status": "unavailable", "reason": "No products CSV table was recognized."}
        if max_price is not None and (max_price < 0 or max_price > 100000000):
            return {"status": "invalid", "reason": "Invalid price filter."}
        selected = []
        for row in self.products.rows:
            title = first(row, "nome_produto", "produto", "nome", "descricao", "modelo", "product_name", "name")
            cat = first(row, "categoria", "tipo", "grupo", "category")
            price = price_number(first(row, "preco_venda", "preco_atual", "preco", "valor", "price"))
            stock = quantity(first(row, "quantidade_em_estoque", "qtd_estoque", "estoque", "quantidade", "stock", "disponivel"))
            if not title:
                continue
            if query:
                tokens = [w for w in textnorm(query).split() if len(w) > 1]
                full = textnorm(title + " " + cat + " " + first(row, "marca", "brand"))
                if not tokens or not all(w in full for w in tokens):
                    continue
            if category and textnorm(category) not in textnorm(cat + " " + title):
                continue
            if max_price is not None and (price is None or price > Decimal(str(max_price))):
                continue
            if in_stock_only and (stock is None or stock <= 0):
                continue
            selected.append({
                "name": title,
                "category": cat or None,
                "sku": first(row, "sku", "codigo_produto", "id_produto", "codigo") or None,
                "price_brl": float(price) if price is not None else None,
                "stock_units": stock,
                "availability": "in_stock" if stock is not None and stock > 0 else "out_of_stock" if stock is not None else "unknown",
            })
        selected.sort(key=lambda item: (item["price_brl"] is None, item["price_brl"] or 0, item["name"]))
        return {"status": "ok", "source": self.products.name + ".csv", "matches": len(selected), "products": selected[:8],
                "note": "Snapshot from local CSV. Not a live inventory system. At most 8 results returned."}

    def _email_for_order(self, row: dict[str, str]) -> str:
        email = first(row, "email", "e_mail", "email_cliente", "cliente_email", "customer_email")
        if email:
            return email.lower()
        client_id = first(row, "cliente_id", "id_cliente", "customer_id")
        if client_id and self.customers:
            for client in self.customers.rows:
                if client_id == first(client, "id_cliente", "cliente_id", "customer_id", "id"):
                    return first(client, "email", "e_mail", "email_cliente").lower()
        return ""

    def order_status(self, *, order_number: str, customer_email: str) -> dict[str, Any]:
        """Do not disclose any order details before matching the purchase email."""
        if not order_number.strip() or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", customer_email.strip()):
            return {"status": "verification_required", "message": "Order number and valid purchase email are required."}
        if not self.orders:
            return {"status": "unavailable", "message": "Order table not available. Refer customer to human support."}
        for row in self.orders.rows:
            id_in_data = first(row, "numero_pedido", "pedido_id", "id_pedido", "order_number", "order_id", "pedido", "id")
            if str(id_in_data).strip().lower() != order_number.strip().lower():
                continue
            if self._email_for_order(row) != customer_email.strip().lower():
                # Do not indicate if an order with a different email exists.
                continue
            return {"status": "verified", "order_number": id_in_data,
                    "order_status": first(row, "status_pedido", "status", "situacao", "etapa", "order_status") or "not_provided",
                    "expected_delivery": first(row, "previsao_entrega", "data_prevista", "estimated_delivery") or None,
                    "source": self.orders.name + ".csv",
                    "note": "Local snapshot, not a realtime shipping feed."}
        return {"status": "not_verified", "message": "Could not verify the supplied order number and email. Do not disclose order information."}
