"""Local web UI: server contract, privacy guards and tool-output capture (synthetic data only, no network)."""
import http.client
import json
import shutil
import socket
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from emporio_agent import web
from emporio_agent.policies import PolicyIndex
from emporio_agent.store import CSVStore

DEMO = Path(__file__).resolve().parents[1] / "demo_data"
# Obvious placeholders (not credentials). The redaction rule must mask anything shaped like "sk-<token>".
SECRET = "sk-REDACTED-PLACEHOLDER-for-tests"
UPSTREAM_TOKEN = "sk-REDACTED-PLACEHOLDER-upstream"


class FakeClient:
    """Stands in for the OpenAI client: one tool call, then a final message. No model output is validated here."""

    def __init__(self):
        self.calls = []
        self.fail = False
        self.responses = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail:
            raise RuntimeError("upstream rejected key " + UPSTREAM_TOKEN)
        last = kwargs["input"][-1]
        if isinstance(last, dict) and last.get("type") == "function_call_output":
            return SimpleNamespace(output=[SimpleNamespace(type="message")], output_text="Encontrei o Violão Escola C30 Demo.",
                                   usage=SimpleNamespace(input_tokens=30, output_tokens=7))
        call = SimpleNamespace(type="function_call", name="search_products", call_id="c1",
                               arguments=json.dumps({"query": None, "category": "violões", "max_price": 1000, "in_stock_only": False}))
        return SimpleNamespace(output=[call], output_text="", usage=SimpleNamespace(input_tokens=100, output_tokens=20))


@pytest.fixture()
def fake():
    return FakeClient()


