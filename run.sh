#!/usr/bin/env bash
# Empório da Música - atendente virtual.
# Primeira execução: cria o ambiente e instala (cerca de 1 minuto). Depois abre a interface no navegador.
# Uso:  ./run.sh            (ou: bash run.sh)
#       ./run.sh --no-browser --port 9000
set -e
cd "$(dirname "$0")"

PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PY="$candidate"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "Não encontrei o Python 3.11 ou superior neste computador."
  echo "Instale em https://www.python.org/downloads/ e rode ./run.sh de novo."
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "Criando o ambiente (somente na primeira vez)..."
  if ! "$PY" -m venv .venv; then
    echo "Não consegui criar o ambiente virtual."
    echo "No Debian/Ubuntu, instale com: sudo apt install python3-venv"
    exit 1
  fi
fi

if [ ! -f .venv/.instalado ] || [ pyproject.toml -nt .venv/.instalado ]; then
  echo "Instalando as dependências (somente na primeira vez, precisa de internet)..."
  if ! .venv/bin/python -m pip install --quiet --disable-pip-version-check -e .; then
    echo "A instalação falhou. Verifique a conexão com a internet e rode ./run.sh de novo."
    exit 1
  fi
  touch .venv/.instalado
fi

exec .venv/bin/python -m emporio_agent serve "$@"
