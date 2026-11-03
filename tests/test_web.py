"""Local web UI: server contract, privacy guards and tool-output capture (synthetic data only, no network)."""
import http.client
import json
import re
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

    def stream(self, **kwargs):
        response = self.create(**kwargs)
        text = response.output_text
        return _FakeStream(response, [text[:9], text[9:]] if text else [])


class _FakeStream:
    def __init__(self, response, deltas):
        self.response, self.deltas = response, deltas

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        for d in self.deltas:
            yield SimpleNamespace(type="response.output_text.delta", delta=d)

    def get_final_response(self):
        return self.response


class NoStreamClient:
    """A client that only offers create(): the stream route must still work, just without deltas."""

    def __init__(self, inner):
        self.responses = self
        self.create = inner.create


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


# ---------- streaming route ----------

def stream_events(srv, message, **over):
    body = {"session": "5" * 16, "message": message, "mode": "llm", "model": "", "data": "demo"}
    body.update(over)
    status, ctype, data = call(srv, "POST", "/api/chat/stream", body)
    return status, ctype, [json.loads(line) for line in data.decode().splitlines() if line.strip()]


def test_stream_route_emits_progress_then_text_then_done(server):
    status, ctype, events = stream_events(server, "Violões até R$ 1.000?")
    assert status == 200 and "ndjson" in ctype
    kinds = [e["type"] for e in events]
    assert kinds[0] == "status" and kinds[-1] == "done"
    assert kinds.index("tool_start") < kinds.index("tool") < kinds.index("delta") < kinds.index("done")
    start = next(e for e in events if e["type"] == "tool_start")
    tool = next(e for e in events if e["type"] == "tool")
    assert start["tool"] == tool["tool"] == "search_products" and tool["output"]["status"] == "ok"
    done = events[-1]
    assert "".join(e["text"] for e in events if e["type"] == "delta") == done["reply"] == "Encontrei o Violão Escola C30 Demo."
    assert done["error"] is None and done["trace"] == [{"tool": "search_products", "status": "ok"}]
    assert done["usage"]["calls"] == 2 and len(done["usage"]["seconds_each"]) == 2


def test_stream_route_works_offline_without_deltas(server):
    status, _, events = stream_events(server, "Quais violões disponíveis custando até R$ 1.000?", mode="offline", session="6" * 16)
    kinds = [e["type"] for e in events]
    assert status == 200 and "delta" not in kinds and kinds[-1] == "done" and "tool" in kinds
    assert "R$ 599,90" in events[-1]["reply"]


def test_stream_route_without_client_streaming_support_still_finishes(fake):
    sources = {"demo": web.Source("Demo", DEMO, False)}
    srv = web.create_server(sources, "demo", port=0, client_factory=lambda: NoStreamClient(fake), environ={"OPENAI_API_KEY": SECRET})
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        status, _, events = stream_events(srv, "Violões até R$ 1.000?")
        kinds = [e["type"] for e in events]
        assert status == 200 and "delta" not in kinds and kinds[-1] == "done"
        assert events[-1]["reply"] == "Encontrei o Violão Escola C30 Demo." and events[-1]["error"] is None
    finally:
        srv.shutdown()
        srv.server_close()


def test_stream_route_reports_upstream_error_in_done_and_session_survives(server, fake):
    fake.fail = True
    status, _, events = stream_events(server, "Oi")
    done = events[-1]
    assert status == 200 and done["type"] == "done" and done["reply"] is None
    assert "RuntimeError" in done["error"] and "PLACEHOLDER-upstream" not in done["error"]
    fake.fail = False
    _, _, events = stream_events(server, "Violões até R$ 1.000?")
    assert events[-1]["error"] is None and events[-1]["reply"]


def test_stream_route_has_the_same_guards_as_chat(server):
    body = {"session": "5" * 16, "message": "oi", "mode": "offline", "model": "", "data": "demo"}
    assert call(server, "POST", "/api/chat/stream", body, headers={"Origin": "http://evil.example.com"})[0] == 403
    assert call(server, "POST", "/api/chat/stream", raw=b"{}", headers={"Content-Type": "text/plain"})[0] == 415
    assert call(server, "POST", "/api/chat/stream", {**body, "session": "../x"})[0] == 400
    assert call(server, "POST", "/api/chat/stream", {**body, "message": "a" * 2001})[0] == 400
    assert call(server, "POST", "/api/chat/stream", {**body, "mode": "outro"})[0] == 400
    assert call(server, "POST", "/api/chat/stream", {**body, "data": "inexistente"})[0] == 400
    assert call(server, "POST", "/api/chat/stream", body, headers={"Host": "evil.example.com"})[0] == 403


def test_usage_reports_seconds_of_each_api_call(server):
    _, out = chat(server, "Violões até R$ 1.000?", mode="llm", session="7" * 16)
    each = out["usage"]["seconds_each"]
    assert len(each) == 2 and all(isinstance(x, float) and x >= 0 for x in each)


