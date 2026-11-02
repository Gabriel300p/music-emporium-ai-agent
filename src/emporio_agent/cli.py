"""CLI: inspect schema, run LLM agent, or run a transparent offline demo."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .agent import Agent
from .offline import OfflineAgent
from .store import CSVStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Empório da Música: support assistant")
    parser.add_argument("command", choices=["chat", "inspect"])
    parser.add_argument("--data-dir", default="data", help="Local CSV/PDF directory")
    parser.add_argument("--offline", action="store_true", help="Rule-based demonstration without LLM; limited intent coverage")
    parser.add_argument("--trace", action="store_true", help="Display tool names and status, not customer data")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    args = parser.parse_args(argv)

    if args.command == "inspect":
        print(json.dumps(CSVStore(args.data_dir).inspect(), ensure_ascii=False, indent=2))
        return 0
    try:
        agent = OfflineAgent(Path(args.data_dir)) if args.offline else Agent(Path(args.data_dir), model=args.model)
    except Exception as exc:
        print(f"Unable to load local files: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if not agent.store.products:
        print("AVISO: nenhum CSV de produtos reconhecido.")
    if not agent.policies.chunks:
        print("AVISO: PDF de políticas ausente ou não legível.")
    print("Empório da Música — modo " + ("offline de demonstração" if args.offline else "LLM") + ". /sair para encerrar.")
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
            reply, trace = agent.reply(message)
        except Exception as exc:
            print(f"Erro ao consultar o modelo: {type(exc).__name__}. Verifique API key, modelo e conexão.")
            return 1
        print("Atendente> " + reply)
        if args.trace:
            print("[tools] " + json.dumps(trace, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
