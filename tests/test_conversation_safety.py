"""Per-conversation safety: verification attempts are limited and the history never breaks the next request."""
import json
import random
from pathlib import Path
from types import SimpleNamespace

from emporio_agent.agent import MAX_HISTORY_ITEMS, Agent, trim_history
from emporio_agent.offline import OfflineAgent
from emporio_agent.store import CSVStore, GuardedStore

DEMO = Path(__file__).resolve().parents[1] / "demo_data"
GOOD = {"order_number": "1001", "customer_email": "ana@example.test"}
BAD = {"order_number": "1001", "customer_email": "outra.pessoa@example.com"}


# ---------- limited verification attempts ----------

def test_three_wrong_emails_lock_the_conversation_even_for_the_right_one():
    store = GuardedStore(CSVStore(DEMO))
    assert [store.order_status(**BAD)["status"] for _ in range(3)] == ["not_verified"] * 3
    locked = store.order_status(**GOOD)
    assert locked["status"] == "locked"
    assert "equipe" in locked["message"].lower()
    assert "tracking_code" not in locked and "items" not in locked


def test_a_success_resets_the_counter():
    store = GuardedStore(CSVStore(DEMO))
    store.order_status(**BAD)
    store.order_status(**BAD)
    assert store.order_status(**GOOD)["status"] == "verified"
    assert [store.order_status(**BAD)["status"] for _ in range(2)] == ["not_verified"] * 2
    assert store.order_status(**GOOD)["status"] == "verified", "two failures after a success are still allowed"


def test_missing_fields_do_not_count_as_failed_attempts():
    store = GuardedStore(CSVStore(DEMO))
    for _ in range(10):
        assert store.order_status(order_number="1001", customer_email="")["status"] == "verification_required"
    assert store.order_status(**GOOD)["status"] == "verified"


def test_conversations_have_independent_counters_over_one_shared_store():
    shared = CSVStore(DEMO)
    first, second = GuardedStore(shared), GuardedStore(shared)
    for _ in range(3):
        first.order_status(**BAD)
    assert first.order_status(**GOOD)["status"] == "locked"
    assert second.order_status(**GOOD)["status"] == "verified"


def test_guarded_store_delegates_everything_else_unchanged():
    shared = CSVStore(DEMO)
    guarded = GuardedStore(shared)
    assert guarded.search_products(query="violão") == shared.search_products(query="violão")
    assert guarded.products is shared.products
    assert guarded.inner is shared


def test_agent_dispatch_reports_locked_in_the_trace():
    calls = {"n": 0}

    class API:
        def create(self, **kw):
            calls["n"] += 1
            if isinstance(kw["input"][-1], dict) and kw["input"][-1].get("type") == "function_call_output":
                return SimpleNamespace(output=[SimpleNamespace(type="message")], output_text="ok")
            return SimpleNamespace(output=[SimpleNamespace(type="function_call", name="order_status", call_id=f"c{calls['n']}",
                                                           arguments=json.dumps(BAD))], output_text="")

    agent = Agent(DEMO, client=SimpleNamespace(responses=API()))
    statuses = [agent.reply("pedido 1001")[1][0]["status"] for _ in range(4)]
    assert statuses == ["not_verified", "not_verified", "not_verified", "locked"]


def test_offline_agent_locks_after_three_wrong_emails_and_says_so():
    agent = OfflineAgent(DEMO)
    for _ in range(3):
        agent.reply("Qual o status do pedido 1001?")
        reply, trace = agent.reply("meu email é outra.pessoa@example.com")
        assert trace[0]["status"] == "not_verified"
    agent.reply("Qual o status do pedido 1001?")
    reply, trace = agent.reply("meu email é ana@example.test")
    assert trace == [{"tool": "order_status", "status": "locked"}]
    assert "equipe" in reply.lower() and "DEMO" not in reply


# ---------- history trimming ----------

def conversation(seed, turns):
    """History items as the Responses API produces them: user dicts, function calls/outputs, assistant messages."""
    rng = random.Random(seed)
    items = []
    for t in range(turns):
        items.append({"role": "user", "content": f"pergunta {t}"})
        for k in range(rng.choice([0, 1, 2])):
            cid = f"c{t}_{k}"
            items.append(SimpleNamespace(type="function_call", name="search_promotions", call_id=cid, arguments="{}"))
            items.append({"type": "function_call_output", "call_id": cid, "output": "{}"})
        items.append(SimpleNamespace(type="message", role="assistant"))
    return items


def is_user(item):
    return isinstance(item, dict) and item.get("role") == "user"


def calls_and_outputs(items):
    calls = {getattr(i, "call_id", None) for i in items if getattr(i, "type", None) == "function_call"}
    outs = {i["call_id"] for i in items if isinstance(i, dict) and i.get("type") == "function_call_output"}
    return calls, outs


def test_trim_never_starts_mid_turn_and_never_orphans_a_tool_output():
    for seed in range(300):
        items = conversation(seed, turns=40)
        trimmed = trim_history(items, 60)
        assert is_user(trimmed[0]), f"seed {seed}: starts with {trimmed[0]!r}"
        calls, outs = calls_and_outputs(trimmed)
        assert outs <= calls, f"seed {seed}: outputs without their call"
        assert trimmed == items[len(items) - len(trimmed):], "it only drops from the front"
        assert len(trimmed) <= 60 + 8, "bounded (one extra turn at most)"


def test_trim_keeps_short_histories_untouched():
    items = conversation(1, turns=3)
    assert trim_history(items, 60) is items or trim_history(items, 60) == items


def test_trim_with_a_single_huge_turn_keeps_that_turn_whole():
    items = [{"role": "user", "content": "oi"}]
    for k in range(40):
        items.append(SimpleNamespace(type="function_call", name="x", call_id=f"c{k}", arguments="{}"))
        items.append({"type": "function_call_output", "call_id": f"c{k}", "output": "{}"})
    trimmed = trim_history(items, 20)
    assert is_user(trimmed[0]) and len(trimmed) == len(items)


def test_agent_history_stays_valid_across_a_long_conversation():
    rng = random.Random(7)

    class API:
        n = 0

        def create(self, **kw):
            self.n += 1
            last = kw["input"][-1]
            if isinstance(last, dict) and last.get("type") == "function_call_output":
                return SimpleNamespace(output=[SimpleNamespace(type="message")], output_text="ok")
            k = rng.choice([0, 1, 2])
            if k == 0:
                return SimpleNamespace(output=[SimpleNamespace(type="message")], output_text="ok")
            return SimpleNamespace(output=[SimpleNamespace(type="function_call", name="search_promotions", call_id=f"c{self.n}_{i}",
                                                           arguments="{}") for i in range(k)], output_text="")

    agent = Agent(DEMO, client=SimpleNamespace(responses=API()))
    for _ in range(80):
        agent.reply("promoções?")
        assert is_user(agent.history[0])
        calls, outs = calls_and_outputs(agent.history)
        assert outs <= calls
        assert len(agent.history) <= MAX_HISTORY_ITEMS + 8
