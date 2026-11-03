"""Optional: collect live LLM conversations after configuring OPENAI_API_KEY.

DO NOT run against private order/customer data for a public transcript.
Always manually verify answers and redact any confidential details before sharing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from emporio_agent.agent import Agent

QUESTIONS = [
    ("catalogue", "Quais violões disponíveis custando até R$ 1.000?"),
    ("model", "Quanto custa o Takamine GD20?"),
    ("promotion", "Há descontos ativos? O desconto de PIX acumula?"),
    ("returns", "Comprei um instrumento online e me arrependi. Como funciona a devolução?"),
    ("out_of_scope", "Qual é a previsão do tempo para amanhã?"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="demo_data")
    parser.add_argument("--out-dir", default="live_examples_local_only")
    args = parser.parse_args()
    target = Path(args.out_dir)
    target.mkdir(exist_ok=True, parents=True)
    for name, question in QUESTIONS:
        agent = Agent(args.data_dir)
        answer, trace = agent.reply(question)
        path = target / f"{name}.md"
        path.write_text("\n".join([
            f"# {name}", "", "> Captured live Responses API output. Human verification pending.", "",
            f"**Customer:** {question}", "", f"**Assistant:** {answer}", "",
            "**Tool trace:** " + json.dumps(trace, ensure_ascii=False), "",
        ]), encoding="utf-8")
        print("Recorded", path)


if __name__ == "__main__":
    main()
