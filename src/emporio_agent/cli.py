"""Command-line interface. Use `python -m emporio_agent inspect|chat`."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from .agent import Agent
from .store import CSVStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Empório da Música | AI support prototype")
    parser.add_argument("command", choices=["chat", "inspect"])
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--trace", action="store_true", help="Print tool names and statuses only (no user data).")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-5.4-mini"))
    args = parser.parse_args(argv)

    if args.command == "inspect":
        print(json.dumps(CSVStore(args.data_dir).inspect(), ensure_ascii=False, indent=2))
        return 0
    try:
        agent = Agent(Path(args.data_dir), model=args.model)
    except Exception as exc:
        print(f"Failed to load local data: {exc}", file=sys.stderr)
        return 1
    if not agent.store.tables:
        print("AVISO: nenhum CSV encontrado. Adicione os dados originais em data/.")
    if not agent.policies.chunks:
        print("AVISO: PDF de políticas ausente. Respostas sobre regras serão limitadas.")
    print("Empório da Música — suporte virtual. Digite /sair para encerrar.")
    while True:
        try:
            message = input("\nCliente> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrado.")
            return 0
        if message.casefold() in {"/sair", "/exit", "quit"}:
            return 0
        if not message:
            continue
        try:
            response, trace = agent.reply(message)
        except Exception as exc:
            print(f"Erro ao consultar o provedor do modelo: {type(exc).__name__}. Confira sua API key, conexão e modelo.")
            return 1
        print(f"Atendente> {response}")
        if args.trace:
            print("[tools] " + json.dumps(trace, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
