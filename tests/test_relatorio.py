"""Testes da exportação Markdown/JSON."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from consultor.base_conhecimento import base_padrao
from consultor.cli import executar
from consultor.relatorio import gerar_json, gerar_markdown

EXEMPLOS = Path(__file__).resolve().parents[1] / "exemplos"


def _gerar(nome: str = "perfil_devops.json"):
    perfil = json.loads((EXEMPLOS / nome).read_text(encoding="utf-8"))
    base = base_padrao()
    resultado, plano = executar(perfil, base, com_sensibilidade=False)
    return base, perfil, resultado, plano


def test_markdown_contem_todas_as_secoes():
    base, perfil, resultado, plano = _gerar()
    texto = gerar_markdown(resultado, plano, base, perfil, hoje=date(2026, 10, 25))
    for secao in (
        "# Plano de carreira em TI",
        "## 1. Resultado da análise",
        "## 2. Ranking completo",
        "## 3. Por que essa trilha",
        "## 4. Perfil por eixo",
        "## 5. Lacunas para o nível",
        "## 6. Roadmap personalizado",
        "## 7. Certificações recomendadas",
        "## 8. Projetos para o portfólio",
        "## 9. Próximos passos",
        "## 10. Como o resultado foi calculado",
    ):
        assert secao in texto, secao
    assert resultado.top.nome in texto
    assert perfil["nome"] in texto
    assert "25/10/2026" in texto


def test_markdown_traz_links_de_certificacao_e_recursos():
    base, perfil, resultado, plano = _gerar()
    texto = gerar_markdown(resultado, plano, base, perfil)
    assert "https://" in texto
    assert "[AWS Certified" in texto or "](http" in texto


def test_json_e_serializavel_e_tem_chaves_esperadas():
    base, perfil, resultado, plano = _gerar()
    dados = gerar_json(resultado, plano, perfil)
    texto = json.dumps(dados, ensure_ascii=False)
    assert len(texto) > 1000
    assert dados["resultado"]["top"] == resultado.top.id
    assert len(dados["resultado"]["ranking"]) == 10
    assert len(dados["plano"]["fases"]) == 3
    assert "analise" in dados["plano"]


def test_markdown_de_empate_explica_o_desempate():
    base, perfil, resultado, plano = _gerar("perfil_conflitante.json")
    texto = gerar_markdown(resultado, plano, base, perfil)
    assert "Empate técnico" in texto
    assert "Pergunta que mais separa" in texto


def test_markdown_sem_nome_usa_valor_padrao():
    base, perfil, resultado, plano = _gerar()
    texto = gerar_markdown(resultado, plano, base, {})
    assert "Estudante" in texto