def test_locked_verification_shows_up_in_the_tool_panel_of_the_web_ui(server):
    sid = "9" * 16
    for _ in range(3):
        chat(server, "Qual o status do pedido 1001?", session=sid)
        chat(server, "Meu email é outra.pessoa@example.com", session=sid)
    chat(server, "Qual o status do pedido 1001?", session=sid)
    _, out = chat(server, "Meu email é ana@example.test", session=sid)
    assert out["tools"][0]["output"]["status"] == "locked"
    assert out["trace"] == [{"tool": "order_status", "status": "locked"}]
    _, fresh = chat(server, "Qual o status do pedido 1001?", session="8" * 16)
    _, ok = chat(server, "Meu email é ana@example.test", session="8" * 16)
    assert ok["tools"][0]["output"]["status"] == "verified", "another conversation is not affected"


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


def test_ambient_openai_base_url_is_ignored_unless_passed_explicitly():
    ambient = {"OPENAI_BASE_URL": "http://127.0.0.1:8787", "OPENAI_API_KEY": SECRET}
    srv = web.create_server({"demo": web.Source("Demo", DEMO, False)}, "demo", port=0, environ=ambient)
    try:
        cfg = srv.app.config()
    finally:
        srv.server_close()
    assert cfg["endpoint_host"] == "api.openai.com" and cfg["endpoint_is_openai"] is True
    srv = web.create_server({"demo": web.Source("Demo", DEMO, False)}, "demo", port=0, environ=ambient,
                            base_url="https://llm.example.org/v1")
    try:
        cfg = srv.app.config()
    finally:
        srv.server_close()
    assert cfg["endpoint_host"] == "llm.example.org" and cfg["endpoint_is_openai"] is False


def test_page_does_not_show_an_endpoint_warning_banner():
    assert "não é api.openai.com" not in web.PAGE


def test_samples_have_short_label_and_a_known_icon(server):
    cfg = json.loads(call(server, "GET", "/api/config")[2])
    for sample in cfg["samples"]:
        assert 0 < len(sample["label"]) <= 18, sample
        assert f'id="i-{sample["icon"]}"' in web.PAGE, f"missing icon symbol: {sample['icon']}"


def test_page_has_the_new_structure_and_stays_self_contained():
    page = web.PAGE
    for needle in ('id="key-dialog"', 'id="settings-dialog"', 'id="kpis"', 'id="turns"', 'id="suggest-menu"',
                   'id="drawer"', 'id="splitter"', 'role="separator"', "<dialog", "data-theme"):
        assert needle in page, needle
    assert 'id="chips"' not in page, "the old chips row must be gone"
    assert "card-btn" in page and "Ver perguntas sugeridas" not in page, "empty state shows selectable suggestion boxes, not a button"
    for gone in ("pcard", "ocard", "qcard", "cards-toggle", "viewModels"):
        assert gone not in page, f"answer cards were removed: {gone}"
    assert "innerHTML" not in page, "model output must only enter the DOM as text"
    external = set(re.findall(r"https?://[^\s\"'<>)]+", page))
    assert external <= {"https://platform.openai.com/api-keys", "http://www.w3.org/2000/svg"}, external
    assert "fonts.googleapis" not in page and "<link" not in page


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


def test_openai_client_is_reused_across_conversations_and_rebuilt_when_the_key_changes(server, monkeypatch):
    built = []

    class Counting:
        def __init__(self, **kwargs):
            built.append(kwargs["api_key"])
            self.responses = self

    import openai
    monkeypatch.setattr(openai, "OpenAI", Counting)
    app = server.app
    app.client_factory = None
    app.environ = {}
    call(server, "POST", "/api/key", {"key": "first-pasted-credential-123"})
    chat(server, "oi", mode="llm", session="a1" * 8)
    chat(server, "oi", mode="llm", session="a2" * 8)
    chat(server, "oi", mode="llm", session="a3" * 8)
    assert built == ["first-pasted-credential-123"], "one client (one connection pool) for all conversations"
    call(server, "POST", "/api/key", {"key": "second-pasted-credential-456"})
    chat(server, "oi", mode="llm", session="a4" * 8)
    assert built == ["first-pasted-credential-123", "second-pasted-credential-456"]


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


# ---------- offline pacing ----------

def test_offline_answers_are_paced_and_streamed_when_pacing_is_on():
    slept = []
    app = web.App({"demo": web.Source("Demo", DEMO, False)}, "demo", None, None, {}, offline_pace=True, sleep=slept.append)
    sess = app.session_for("a" * 16, "offline", "", "demo")
    events = []
    result = sess.run("Quais violões disponíveis custando até R$ 1.000?", emit=events.append)
    deltas = [e["text"] for e in events if e["type"] == "delta"]
    assert len(deltas) > 5 and "".join(deltas) == result["reply"], "the whole reply arrives as small chunks"
    assert slept and 0.3 <= slept[0] <= 1.3, "a short 'thinking' pause comes first"
    assert 0.6 <= sum(slept) <= 3.5, f"total artificial delay stays reasonable: {sum(slept):.2f}s"
    kinds = [e["type"] for e in events]
    assert kinds.index("tool") < kinds.index("delta"), "tools show before the text starts"


def test_offline_pacing_is_off_by_default_so_tests_and_scripts_stay_instant():
    slept = []
    app = web.App({"demo": web.Source("Demo", DEMO, False)}, "demo", None, None, {}, sleep=slept.append)
    sess = app.session_for("b" * 16, "offline", "", "demo")
    events = []
    sess.run("Oi", emit=events.append)
    assert slept == [] and not any(e["type"] == "delta" for e in events)


def test_the_page_states_that_offline_answers_come_from_rules():
    assert "respostas por regras" in web.PAGE
