@echo off
rem Emporio da Musica - atendente virtual.
rem Primeira execucao: cria o ambiente e instala (cerca de 1 minuto). Depois abre a interface no navegador.
rem Uso: de um duplo clique em run.bat, ou execute: run.bat --no-browser --port 9000
setlocal
cd /d "%~dp0"

set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
  if not errorlevel 1 set "PY=python3"
)
if not defined PY (
  echo Nao encontrei o Python 3.11 ou superior neste computador.
  echo Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
  echo Depois de instalar, de um duplo clique em run.bat de novo.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando o ambiente (somente na primeira vez)...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo Nao consegui criar o ambiente virtual.
    pause
    exit /b 1
  )
)

if not exist ".venv\.instalado" (
  echo Instalando as dependencias (somente na primeira vez, precisa de internet)...
  ".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -e .
  if errorlevel 1 (
    echo A instalacao falhou. Verifique a conexao com a internet e tente de novo.
    pause
    exit /b 1
  )
  type nul > ".venv\.instalado"
)

".venv\Scripts\python.exe" -m emporio_agent serve %*
if errorlevel 1 pause
