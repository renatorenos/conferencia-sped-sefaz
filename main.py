#!/usr/bin/env python3
"""
Conferência SPED — ponto de entrada.

Uso:
    python main.py
    # ou com a venv:
    .venv/bin/python main.py
"""
import sys
import os

# Garante que o diretório do projeto está no path
sys.path.insert(0, os.path.dirname(__file__))

from src.gui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
