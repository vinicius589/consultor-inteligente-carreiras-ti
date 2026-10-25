"""Executa todos os perfis de exemplo e gera a tabela de validação.

Uso:
    python tools/benchmark.py
    python tools/benchmark.py --saida docs/resultados-validacao.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from consultor.base_conhecimento import base_padrao  # noqa: E402
from consultor.cli import executar  # noqa: E402

EXEMPLOS = RAIZ / "exemplos"


def _pct(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",") + "%"


ROTULO_CONFIANCA = {"alta": "alta", "media": "média", "baixa": "baixa"}


def gerar_tabela() -> str:
    base = base_padrao()
    linhas = [
        "# Resultados de validação",
        "",
        "Saída de `python tools/benchmark.py`. Cada linha é um perfil de `exemplos/` executado "
        "pelo motor completo (ranking + lacunas + roadmap).",
        "",
        "| Perfil | 1º lugar | % | 2º lugar | % | Margem | Confiança | Empate | Estabilidade | Lacunas | Horas | Semanas |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for arquivo in sorted(EXEMPLOS.glob("*.json")):
        perfil = json.loads(arquivo.read_text(encoding="utf-8"))
        resultado, plano = executar(perfil, base)
        top, segundo = resultado.ranking[0], resultado.ranking[1]
        estabilidade = resultado.sensibilidade.get("estabilidade")
        linhas.append(
            f"| `{arquivo.name}` | {top.nome} | {_pct(top.percentual)} | {segundo.nome} | "
            f"{_pct(segundo.percentual)} | {f'{top.percentual - segundo.percentual:.1f}'.replace('.', ',')} | "
            f"{ROTULO_CONFIANCA.get(resultado.nivel_confianca, resultado.nivel_confianca)} "
            f"({f'{resultado.confianca:.2f}'.replace('.', ',')}) | "
            f"{'sim' if resultado.empate else 'não'} | "
            f"{f'{estabilidade * 100:.0f}%' if estabilidade is not None else '—'} | "
            f"{len(plano.analise.lacunas)} | {plano.horas_totais}h | {plano.semanas_estimadas} |"
        )
    linhas.append("")
    linhas.append(
        "> Perfis `perfil_neutro.json` e `perfil_conflitante.json` são casos-limite: o primeiro "
        "responde 3 em todas as perguntas (empate por ausência de evidência) e o segundo combina "
        "afinidades contraditórias (design + infraestrutura + matemática em nível máximo)."
    )
    linhas.append("")
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Roda os perfis de exemplo e gera a tabela de validação.")
    parser.add_argument("--saida", help="Arquivo Markdown de saída (padrão: stdout)")
    args = parser.parse_args(argv)

    tabela = gerar_tabela()
    if args.saida:
        destino = Path(args.saida)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(tabela, encoding="utf-8")
        print(f"Tabela escrita em {destino}")
    else:
        print(tabela)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
