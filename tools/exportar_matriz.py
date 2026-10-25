"""Gera a matriz de pesos (perguntas × trilhas) em Markdown a partir do JSON.

Uso:
    python tools/exportar_matriz.py            # imprime no terminal
    python tools/exportar_matriz.py --saida docs/matriz-de-pesos.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from consultor.base_conhecimento import base_padrao  # noqa: E402

ABREVIACOES = {
    "backend": "Back",
    "frontend": "Front",
    "dados_ml": "Dados",
    "eng_dados": "EngDados",
    "seguranca": "Seg",
    "devops": "DevOps",
    "cloud": "Cloud",
    "mobile": "Mobile",
    "qa": "QA",
    "produto": "Prod",
}


def _numero(valor: float) -> str:
    if abs(valor) < 0.005:
        return "—"
    return f"{valor:.2f}".replace(".", ",")


def gerar_markdown() -> str:
    base = base_padrao()
    ids = list(base.ids_trilhas)
    linhas: list[str] = []

    linhas.append("# Matriz de pesos — perguntas × trilhas")
    linhas.append("")
    linhas.append(
        "Gerada automaticamente a partir de `data/perguntas.json` por "
        "`python tools/exportar_matriz.py`. Cada célula indica o peso da pergunta na trilha: "
        "valores positivos aproximam o perfil da trilha; valores negativos afastam. "
        "O traço (—) indica que a pergunta não pontua naquela trilha."
    )
    linhas.append("")
    linhas.append("## Perguntas de afinidade")
    linhas.append("")
    cabecalho = "| # | Pergunta | Dimensão | " + " | ".join(ABREVIACOES.get(i, i) for i in ids) + " |"
    linhas.append(cabecalho)
    linhas.append("|" + "---|" * (len(ids) + 3))
    for indice, pergunta in enumerate(base.perguntas, start=1):
        celulas = " | ".join(_numero(pergunta.peso_para(t)) for t in ids)
        linhas.append(
            f"| {indice} | {pergunta.texto} | {base.dimensoes.get(pergunta.dimensao, pergunta.dimensao)} | {celulas} |"
        )
    linhas.append("")

    linhas.append("## Perfil de dimensões por trilha")
    linhas.append("")
    dimensoes = list(base.dimensoes)
    linhas.append("| Dimensão | " + " | ".join(ABREVIACOES.get(i, i) for i in ids) + " |")
    linhas.append("|" + "---|" * (len(ids) + 1))
    for dimensao in dimensoes:
        valores = " | ".join(_numero(base.trilha(t).dimensoes.get(dimensao, 0.0)) for t in ids)
        linhas.append(f"| {base.dimensoes[dimensao]} | {valores} |")
    linhas.append("")

    linhas.append("## Estatísticas de cobertura")
    linhas.append("")
    linhas.append("| Trilha | Perguntas com peso | Peso positivo total | Peso negativo total |")
    linhas.append("|---|---|---|---|")
    for trilha_id in ids:
        pesos = [base.perguntas[i].peso_para(trilha_id) for i in range(len(base.perguntas))]
        positivos = sum(p for p in pesos if p > 0)
        negativos = sum(p for p in pesos if p < 0)
        linhas.append(
            f"| {base.trilha(trilha_id).nome} | {sum(1 for p in pesos if p)} | "
            f"{_numero(positivos)} | {_numero(negativos)} |"
        )
    linhas.append("")
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Exporta a matriz de pesos em Markdown.")
    parser.add_argument("--saida", help="Arquivo de saída (padrão: stdout)")
    args = parser.parse_args(argv)

    texto = gerar_markdown()
    if args.saida:
        destino = Path(args.saida)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")
        print(f"Matriz escrita em {destino}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
