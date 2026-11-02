"""Performance-oriented behaviour: no repeated work per question, shared read-only data, warm connections.

Every optimisation here must leave answers unchanged, so the ranking test compares against the original algorithm.
"""
import math
import threading
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from emporio_agent import policies as policies_module
from emporio_agent import web
from emporio_agent.agent import Agent
from emporio_agent.offline import OfflineAgent
from emporio_agent.policies import TOPICS, PolicyIndex, terms
from emporio_agent.store import CSVStore

ROOT = Path(__file__).parent / "fixtures" / "data"
DEMO = Path(__file__).resolve().parents[1] / "demo_data"

PAGES = [
    "Empório da Música. Manual de políticas. Horário de funcionamento: segunda a sexta, das 9h às 18h. Sábado das 9h às 13h.",
    "Endereço da loja: Rua Exemplo, 10, Centro. Contato por telefone e WhatsApp. Estacionamento gratuito para clientes.",
    "Pagamento: PIX com 5% de desconto, cartão de crédito em até 10 parcelas, débito e boleto. Parcelamento sem juros.",
    "Troca e devolução: arrependimento em até 7 dias após o recebimento da compra online. Produto com defeito: troca em 30 dias.",
    "Entrega e frete: prazo de 3 a 7 dias úteis. Rastreamento pelo código enviado por e-mail. Retirada na loja sem custo.",
    "Promoções e descontos: o desconto PIX não acumula com promoções ativas. Liquidação e Black Friday seguem regras próprias.",
    "Garantia: 90 dias legal mais garantia do fabricante. Privacidade e LGPD: dados usados apenas para pedidos; exclusão sob pedido.",
]
QUERIES = [
    "Qual o horário de funcionamento?", "Vocês abrem aos domingos?", "Onde fica a loja e qual o telefone?",
    "Posso pagar no PIX e parcelar no cartão?", "Me arrependi da minha compra, posso devolver?", "Chegou com defeito, como trocar?",
    "Qual o prazo de entrega e como rastrear?", "O desconto PIX acumula com promoção?", "Quanto tempo de garantia?",
    "Quero excluir meus dados pessoais", "devolução", "pix promoção desconto", "Quem ganhou a Copa do Mundo?", "?", "",
]


@pytest.fixture(scope="module")
def multipage_pdf(tmp_path_factory):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    path = tmp_path_factory.mktemp("pdf") / "políticas_da_loja.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    for text in PAGES:
        y = 800
        words, line = text.split(), ""
        for w in words:
            if len(line) + len(w) > 80:
                c.drawString(40, y, line)
                y -= 16
                line = ""
            line += w + " "
        c.drawString(40, y, line)
        c.showPage()
    c.save()
    return path


def reference_search(index, question, top_k=3):
    """The original scoring, recomputed from scratch on every call (kept here as the behavioural reference)."""
    qterms = terms(question)
    if not qterms:
        return []
    q = set(qterms)
    counters = [Counter(terms(chunk.text)) for chunk in index.chunks]
    n = len(counters)
    scored = []
    for chunk, counter in zip(index.chunks, counters):
        score = sum((1 + math.log(1 + counter[t])) * math.log(1 + (n + 1) / (1 + sum(t in c for c in counters)))
                    for t in q if counter[t] > 0)
        for triggers, pages in TOPICS:
            if q.intersection(triggers) and chunk.page in pages and any(counter[t] > 0 for t in triggers):
                score += 3
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda row: (-row[0], row[1].page))
    return [chunk.page for _, chunk in scored[:max(1, min(top_k, 4))]]


def test_policy_ranking_is_identical_to_the_original_algorithm(multipage_pdf):
    index = PolicyIndex(multipage_pdf)
    assert len(index.chunks) == len(PAGES)
    for question in QUERIES:
        got = [r["page"] for r in index.search(question).get("results", [])]
        assert got == reference_search(index, question), question
        got4 = [r["page"] for r in index.search(question, top_k=4).get("results", [])]
        assert got4 == reference_search(index, question, top_k=4), question


def test_policy_search_does_not_reprocess_the_manual_on_every_question(multipage_pdf, monkeypatch):
    index = PolicyIndex(multipage_pdf)
    calls = {"n": 0}
    real = policies_module.terms

    def counting(text):
        calls["n"] += 1
        return real(text)

    monkeypatch.setattr(policies_module, "terms", counting)
    for _ in range(25):
        index.search("Me arrependi da minha compra, posso devolver?")
    assert calls["n"] == 25, "one tokenisation per question (the question itself), none per chunk"


