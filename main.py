"""Ponto de entrada de linha de comando.

Uso:
    python main.py --perfil exemplos/perfil_backend.json --saida plano.md

A interface principal do projeto é o Streamlit (``app.py``); este script existe
para demonstrar o motor sem interface gráfica e para gerar relatórios em lote.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from consultor.cli import main  # noqa: E402  (import após ajuste de sys.path)


if __name__ == "__main__":
    raise SystemExit(main())
