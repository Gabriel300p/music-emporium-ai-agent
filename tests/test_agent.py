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
