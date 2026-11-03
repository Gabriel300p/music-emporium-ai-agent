import json
from pathlib import Path
from types import SimpleNamespace

from emporio_agent.agent import Agent

ROOT = Path(__file__).parent / "fixtures" / "data"


class FakeResponseAPI:
    """Emulates tool round-trip; NO LLM output is presented as real validation."""
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            call = SimpleNamespace(type="function_call", name="search_products", call_id="test_call_01",
                                   arguments=json.dumps({"query": None, "category": "violões", "max_price": 1000, "in_stock_only": True}))
            return SimpleNamespace(output=[call], output_text="")
        return SimpleNamespace(output=[SimpleNamespace(type="message", role="assistant", content=[])],
                               output_text="Encontrei uma opção de violão até R$1.000.")


class FakeClient:
    def __init__(self):
        self.responses = FakeResponseAPI()


def test_agent_executes_tool_and_passes_results_to_model():
    fake = FakeClient()
    agent = Agent(ROOT, client=fake)
    answer, trace = agent.reply("Quais violões até R$1.000 estão em estoque?")
    assert "violão" in answer
    assert trace == [{"tool": "search_products", "status": "ok"}]
    next_input = fake.responses.calls[1]["input"]
    results = [i for i in next_input if isinstance(i, dict) and i.get("type") == "function_call_output"]
    assert len(results) == 1
    assert json.loads(results[0]["output"])["products"][0]["name"] == "Violão Acústico XPTO"
    assert fake.responses.calls[0]["store"] is False


class _FakeStream:
    """Context manager shaped like the SDK's response stream: iterate events, then get_final_response()."""

    def __init__(self, response, deltas):
        self.response, self.deltas = response, deltas

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        for d in self.deltas:
            yield SimpleNamespace(type="response.output_text.delta", delta=d)
        yield SimpleNamespace(type="response.completed")

    def get_final_response(self):
        return self.response


class FakeStreamingAPI(FakeResponseAPI):
    def __init__(self):
        super().__init__()
        self.streamed = 0

    def create(self, **kwargs):  # must not be used when the caller asks for streaming
        raise AssertionError("create() called although streaming was requested")

    def stream(self, **kwargs):
        self.streamed += 1
        self.calls.append(kwargs)
        if self.streamed == 1:
            call = SimpleNamespace(type="function_call", name="search_products", call_id="test_call_01",
                                   arguments=json.dumps({"query": None, "category": "violões", "max_price": 1000, "in_stock_only": True}))
            return _FakeStream(SimpleNamespace(output=[call], output_text=""), [])
        text = "Encontrei uma opção de violão até R$1.000."
        return _FakeStream(SimpleNamespace(output=[SimpleNamespace(type="message", role="assistant", content=[])], output_text=text),
                           [text[:11], text[11:]])


def test_agent_streams_only_the_final_answer_text():
    api = FakeStreamingAPI()
    agent = Agent(ROOT, client=SimpleNamespace(responses=api))
    deltas = []
    answer, trace = agent.reply("Quais violões até R$1.000 estão em estoque?", on_text=deltas.append)
    assert answer == "Encontrei uma opção de violão até R$1.000."
    assert "".join(deltas) == answer and len(deltas) == 2, "only the final round streams text"
    assert trace == [{"tool": "search_products", "status": "ok"}]
    assert api.streamed == 2


def test_agent_without_streaming_support_still_answers():
    fake = FakeClient()  # only has create(); on_text must not break it
    agent = Agent(ROOT, client=fake)
    deltas = []
    answer, _ = agent.reply("Quais violões até R$1.000 estão em estoque?", on_text=deltas.append)
    assert "violão" in answer and deltas == []


# ---------- error paths of the loop ----------

def _tool_call(name, arguments, call_id="c1"):
    return SimpleNamespace(type="function_call", name=name, call_id=call_id, arguments=arguments)


class ScriptedAPI:
    """Returns the scripted responses in order; every create() call is recorded."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _agent(*responses):
    api = ScriptedAPI(*responses)
    return Agent(ROOT, client=SimpleNamespace(responses=api)), api


def _final(text="ok"):
    return SimpleNamespace(output=[SimpleNamespace(type="message")], output_text=text)


def _calling(*calls):
    return SimpleNamespace(output=list(calls), output_text="")


def test_invalid_tool_arguments_become_an_error_result_not_a_crash():
    for bad in ("{not json", "[1, 2]", '"text"', "null"):
        agent, api = _agent(_calling(_tool_call("search_products", bad)), _final())
        answer, trace = agent.reply("oi")
        assert answer == "ok" and trace == [{"tool": "search_products", "status": "error"}], bad
        sent = [i for i in api.calls[1]["input"] if isinstance(i, dict) and i.get("type") == "function_call_output"]
        assert json.loads(sent[0]["output"])["reason"] == "Invalid tool parameters"


def test_unknown_tool_is_reported_to_the_model():
    agent, api = _agent(_calling(_tool_call("delete_everything", "{}")), _final())
    _, trace = agent.reply("oi")
    assert trace == [{"tool": "delete_everything", "status": "error"}]


def test_parallel_tool_calls_all_get_an_output():
    agent, api = _agent(_calling(_tool_call("search_promotions", "{}", "a"), _tool_call("search_promotions", "{}", "b")), _final())
    _, trace = agent.reply("oi")
    ids = [i["call_id"] for i in api.calls[1]["input"] if isinstance(i, dict) and i.get("type") == "function_call_output"]
    assert ids == ["a", "b"] and len(trace) == 2


def test_the_loop_gives_up_after_six_rounds_with_a_safe_message():
    agent, api = _agent(*[_calling(_tool_call("search_promotions", "{}", f"c{i}")) for i in range(6)])
    answer, trace = agent.reply("oi")
    assert len(api.calls) == 6 and len(trace) == 6
    assert "equipe" in answer.lower()
    assert agent.history == [], "an incomplete turn is not remembered"


def test_empty_message_does_not_call_the_model():
    agent, api = _agent()
    assert agent.reply("   ")[0].startswith("Pode me contar")
    assert api.calls == []


def test_empty_model_answer_falls_back_to_a_handoff_message():
    agent, _ = _agent(_final(""))
    assert "equipe" in agent.reply("oi")[0].lower()


def test_an_api_error_propagates_and_leaves_the_history_untouched():
    agent, _ = _agent(_final("primeira"), RuntimeError("boom"), _final("terceira"))
    agent.reply("um")
    before = list(agent.history)
    try:
        agent.reply("dois")
    except RuntimeError:
        pass
    else:
        raise AssertionError("the error must reach the caller")
    assert agent.history == before
    assert agent.reply("três")[0] == "terceira", "the conversation continues after the failure"
