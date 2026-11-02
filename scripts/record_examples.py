"""Generate REAL interactions after obtaining source CSV/PDF and API access.

Examples are not shipped with invented LLM output. Do not run in fixture mode
for the public deliverable; examples must use original challenge source data.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from emporio_agent.agent import Agent

QUESTIONS = [
    ("01_catalogo", "Quais opções de violões disponíveis custando até R$ 1.000?"),
    ("02_preco", "Quanto custa o Takamine GD20?"),
    ("03_horarios", "Quais são os horários de funcionamento e o endereço da loja?"),
    ("04_devolucao", "Me arrependi da minha compra. Posso devolver o pedido? Como funciona?"),
    ("05_fora_escopo", "Qual a previsão do tempo para amanhã em Curitiba?"),
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data")
    p.add_argument("--out-dir", default="examples")
    args = p.parse_args()
    agent = Agent(args.data_dir)
    if not agent.store.products or not agent.policies.chunks:
        raise SystemExit("Original product CSV and store policy PDF are required to record final examples.")
    output = Path(args.out_dir)
    output.mkdir(exist_ok=True, parents=True)
    for name, question in QUESTIONS:
        # New session per example; each one documents precisely one run.
        agent.history = []
        answer, trace = agent.reply(question)
        used = ", ".join(t["tool"] for t in trace) if trace else "none"
        body = f"# Example: {name}\n\n**Customer:** {question}\n\n**Assistant:** {answer}\n\n**Tools invoked:** {used}\n\n"
        (output / (name + ".md")).write_text(body, encoding="utf-8")
        print("Recorded:", output / (name + ".md"))

if __name__ == "__main__":
    main()
