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
