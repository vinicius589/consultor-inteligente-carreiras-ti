"""Interface de linha de comando do consultor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .base_conhecimento import BaseConhecimento, ErroBaseConhecimento, base_padrao, carregar_base
from .motor import Resultado, avaliar
from .relatorio import gerar_json, gerar_markdown
from .roadmap import PlanoAcao, gerar_plano


def carregar_perfil(caminho: str | Path) -> dict[str, Any]:
    """Lê um perfil de exemplo em JSON e valida a estrutura mínima."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Perfil não encontrado: {caminho}")
    with caminho.open(encoding="utf-8") as arquivo:
        perfil = json.load(arquivo)
    if not isinstance(perfil, dict):
        raise ValueError("O perfil deve ser um objeto JSON")
    if not perfil.get("respostas"):
        raise ValueError("O perfil precisa da chave 'respostas' com as notas de afinidade")
    return perfil


def executar(
    perfil: dict[str, Any],
    base: BaseConhecimento | None = None,
    com_sensibilidade: bool = True,
) -> tuple[Resultado, PlanoAcao]:
    """Executa o motor e o gerador de plano para um perfil já carregado."""
    base = base or base_padrao()
    respostas = perfil.get("respostas") or {}
    nivel_alvo = perfil.get("nivel_alvo", "junior")
    resultado = avaliar(
        base,
        respostas,
        objetivo=perfil.get("objetivo"),
        modalidade=perfil.get("modalidade"),
        nivel_alvo=nivel_alvo,
        com_sensibilidade=com_sensibilidade,
    )
    plano = gerar_plano(
        base,
        resultado.top.id,
        perfil.get("conhecimentos") or {},
        nivel_alvo=nivel_alvo,
        horas_semana=int(perfil.get("horas_semana") or 10),
        prazo_meses=int(perfil.get("prazo_meses") or 6),
        objetivo=perfil.get("objetivo"),
    )
    return resultado, plano


def _num(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _resumo_console(resultado: Resultado, plano: PlanoAcao, base: BaseConhecimento) -> str:
    linhas: list[str] = []
    linhas.append("Consultor Inteligente de Carreiras em TI — motor v2")
    linhas.append("")
    linhas.append("Ranking de compatibilidade")
    for posicao, avaliada in enumerate(resultado.ranking, start=1):
        marca = "  ← recomendada" if posicao == 1 else ""
        linhas.append(f"  {posicao:>2}. {avaliada.nome:<38} {_num(avaliada.percentual):>5}%{marca}")
    linhas.append("")
    linhas.append(
        f"Confiança: {resultado.nivel_confianca} ({_num(resultado.confianca, 2)}) · "
        f"empate técnico: {'sim' if resultado.empate else 'não'}"
    )
    if resultado.sensibilidade.get("estabilidade") is not None:
        linhas.append(
            f"Estabilidade do 1º lugar: {resultado.sensibilidade['estabilidade'] * 100:.0f}% "
            "das variações de ±1 ponto"
        )
    linhas.append("")
    analise = plano.analise
    linhas.append(
        f"Lacunas para {base.niveis[plano.nivel_alvo]['rotulo']} em {plano.trilha_nome}: "
        f"{len(analise.lacunas)} ({len(analise.criticas)} críticas) · cobertura {analise.cobertura:.0f}%"
    )
    plural = "fase" if len(plano.fases) == 1 else "fases"
    linhas.append(
        f"Plano: {len(plano.fases)} {plural} · {plano.horas_totais}h · ~{plano.semanas_estimadas} semanas "
        f"a {plano.horas_semana}h/semana"
    )
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Consultor Inteligente de Carreiras em TI (motor de inferência ponderada)."
    )
    parser.add_argument("--perfil", required=True, help="Arquivo JSON com o perfil do usuário")
    parser.add_argument("--base", help="Pasta com os arquivos JSON da base de conhecimento")
    parser.add_argument("--saida", default="plano-carreira.md", help="Arquivo Markdown de saída")
    parser.add_argument("--json", dest="saida_json", help="Arquivo JSON de saída (opcional)")
    parser.add_argument("--rapido", action="store_true", help="Pula a análise de sensibilidade")
    args = parser.parse_args(argv)

    try:
        base = carregar_base(args.base) if args.base else base_padrao()
        perfil = carregar_perfil(args.perfil)
        resultado, plano = executar(perfil, base, com_sensibilidade=not args.rapido)
    except (ErroBaseConhecimento, ValueError, FileNotFoundError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 2

    print(_resumo_console(resultado, plano, base))
    print("")

    destino = Path(args.saida)
    destino.write_text(gerar_markdown(resultado, plano, base, perfil), encoding="utf-8")
    print(f"Relatório Markdown: {destino}")

    if args.saida_json:
        caminho_json = Path(args.saida_json)
        caminho_json.write_text(
            json.dumps(gerar_json(resultado, plano, perfil), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Resultado JSON: {caminho_json}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
