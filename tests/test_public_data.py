"""Verify that the published case complement is usable and non-identifying."""
from __future__ import annotations

import csv
from pathlib import Path

from emporio_agent.policies import PolicyIndex
from emporio_agent.store import CSVStore

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data_public"


def csv_rows(name: str) -> list[dict[str, str]]:
    with (PUBLIC / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_public_case_is_complete_and_preserves_fks():
    counts = {name: len(csv_rows(name)) for name in
              ("products", "categories", "promotions", "orders", "order_items", "customers")}
    assert counts == {"products": 65, "categories": 9, "promotions": 25,
                      "orders": 20, "order_items": 22, "customers": 50}
    assert CSVStore(PUBLIC).inspect()["active_promotions"] == 4
    products = {r["product_id"] for r in csv_rows("products")}
    categories = {r["category_id"] for r in csv_rows("categories")}
    customers = {r["customer_id"] for r in csv_rows("customers")}
    orders = {r["order_id"] for r in csv_rows("orders")}
    assert all(r["category_id"] in categories for r in csv_rows("products"))
    assert all(r["product_id"] in products for r in csv_rows("promotions"))
    assert all(r["customer_id"] in customers for r in csv_rows("orders"))
    assert all(r["order_id"] in orders and r["product_id"] in products for r in csv_rows("order_items"))


def test_public_case_does_not_disclose_customer_identifiers():
    customers = csv_rows("customers")
    assert all(r["email"].endswith("@example.test") for r in customers)
    assert all(r["phone"] == "0000000000" for r in customers)
    assert all(r["name"].startswith("Cliente fictício ") for r in customers)
    assert all(r["city"] == "Cidade Demonstrativa" for r in customers)
    orders = csv_rows("orders")
    assert all(r["notes"] == "" for r in orders)
    assert all(not r["tracking_code"] or r["tracking_code"].startswith("DEMO-") for r in orders)


def test_public_case_has_synthetic_policy_and_valid_read_only_queries():
    index = PolicyIndex(PUBLIC / "políticas_da_loja.pdf")
    assert len(index.chunks) == 1  # source internal PDF has 8 pages
    assert "FICTICIAS" in index.chunks[0].text
    store = CSVStore(PUBLIC)
    result = store.search_products(category="violões", max_price=1000, in_stock_only=True)
    assert result["status"] == "ok" and result["matches"] == 12


def test_public_case_order_lookup_requires_synthetic_email():
    store = CSVStore(PUBLIC)
    row = csv_rows("orders")[0]
    email = next(r["email"] for r in csv_rows("customers") if r["customer_id"] == row["customer_id"])
    good = store.order_status(order_number=row["order_id"], customer_email=email)
    bad = store.order_status(order_number=row["order_id"], customer_email="wrong@example.test")
    assert good["status"] == "verified"
    assert bad["status"] != "verified"
    assert "notes" not in good and "customer_email" not in good