def test_policy_search_cost_is_linear_in_chunks(multipage_pdf):
    index = PolicyIndex(multipage_pdf)
    base = index.chunks[:]
    index.chunks = base * 40  # 280 chunks
    index._build()
    start = time.perf_counter()
    for _ in range(20):
        index.search("Me arrependi da minha compra, posso devolver?")
    per_search = (time.perf_counter() - start) / 20
    assert per_search < 0.02, f"{per_search * 1000:.1f} ms per search over 280 chunks"


# ---------- shared read-only data ----------

def test_agents_accept_prebuilt_store_and_policies():
    store, pol = CSVStore(DEMO), PolicyIndex(DEMO / "políticas_da_loja.pdf")
    agent = Agent(DEMO, client=SimpleNamespace(responses=None), store=store, policies=pol)
    assert agent.store is store and agent.policies is pol
    offline = OfflineAgent(DEMO, store=store, policies=pol)
    assert offline.store is store and offline.policies is pol
    assert "R$ 599,90" in offline.reply("Quais violões disponíveis custando até R$ 1.000?")[0]


def test_conversations_share_one_loaded_copy_of_the_data(monkeypatch):
    built = {"store": 0, "policies": 0}
    real_store, real_pol = web.CSVStore, policies_module.PolicyIndex

    class CountingStore(real_store):
        def __init__(self, *a, **k):
            built["store"] += 1
            super().__init__(*a, **k)

    class CountingPolicies(real_pol):
        def __init__(self, *a, **k):
            built["policies"] += 1
            super().__init__(*a, **k)

    monkeypatch.setattr(web, "CSVStore", CountingStore)
    monkeypatch.setattr(policies_module, "PolicyIndex", CountingPolicies)
    app = web.App({"demo": web.Source("Demo", DEMO, False)}, "demo", None, None, {})
    sessions = [app.session_for(f"{i:016x}", "offline", "", "demo") for i in range(1, 6)]
    assert built == {"store": 1, "policies": 1}, built
    inner = {id(s.agent.store._inner) for s in sessions}
    assert len(inner) == 1, "all conversations read the same immutable tables"
    # each conversation still has its own recorder/history
    assert len({id(s.rec) for s in sessions}) == 5
    assert "R$ 599,90" in sessions[0].run("Quais violões disponíveis custando até R$ 1.000?")["reply"]
    assert sessions[1].run("Quais violões disponíveis custando até R$ 1.000?")["tools"][0]["tool"] == "search_products"


# ---------- connection reuse and warm-up ----------

def test_openai_client_keeps_connections_open_longer_than_the_sdk_default(monkeypatch):
    import openai

    seen = {}

    class Recorder:
        def __init__(self, **kwargs):
            seen.update(kwargs)
            self.responses = self

    monkeypatch.setattr(openai, "OpenAI", Recorder)
    app = web.App({"demo": web.Source("Demo", DEMO, False)}, "demo", None, None, {"OPENAI_API_KEY": "placeholder-credential-1234"})
    app._openai_client()
    assert isinstance(seen["http_client"], openai.DefaultHttpxClient)
    limits = web.connection_limits()
    assert limits.keepalive_expiry >= 60 > openai.DEFAULT_CONNECTION_LIMITS.keepalive_expiry
    assert limits.max_keepalive_connections >= 1


def test_warm_up_opens_the_connection_and_loads_data_without_blocking(monkeypatch):
    import openai

    pinged = []

    class Models:
        def list(self, **kw):
            pinged.append("models.list")
            return []

    class Warmable:
        def __init__(self, **kwargs):
            self.models = Models()
            self.responses = self

    monkeypatch.setattr(openai, "OpenAI", Warmable)
    app = web.App({"demo": web.Source("Demo", DEMO, False)}, "demo", None, None, {"OPENAI_API_KEY": "placeholder-credential-1234"})
    t = app.warm()
    assert isinstance(t, threading.Thread) and t.daemon
    t.join(5)
    assert pinged == ["models.list"]
    assert "demo" in app._shared, "data was preloaded so the first question does not pay for it"


def test_warm_up_is_skipped_without_key_and_never_raises(monkeypatch):
    import openai

    def boom(**kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(openai, "OpenAI", boom)
    no_key = web.App({"demo": web.Source("Demo", DEMO, False)}, "demo", None, None, {})
    no_key.warm().join(5)  # loads data only, no client, no exception
    with_key = web.App({"demo": web.Source("Demo", DEMO, False)}, "demo", None, None, {"OPENAI_API_KEY": "placeholder-credential-1234"})
    with_key.warm().join(5)  # the failure is swallowed; the first real request will report it
