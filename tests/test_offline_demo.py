"""Public, reproducible end-to-end tests on entirely synthetic records."""
from pathlib import Path

from emporio_agent.offline import OfflineAgent
from emporio_agent.policies import PolicyIndex
from emporio_agent.store import CSVStore

DATA = Path(__file__).resolve().parents[1] / "demo_data"


def test_demo_is_self_contained():
    store = CSVStore(DATA)
    assert set(store.inspect()["recognized"].values()) == {
        "products", "categories", "promotions", "customers", "orders", "order_items"
    }
    assert PolicyIndex(DATA / "políticas_da_loja.pdf").chunks


def test_demo_budget_and_promotion_source():
    agent = OfflineAgent(DATA)
    response, trace = agent.reply("Quais violões disponíveis custando até R$ 1.000?")
    assert "R$ 599,90" in response and "R$ 879,20" in response
    assert "Guitarra" not in response
    assert trace == [{"tool": "search_products", "status": "ok"}]


def test_demo_promotions_use_different_manual_page_from_private():
    response, trace = OfflineAgent(DATA).reply("Quais promoções estão ativas?")
    assert "R$ 1.099,00" in response and "R$ 879,20" in response
    assert "Manual, p. 1" in response
    assert trace[0]["tool"] == "search_promotions"
    assert trace[1]["tool"] == "search_policies"


def test_demo_order_two_turns_and_denial():
    agent = OfflineAgent(DATA)
    question, trace = agent.reply("Qual o status do pedido 1001?")
    assert "e-mail" in question and not trace
    bad, trace = agent.reply("Meu email é wrong@example.test")
    assert "não posso apresentar" in bad and trace[0]["status"] == "not_verified"
    agent.reply("Qual o status do pedido 1001?")
    good, trace = agent.reply("Meu email é ana@example.test")
    assert "shipped" in good and "DEMO0001" in good and trace[0]["status"] == "verified"
    assert "ana@example.test" not in good


def test_demo_out_of_scope_no_tool():
    response, trace = OfflineAgent(DATA).reply("Quanto vai chover amanhã em Curitiba?")
    assert "instrumentos musicais" in response and trace == []