@pytest.fixture()
def server(fake):
    sources = {
        "demo": web.Source("Demo sintético", DEMO, False),
        "original": web.Source("Originais (privados)", DEMO, True),
    }
    srv = web.create_server(sources, "demo", port=0, client_factory=lambda: fake,
                            environ={"OPENAI_API_KEY": SECRET, "OPENAI_MODEL": "modelo-teste"})
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def call(srv, method, path, body=None, headers=None, raw=None):
    port = srv.server_address[1]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    hdrs = {"Host": f"127.0.0.1:{port}"}
    payload = raw
    if body is not None:
        payload = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    conn.request(method, path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, resp.getheader("Content-Type") or "", data


def chat(srv, message, **over):
    body = {"session": "a" * 16, "message": message, "mode": "offline", "model": "", "data": "demo"}
    body.update(over)
    status, _, data = call(srv, "POST", "/api/chat", body)
    return status, json.loads(data)


# ---------- helpers ----------

def test_load_dotenv_fills_only_missing_and_never_prints(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text('# comentario\nOPENAI_API_KEY="from-file"\nOPENAI_MODEL=gpt-x\n\nLIXO\n')
    environ = {"OPENAI_MODEL": "ja-definido"}
    web.load_dotenv(env_file, environ)
    assert environ["OPENAI_API_KEY"] == "from-file"
    assert environ["OPENAI_MODEL"] == "ja-definido"
    assert "from-file" not in capsys.readouterr().out


def test_load_dotenv_missing_file_is_noop(tmp_path):
    environ = {}
    web.load_dotenv(tmp_path / "nao-existe.env", environ)
    assert environ == {}


def test_redact_masks_anything_shaped_like_an_api_key():
    out = web.redact("erro com " + UPSTREAM_TOKEN + " fim")
    assert "PLACEHOLDER-upstream" not in out and "sk-" in out and out.endswith("fim")


def test_resolve_data_dir_maps_sheets_style_names_without_touching_source(tmp_path):
    src = tmp_path / "data"
    src.mkdir()
    for table in ("categories", "customers", "order_items", "orders", "products", "promotions"):
        shutil.copy(DEMO / f"{table}.csv", src / f"desafio_tecnico_ai_eng - {table}.csv")
    shutil.copy(DEMO / "políticas_da_loja.pdf", src / "politicas_da_loja.pdf")
    before = sorted(p.name for p in src.iterdir())
    resolved = web.resolve_data_dir(src)
    assert resolved != src
    assert set(CSVStore(resolved).inspect()["recognized"].values()) == {
        "products", "categories", "promotions", "customers", "orders", "order_items"}
    assert PolicyIndex(resolved / "políticas_da_loja.pdf").chunks
    assert sorted(p.name for p in src.iterdir()) == before


def test_resolve_data_dir_keeps_directory_with_expected_names():
    assert web.resolve_data_dir(DEMO) == DEMO


def test_discover_sources_lists_only_non_empty_dirs_and_flags_private(tmp_path):
    (tmp_path / "data_public").mkdir()
    (tmp_path / "data_public" / "products.csv").write_text("product_id\n1\n")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / ".gitkeep").write_text("")
    sources, default = web.discover_sources(tmp_path)
    assert list(sources) == ["public"] and default == "public" and not sources["public"].private
    (tmp_path / "data" / "products.csv").write_text("product_id\n1\n")
    sources, default = web.discover_sources(tmp_path)
    assert sources["original"].private and default == "public"


# ---------- server contract ----------

def test_index_and_config_do_not_leak_secret(server):
    status, ctype, data = call(server, "GET", "/")
    assert status == 200 and "text/html" in ctype and "Empório" in data.decode()
    status, ctype, data = call(server, "GET", "/api/config")
    cfg = json.loads(data)
    assert status == 200 and cfg["has_key"] is True and cfg["default_model"] == "modelo-teste"
    assert {s["key"] for s in cfg["sources"]} == {"demo", "original"}
    assert next(s for s in cfg["sources"] if s["key"] == "original")["private"] is True
    assert cfg["endpoint_host"] == "api.openai.com" and cfg["endpoint_is_openai"] is True
    assert SECRET not in data.decode()


def test_offline_chat_returns_trace_and_raw_tool_output(server):
    status, out = chat(server, "Quais violões disponíveis custando até R$ 1.000?")
    assert status == 200 and out["error"] is None
    assert "R$ 599,90" in out["reply"]
    assert out["trace"] == [{"tool": "search_products", "status": "ok"}]
    raw = out["tools"][0]
    assert raw["tool"] == "search_products" and raw["output"]["status"] == "ok"
    assert raw["output"]["products"], "raw tool output must be exposed"
    assert out["usage"]["calls"] == 0


def test_offline_session_keeps_order_flow_between_turns(server):
    _, first = chat(server, "Qual o status do pedido 1001?")
    assert "e-mail" in first["reply"] and first["tools"] == []
    _, second = chat(server, "Meu email é ana@example.test")
    assert second["trace"][0]["status"] == "verified"
    assert second["tools"][0]["tool"] == "order_status"


def test_llm_mode_uses_client_and_reports_usage(server, fake):
    status, out = chat(server, "Violões até R$ 1.000?", mode="llm", model="meu-modelo")
    assert status == 200 and out["error"] is None
    assert out["reply"].startswith("Encontrei")
    assert out["trace"] == [{"tool": "search_products", "status": "ok"}]
    assert out["tools"][0]["args"]["category"] == "violões"
    usage = out["usage"]
    assert (usage["calls"], usage["tokens_in"], usage["tokens_out"]) == (2, 130, 27)
    assert usage["seconds_api"] >= 0
    assert fake.calls[0]["model"] == "meu-modelo"


def test_llm_error_becomes_json_redacted_and_session_survives(server, fake):
    fake.fail = True
    status, out = chat(server, "Oi", mode="llm")
    assert status == 200 and out["reply"] is None
    assert "RuntimeError" in out["error"] and "PLACEHOLDER-upstream" not in out["error"]
    fake.fail = False
    status, out = chat(server, "Violões até R$ 1.000?", mode="llm")
    assert out["error"] is None and out["reply"]


def test_llm_without_key_reports_clear_error():
    srv = web.create_server({"demo": web.Source("Demo", DEMO, False)}, "demo", port=0, environ={})
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        status, out = chat(srv, "Oi", mode="llm")
        assert status == 200 and out["reply"] is None
        assert "chave" in out["error"].lower() and "offline" in out["error"].lower()
    finally:
        srv.shutdown()
        srv.server_close()


def test_reset_clears_history(server):
    chat(server, "Qual o status do pedido 1001?")
    status, _, _ = call(server, "POST", "/api/reset", {"session": "a" * 16})
    assert status == 200
    _, out = chat(server, "Meu email é ana@example.test")
    assert out["tools"] == []


def test_session_is_bound_to_its_data_source(server):
    chat(server, "Qual o status do pedido 1001?", data="demo")
    status, out = chat(server, "Meu email é ana@example.test", data="original")
    assert status == 409 or (status == 200 and out["tools"] == [])


# ---------- guards ----------

def test_rejects_foreign_host(server):
    status, _, _ = call(server, "GET", "/api/config", headers={"Host": "evil.example.com"})
    assert status == 403


def test_rejects_foreign_origin(server):
    status, _, _ = call(server, "POST", "/api/chat",
                        {"session": "a" * 16, "message": "oi", "mode": "offline", "model": "", "data": "demo"},
                        headers={"Origin": "http://evil.example.com"})
    assert status == 403


def test_rejects_wrong_content_type_and_large_body_and_long_message(server):
    status, _, _ = call(server, "POST", "/api/chat", raw=b"{}", headers={"Content-Type": "text/plain"})
    assert status == 415
    status, _, _ = call(server, "POST", "/api/chat", raw=b"x" * 70_000, headers={"Content-Type": "application/json"})
    assert status == 413
    status, out = chat(server, "a" * 2001)
    assert status == 400


def test_rejects_bad_session_unknown_source_mode_and_route(server):
    assert chat(server, "oi", session="../etc")[0] == 400
    assert chat(server, "oi", data="inexistente")[0] == 400
    assert chat(server, "oi", mode="outro")[0] == 400
    assert call(server, "GET", "/nada")[0] == 404


# ---------- export ----------

def test_export_labels_mode_data_and_tools_without_raw_output(server):
    chat(server, "Quais violões disponíveis custando até R$ 1.000?")
    status, ctype, data = call(server, "GET", "/api/export?session=" + "a" * 16)
    md = data.decode()
    assert status == 200 and "markdown" in ctype
    assert "Modo: offline" in md and "Dados: Demo sintético" in md
    assert "search_products" in md and "R$ 599,90" in md
    assert "dados privados" not in md.lower()
    assert '"products"' not in md, "raw tool JSON must not be exported"


def test_export_warns_when_source_is_private(server):
    chat(server, "Quais promoções estão ativas?", session="c" * 16, data="original")
    _, _, data = call(server, "GET", "/api/export?session=" + "c" * 16)
    assert "dados privados" in data.decode().lower()


def test_export_unknown_session_is_404(server):
    assert call(server, "GET", "/api/export?session=" + "b" * 16)[0] == 404


# ---------- first use: key in memory, labelled samples, ports, browser ----------

PASTED = "pasted-test-credential-0123456789"  # not shaped like an OpenAI key on purpose: any provider format must work


def test_config_samples_are_labelled_and_order_samples_use_public_data(server):
    cfg = json.loads(call(server, "GET", "/api/config")[2])
    assert all(s["q"] and s["tests"] for s in cfg["samples"])
    order = [s for s in cfg["samples"] if "pedido" in s["q"].lower() and "@" in s["q"]]
    assert order, "an order sample with a valid e-mail is expected for non-private data"
    assert "ana@example.test" in order[0]["q"] and "1001" in order[0]["q"]
    assert cfg["key_source"] == "env"


def test_no_order_sample_for_private_source():
    srv = web.create_server({"original": web.Source("Originais", DEMO, True)}, "original", port=0, environ={})
    try:
        cfg = srv.app.config()
    finally:
        srv.server_close()
    assert not any("@" in s["q"] for s in cfg["samples"])


def test_pasted_key_is_kept_in_memory_only_and_never_echoed(server, monkeypatch):
    seen = {}

    class Recorder:
        def __init__(self, **kwargs):
            seen.update(kwargs)
            self.responses = self

    import openai
    monkeypatch.setattr(openai, "OpenAI", Recorder)
    app = server.app
    app.client_factory = None
    app.environ = {}
    assert json.loads(call(server, "GET", "/api/config")[2])["key_source"] == "none"
    status, ctype, data = call(server, "POST", "/api/key", {"key": "  " + PASTED + "  "})
    assert status == 200 and PASTED not in data.decode()
    cfg_raw = call(server, "GET", "/api/config")[2].decode()
    assert json.loads(cfg_raw)["key_source"] == "ui" and PASTED not in cfg_raw
    chat(server, "oi", mode="llm", session="d" * 16)  # builds the client with the pasted key
    assert seen.get("api_key") == PASTED
    status, _, _ = call(server, "POST", "/api/key", {"key": ""})
    assert status == 200 and json.loads(call(server, "GET", "/api/config")[2])["key_source"] == "none"


def test_key_endpoint_validates_and_guards(server):
    assert call(server, "POST", "/api/key", {"key": "curta"})[0] == 400
    assert call(server, "POST", "/api/key", {"key": "tem espaco no meio 123456"})[0] == 400
    assert call(server, "POST", "/api/key", {"key": 123})[0] == 400
    assert call(server, "POST", "/api/key", {"key": PASTED}, headers={"Origin": "http://evil.example.com"})[0] == 403
    assert call(server, "POST", "/api/key", raw=b"{}", headers={"Content-Type": "text/plain"})[0] == 415


def test_pasted_key_is_masked_in_upstream_errors(server, fake):
    call(server, "POST", "/api/key", {"key": PASTED})
    fake.fail = True

    def boom(**kwargs):
        raise RuntimeError("provider said bad key " + PASTED)
    fake.create = boom
    _, out = chat(server, "oi", mode="llm", session="e" * 16)
    assert out["error"] and PASTED not in out["error"]


def test_exported_markdown_never_contains_the_key(server):
    call(server, "POST", "/api/key", {"key": PASTED})
    chat(server, "Quais violões disponíveis custando até R$ 1.000?", mode="llm", session="f" * 16)
    md = call(server, "GET", "/api/export?session=" + "f" * 16)[2].decode()
    assert PASTED not in md


def test_find_free_port_skips_busy_ports():
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    busy = blocker.getsockname()[1]
    try:
        assert web.find_free_port(busy, tries=20) != busy
    finally:
        blocker.close()


def test_open_browser_helper_calls_opener_with_url():
    opened = []
    timer = web.schedule_browser("http://127.0.0.1:1234", opener=opened.append, delay=0)
    timer.join(2)
    assert opened == ["http://127.0.0.1:1234"]


# ---------- startup ----------

def test_serve_reports_port_in_use(capsys):
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    try:
        code = web.serve(port=blocker.getsockname()[1], root=DEMO.parent, data_dir=str(DEMO))
    finally:
        blocker.close()
    assert code == 1
    assert "porta" in capsys.readouterr().err.lower()
