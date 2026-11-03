from decimal import Decimal
from pathlib import Path

from emporio_agent.store import CSVStore, norm, price_number

ROOT = Path(__file__).parent / "fixtures" / "data"


def test_parse_localized_price():
    assert price_number("R$ 1.299,90") == Decimal("1299.90")
    assert price_number("2499.00") == Decimal("2499.00")
    assert price_number("R$ 1.200") == Decimal("1200")
    assert price_number("N/A") is None
    assert norm("Violões Acústicos") == "violoes_acusticos"


def test_budget_filter_and_stock():
    store = CSVStore(ROOT)
    result = store.search_products(category="violões", max_price=1000, in_stock_only=True)
    assert result["status"] == "ok"
    assert result["matches"] == 1
    assert result["products"][0]["name"] == "Violão Acústico XPTO"
    assert result["products"][0]["price_brl"] == 799.90


def test_product_name_lookup():
    store = CSVStore(ROOT)
    r = store.search_products(query="Takamine GD20")
    assert r["matches"] == 1
    assert r["products"][0]["price_brl"] == 2450.0


def test_order_requires_matching_email_and_reveals_no_customer_pii():
    store = CSVStore(ROOT)
    r = store.order_status(order_number="A123", customer_email="wrong@example.com")
    assert r["status"] == "not_verified"
    assert "Em separação" not in str(r)
    r = store.order_status(order_number="A123", customer_email="cliente@example.com")
    assert r["status"] == "verified"
    assert r["order_status"] == "Em separação"
    assert "cliente@example.com" not in str(r)
    assert store.order_status(order_number="A123", customer_email="invalid")["status"] == "verification_required"


def test_unknown_data_never_fabricated(tmp_path):
    store = CSVStore(tmp_path)
    assert store.search_products()["status"] == "unavailable"
    assert store.order_status(order_number="1", customer_email="x@y.com")["status"] == "unavailable"
