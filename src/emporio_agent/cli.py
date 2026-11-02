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
    parser.add_argument("command", choices=["chat", "inspect", "serve"])
    parser.add_argument("--data-dir", default=None, help="Local CSV/PDF directory (default: data; data_public for serve)")
    parser.add_argument("--port", type=int, default=None, help="Port for the local web UI (serve only; default: first free from 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser automatically (serve only)")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible endpoint for the web UI (serve only)")
    parser.add_argument("--offline", action="store_true", help="Rule-based demonstration without LLM; limited intent coverage")
    parser.add_argument("--trace", action="store_true", help="Display tool names and status, not customer data")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    args = parser.parse_args(argv)

    if args.command == "serve":
        from .web import serve
        return serve(port=args.port, data_dir=args.data_dir or "data_public", base_url=args.base_url,
                     open_browser=not args.no_browser)
    data_dir = args.data_dir or "data"
    if args.command == "inspect":
        print(json.dumps(CSVStore(data_dir).inspect(), ensure_ascii=False, indent=2))
        return 0
    try:
        agent = OfflineAgent(Path(data_dir)) if args.offline else Agent(Path(data_dir), model=args.model)
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
