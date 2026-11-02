"""Produce five REAL, reproducible OFFLINE DEMO transcripts (not live LLM outputs).

The source data is entirely synthetic and included in demo_data/. Capturing
actual OfflineAgent responses is more honest than writing fabricated model output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from emporio_agent.offline import OfflineAgent

CASES = [
    ("01_catalogue_budget", ["Quais violões disponíveis custando até R$ 1.000?"]),
    ("02_model_and_out_of_scope", ["Quanto custa o Takamine GD20?", "Qual será o tempo amanhã em Curitiba?"]),
    ("03_promotions", ["Quais promoções estão ativas no momento?"]),
    ("04_return_policy", ["Me arrependi da compra online, posso devolver?"]),
    ("05_order_verification", ["Qual o status do pedido 1001?", "Meu email é wrong@example.test",
                               "Qual o status do pedido 1001?", "Meu email é ana@example.test"]),
]


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--data-dir", default="demo_data")
    cli.add_argument("--out-dir", default="examples")
    args = cli.parse_args()
    dest = Path(args.out_dir)
    dest.mkdir(exist_ok=True, parents=True)
    for name, questions in CASES:
        agent = OfflineAgent(Path(args.data_dir))  # isolated session
        lines = [f"# {name.replace('_', ' ').title()}",
                 "", "> **Execution mode:** offline deterministic demonstration. "
                 "**Data:** 100% synthetic `demo_data/`. This is NOT a live LLM response.", ""]
        for question in questions:
            answer, trace = agent.reply(question)
            lines.extend([f"**Customer:** {question}", "", f"**Assistant:** {answer}", "",
                          "**Executed tools (name/status only):** " + json.dumps(trace, ensure_ascii=False), ""])
        (dest / f"{name}.md").write_text("\n".join(lines), encoding="utf-8")
        print("Wrote", dest / f"{name}.md")


if __name__ == "__main__":
    main()
