@echo off
rem Emporio da Musica - atendente virtual.
rem Primeira execucao: cria o ambiente e instala. Leva cerca de 1 minuto. Depois abre a interface no navegador.
rem Uso: duplo clique em run.bat, ou run.bat --no-browser --port 9000
rem O ambiente fica em %LOCALAPPDATA%\EmporioAgent, fora da pasta do projeto: a pasta pode estar num compartilhamento
rem do WSL, onde ja existe uma .venv do Linux e onde um ambiente do Windows nao funciona.
rem Sem blocos entre parenteses: um parentese dentro de um echo fecha o bloco antes da hora e quebra o arquivo.
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
pushd "%~dp0"
if errorlevel 1 goto :no_folder
if not exist "src\emporio_agent\__init__.py" goto :wrong_folder

set "BASE=%LOCALAPPDATA%"
if not defined BASE set "BASE=%USERPROFILE%"
if not defined BASE set "BASE=%TEMP%"
set "BASE=%BASE%\EmporioAgent"
set "VENV=%BASE%\venv"
set "MARK=%BASE%\instalado-v2"

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
if exist "%VENV%\Scripts\python.exe" goto :have_venv
if not exist "%BASE%" mkdir "%BASE%"
echo Criando o ambiente em %VENV% - somente na primeira vez...
%PY% -m venv "%VENV%"
if errorlevel 1 goto :venv_fail

:have_venv
if exist "%MARK%" goto :run
echo Instalando as dependencias - somente na primeira vez, precisa de internet...
"%VENV%\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check "openai>=2.0,<4.0" "pypdf>=5.0,<7.0"
if errorlevel 1 goto :pip_fail
type nul > "%MARK%"

:run
set "PYTHONPATH=%CD%\src"
"%VENV%\Scripts\python.exe" -m emporio_agent serve %*
set "RC=%errorlevel%"
if not "%RC%"=="0" echo O programa terminou com erro codigo %RC%.
if not "%RC%"=="0" goto :fail
popd
exit /b 0

:no_folder
echo Nao consegui entrar na pasta do projeto: %~dp0
echo Copie a pasta para o disco local, por exemplo C:\projetos, e tente de novo.
goto :fail

:wrong_folder
echo Nao encontrei a pasta src do projeto ao lado do run.bat.
echo Execute o run.bat de dentro da pasta completa do projeto, sem mover o arquivo.
goto :fail

:venv_fail
echo Nao consegui criar o ambiente virtual em %VENV%.
goto :fail

:pip_fail
echo A instalacao falhou. Verifique a conexao com a internet e tente de novo.
goto :fail

:fail
pause
popd
exit /b 1
