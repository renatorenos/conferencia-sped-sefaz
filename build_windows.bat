@echo off
REM ============================================================
REM  Build script — Conferência SPED (Windows)
REM  Execute este arquivo em uma máquina Windows com Python 3.10+
REM ============================================================

echo [1/4] Criando ambiente virtual...
python -m venv .venv_build
call .venv_build\Scripts\activate.bat

echo [2/4] Instalando dependencias...
pip install --upgrade pip
pip install customtkinter xlrd openpyxl pyinstaller

echo [3/4] Gerando executavel...
pyinstaller conferencia_sped.spec --clean --noconfirm

echo [4/4] Concluido!
echo.
echo O executavel esta em: dist\ConferenciaSPED.exe
echo.
pause
