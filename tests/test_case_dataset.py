"""Integration tests using the original private case files if installed in data/.

Public repository does not include the source files. These tests skip cleanly
without them; public synthetic demo tests remain runnable everywhere.
"""
from pathlib import Path

import pytest

from emporio_agent.policies import PolicyIndex
from emporio_agent.store import CSVStore

DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def store():
    if not (DATA / "products.csv").exists():
        pytest.skip("Original private case files not present")
    return CSVStore(DATA)


@pytest.fixture(scope="module")
def policies():
    if not (DATA / "políticas_da_loja.pdf").exists():
        pytest.skip("Original private manual not present")
    return PolicyIndex(DATA / "políticas_da_loja.pdf")


def test_real_source_counts_and_joins(store):
    assert len(store.products.rows) == 65
    assert len(store.categories.rows) == 9
    assert len(store.promotions.rows) == 25
    assert len(store.orders.rows) == 20
    assert len(store.order_items.rows) == 22
    assert len(store.customers.rows) == 50
    assert len(store.active_promotions) == 4
    assert set(store.products_by_id)
    assert all(row["category_id"] in store.categories_by_id for row in store.products.rows)
    assert all(row["product_id"] in store.products_by_id for row in store.promotions.rows)
    assert all(row["customer_id"] in store.customers_by_id for row in store.orders.rows)
    assert all(row["order_id"] in {x["order_id"] for x in store.orders.rows} for row in store.order_items.rows)


def test_real_violao_filter_and_model_price(store):
    result = store.search_products(category="violões", max_price=1000, in_stock_only=True)
    assert result["status"] == "ok"
    assert result["matches"] == 12
    assert len(result["products"]) == 8 and result["truncated"]
    assert store.search_products(category="violão", max_price=1000, in_stock_only=True)["matches"] == 12
    takamine = store.search_products(query="Takamine GD20")["products"]
    assert len(takamine) == 1 and takamine[0]["current_price_brl"] == 2199


def test_real_promo_price_and_pix_nonstacking(store):
    promo = store.search_products(query="Crafter HT-100")["products"][0]
    assert promo["regular_price_brl"] == 2399
    assert promo["promotion_discount_percent"] == 18
    assert promo["current_price_brl"] == 1967.18
    assert promo["pix_price_brl_if_not_promotional"] is None
    assert len(store.search_promotions()["products"]) == 4
    no_promo = store.search_products(query="Takamine GD20")["products"][0]
    assert no_promo["pix_price_brl_if_not_promotional"] == 2089.05


def test_real_unavailable_and_discontinued_are_not_marked_in_stock(store):
    assert store.search_products(query="Giannini GF-3D")["products"][0]["availability"] == "out_of_stock"
    assert store.search_products(query="Shelby SN-7C")["products"][0]["availability"] == "discontinued"
    assert store.search_products(query="Kala KA-ABP-CTG")["products"][0]["availability"] == "coming_soon"
    assert store.search_products(query="Shelby SN-7C", in_stock_only=True)["matches"] == 0
    assert store.search_products(query="Kala KA-ABP-CTG", in_stock_only=True)["matches"] == 0


def test_real_order_requires_private_email_match(store):
    order = store.orders.rows[0]
    correct_email = store.customers_by_id[order["customer_id"]]["email"]
    bad = store.order_status(order_number=order["order_id"], customer_email="wrong@example.com")
    assert bad["status"] == "not_verified" and "tracking_code" not in bad
    good = store.order_status(order_number=order["order_id"], customer_email=correct_email)
    assert good["status"] == "verified" and good["order_status"] == "delivered"
    assert good["tracking_code"] and len(good["items"]) >= 1
    assert correct_email not in str(good)
    assert store.order_status(order_number=order["order_id"], customer_email="bad")["status"] == "verification_required"


@pytest.mark.parametrize("question,page", [
    ("Quais os horários e endereço da loja?", 2),
    ("Posso devolver compra online em arrependimento?", 4),
    ("Quais são as formas de pagamento PIX e parcelamento?", 3),
    ("Como é o frete por SEDEX?", 5),
    ("Promoções e descontos acumulam com PIX?", 6),
    ("A garantia cobre defeitos?", 7),
    ("Quero excluir meus dados pessoais LGPD.", 8),
])
def test_real_policy_pages_retrieved(policies, question, page):
    r = policies.search(question)
    assert r["status"] == "ok"
    assert page in [p["page"] for p in r["results"]]


def test_real_manual_contains_conflicting_topics(policies):
    r = policies.search("Defeito na troca e garantia legal")
    assert {4, 7}.issubset({p["page"] for p in r["results"]})
    assert policies.search("Quem vai ganhar a loteria amanhã?")["status"] == "no_evidence"
