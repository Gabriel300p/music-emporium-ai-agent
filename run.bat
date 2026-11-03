@echo off
rem Emporio da Musica - atendente virtual.
rem Primeira execucao: cria o ambiente e instala. Leva cerca de 1 minuto. Depois abre a interface no navegador.
rem Uso: duplo clique em run.bat, ou run.bat --no-browser --port 9000
rem Sem blocos entre parenteses: um parentese dentro de um echo fecha o bloco antes da hora e quebra o arquivo.
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
pushd "%~dp0"
if errorlevel 1 goto :no_folder

set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto :have_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto :have_python
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=python3"
if defined PY goto :have_python

echo Nao encontrei o Python 3.11 ou superior neste computador.
echo Instale em https://www.python.org/downloads/ e marque a opcao Add python.exe to PATH.
echo Depois de instalar, de um duplo clique em run.bat de novo.
goto :fail

:have_python
if exist ".venv\Scripts\python.exe" goto :have_venv
if exist ".venv\bin\python" goto :linux_venv
echo Criando o ambiente - somente na primeira vez...
%PY% -m venv .venv
if errorlevel 1 goto :venv_fail

:have_venv
if exist ".venv\.instalado" goto :run
echo Instalando as dependencias - somente na primeira vez, precisa de internet...
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -e .
if errorlevel 1 goto :pip_fail
type nul > ".venv\.instalado"

:run
".venv\Scripts\python.exe" -m emporio_agent serve %*
set "RC=%errorlevel%"
if not "%RC%"=="0" echo O programa terminou com erro codigo %RC%.
if not "%RC%"=="0" goto :fail
popd
exit /b 0

:no_folder
echo Nao consegui entrar na pasta do projeto. Copie a pasta para o disco local, por exemplo C:\projetos, e tente de novo.
goto :fail

:linux_venv
echo A pasta .venv foi criada no Linux ou no WSL e nao serve no Windows.
echo Apague a pasta .venv e de um duplo clique em run.bat de novo.
goto :fail

:venv_fail
echo Nao consegui criar o ambiente virtual.
goto :fail

:pip_fail
echo A instalacao falhou. Verifique a conexao com a internet e tente de novo.
goto :fail

:fail
pause
popd
exit /b 1
