"""Static checks for the one-command launchers.

The Windows launcher cannot be executed here, so the known ways a batch file breaks are ruled out by construction
(the CI workflow additionally runs it on a real Windows machine).
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BAT = ROOT / "run.bat"
SH = ROOT / "run.sh"


def bat_lines():
    return BAT.read_bytes().decode("ascii").split("\r\n")


def test_bat_is_ascii_with_crlf_only():
    raw = BAT.read_bytes()
    raw.decode("ascii")  # accents break cmd.exe code pages
    assert raw.count(b"\r\n") == raw.count(b"\n"), "every line must end in CRLF"
    assert b"\r" not in raw.replace(b"\r\n", b"")


def test_bat_has_no_parenthesised_blocks_and_no_parentheses_in_echo():
    """A ')' inside `echo` ends an enclosing `if (...)` block early; the fix is to avoid blocks altogether."""
    for number, line in enumerate(bat_lines(), start=1):
        stripped = line.strip()
        if stripped.lower().startswith(("echo ", "rem ")):
            assert "(" not in stripped and ")" not in stripped, f"run.bat:{number}: parenthesis in text: {stripped}"
        assert not stripped.endswith("("), f"run.bat:{number}: multi-line block: {stripped}"
        assert not stripped.startswith(")"), f"run.bat:{number}: block terminator: {stripped}"


def test_bat_gotos_have_labels_and_every_path_ends():
    text = "\n".join(bat_lines())
    labels = set(re.findall(r"^:(\w+)", text, re.M))
    targets = set(re.findall(r"goto :(\w+)", text, re.I))
    assert targets <= labels, f"missing labels: {targets - labels}"
    assert "exit /b" in text.lower()


def test_bat_keeps_its_environment_outside_the_project_folder():
    """The project may sit on a WSL/UNC share that also holds a Linux .venv; a Windows venv cannot live there."""
    text = "\n".join(bat_lines()).lower()
    assert "pushd" in text and "cd /d" not in text, "cd /d fails on UNC paths such as \\\\wsl$"
    assert "%localappdata%" in text and "emporioagent" in text
    code = "\n".join(line for line in text.splitlines() if not line.startswith("rem "))
    assert ".venv" not in code, "the project .venv (possibly created on Linux) must not be touched"


def test_bat_does_not_use_an_editable_install_that_would_record_a_temporary_drive_letter():
    text = "\n".join(bat_lines())
    assert "install -e" not in text and "pip install -e" not in text
    assert 'set "PYTHONPATH=%CD%\\src"' in text


def test_bat_dependency_pins_match_pyproject():
    text = "\n".join(bat_lines())
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    declared = re.search(r"^dependencies = \[(.*)\]$", pyproject, re.M).group(1)
    for requirement in re.findall(r'"([^"]+)"', declared):
        assert f'"{requirement}"' in text, f"run.bat must install {requirement}, as pyproject.toml declares"


def test_bat_forces_utf8_so_accents_and_dashes_print_on_any_windows_code_page():
    text = "\n".join(bat_lines())
    assert 'set "PYTHONUTF8=1"' in text and "chcp 65001" in text


def test_bat_looks_for_python_311_through_py_launcher_python_and_python3():
    text = "\n".join(bat_lines())
    for candidate in ("py -3 -c", "python -c", "python3 -c"):
        assert candidate in text
    assert "3, 11" in text


def test_sh_declares_bash_and_the_repository_forces_lf_for_it():
    assert SH.read_text(encoding="utf-8").splitlines()[0].startswith("#!/usr/bin/env bash")
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "*.sh text eol=lf" in attributes and "*.bat text eol=crlf" in attributes


@pytest.mark.skipif(sys.platform == "win32" or shutil.which("bash") is None, reason="run.sh only runs on Linux and macOS")
def test_sh_is_valid_bash_with_lf_line_endings():
    assert b"\r" not in SH.read_bytes(), "run.sh must use LF"
    subprocess.run(["bash", "-n", str(SH)], check=True)
