"""Terminal chat loop: it must survive an API error and keep the conversation."""
from pathlib import Path

from emporio_agent import cli

DEMO = Path(__file__).resolve().parents[1] / "demo_data"


class FlakyAgent:
    def __init__(self, *_, **__):
        self.calls = 0
        self.store = type("S", (), {"products": object()})()
        self.policies = type("P", (), {"chunks": [1]})()

    def reply(self, message):
        self.calls += 1
        if self.calls == 1:
            raise ConnectionError("rede caiu")
        return "resposta " + message, [{"tool": "search_products", "status": "ok"}]


def run_chat(monkeypatch, capsys, lines, argv):
    feed = iter(lines)
    monkeypatch.setattr("builtins.input", lambda *_: next(feed))
    code = cli.main(argv)
    return code, capsys.readouterr()


def test_an_api_error_does_not_end_the_session(monkeypatch, capsys):
    monkeypatch.setattr(cli, "Agent", FlakyAgent)
    code, out = run_chat(monkeypatch, capsys, ["primeira", "segunda", "/sair"], ["chat", "--data-dir", str(DEMO), "--trace"])
    assert code == 0
    assert "ConnectionError" in out.out and "tente de novo" in out.out.lower()
    assert "Atendente> resposta segunda" in out.out
    assert '[tools] [{"tool": "search_products", "status": "ok"}]' in out.out


def test_the_error_message_never_prints_the_exception_text(monkeypatch, capsys):
    class Leaky(FlakyAgent):
        def reply(self, message):
            raise RuntimeError("Incorrect API key provided: placeholder-secret-value")

    monkeypatch.setattr(cli, "Agent", Leaky)
    _, out = run_chat(monkeypatch, capsys, ["oi", "/sair"], ["chat", "--data-dir", str(DEMO)])
    assert "placeholder-secret-value" not in out.out + out.err


def test_offline_chat_answers_and_exits_on_eof(monkeypatch, capsys):
    def eof(*_):
        raise EOFError

    feed = iter(["Quanto custa o Takamine GD20?"])
    monkeypatch.setattr("builtins.input", lambda *_: next(feed, None) or eof())
    code = cli.main(["chat", "--data-dir", str(DEMO), "--offline", "--trace"])
    out = capsys.readouterr().out
    assert code == 0 and "Atendente>" in out and "Encerrado." in out


def test_inspect_prints_the_recognised_tables(capsys):
    assert cli.main(["inspect", "--data-dir", str(DEMO)]) == 0
    assert '"products"' in capsys.readouterr().out


def test_missing_data_is_warned_about_not_raised(monkeypatch, capsys):
    def eof(*_):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert cli.main(["chat", "--data-dir", "/nonexistent-folder-xyz", "--offline"]) == 0
    assert "AVISO" in capsys.readouterr().out
