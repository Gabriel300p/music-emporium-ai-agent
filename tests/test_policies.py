from pathlib import Path
from emporio_agent.policies import PolicyIndex

ROOT = Path(__file__).parent / "fixtures" / "data"


def test_cited_policy_retrieval():
    index = PolicyIndex(ROOT / "políticas_da_loja.pdf")
    r = index.search("Quais os horários de funcionamento?")
    assert r["status"] == "ok"
    assert r["results"][0]["page"] == 1
    assert "Horario" in r["results"][0]["excerpt"]


def test_returns_policy_is_retrieved():
    index = PolicyIndex(ROOT / "políticas_da_loja.pdf")
    r = index.search("Me arrependi, posso devolver a compra?")
    assert r["status"] == "ok"
    assert "Devolucao" in r["results"][0]["excerpt"]


def test_missing_policy_never_invented(tmp_path):
    assert PolicyIndex(tmp_path / "missing.pdf").search("Posso devolver?")["status"] == "unavailable"
