"""Testes de robustez: perfis ambíguos, neutros e contraditórios."""

from __future__ import annotations

import json
from pathlib import Path

from consultor.base_conhecimento import base_padrao
from consultor.motor import avaliar

EXEMPLOS = Path(__file__).resolve().parents[1] / "exemplos"


def _carregar(nome: str) -> dict:
    return json.loads((EXEMPLOS / nome).read_text(encoding="utf-8"))


def test_perfil_neutro_gera_empate_tecnico_e_baixa_confianca():
    base = base_padrao()
    perfil = _carregar("perfil_neutro.json")
    resultado = avaliar(base, perfil["respostas"], com_sensibilidade=False)
    assert resultado.empate is True
    assert resultado.nivel_confianca == "baixa"
    assert resultado.confianca < 0.45
    assert len(resultado.co_recomendadas) == 2
    assert resultado.mensagem_confianca == base.mensagens["empate"]
    # todos os percentuais ficam próximos do neutro (~60%)
    assert all(55 <= t.percentual <= 65 for t in resultado.ranking)


def test_perfil_conflitante_recebe_sugestao_de_desempate():
    base = base_padrao()
    perfil = _carregar("perfil_conflitante.json")
    resultado = avaliar(base, perfil["respostas"], com_sensibilidade=False)
    assert resultado.empate is True
    assert resultado.desempate is not None
    assert resultado.desempate["pergunta_id"]
    assert resultado.desempate["acao"]
    assert resultado.desempate["competencias_decisivas"]


def test_todas_as_respostas_maximas_nao_quebram_o_ranking():
    base = base_padrao()
    perfil = {pergunta.id: 5 for pergunta in base.perguntas}
    resultado = avaliar(base, perfil, com_sensibilidade=False)
    assert len(resultado.ranking) == 10
    assert resultado.top.percentual >= 85
    assert all(t.percentual <= 97.0001 for t in resultado.ranking)


def test_todas_as_respostas_minimas_nao_quebram_o_ranking():
    base = base_padrao()
    perfil = {pergunta.id: 1 for pergunta in base.perguntas}
    resultado = avaliar(base, perfil, com_sensibilidade=False)
    assert len(resultado.ranking) == 10
    assert all(0 <= t.percentual <= 100 for t in resultado.ranking)


def test_uma_unica_resposta_gera_resultado_com_cobertura_baixa():
    base = base_padrao()
    resultado = avaliar(base, {"q_codigo": 5}, com_sensibilidade=False)
    assert resultado.cobertura < 0.2
    assert resultado.ranking


def test_respostas_em_texto_sao_convertidas():
    base = base_padrao()
    perfil = {"q_codigo": "5", "q_logica": "4"}
    resultado = avaliar(base, perfil, com_sensibilidade=False)
    assert resultado.respostas["q_codigo"] == 5.0


def test_resposta_invalida_em_texto_falha():
    base = base_padrao()
    try:
        avaliar(base, {"q_codigo": "muito"}, com_sensibilidade=False)
    except ValueError as erro:
        assert "q_codigo" in str(erro)
    else:  # pragma: no cover
        raise AssertionError("deveria ter falhado")


def test_empate_usa_empregabilidade_como_criterio_de_ordem():
    """Com respostas idênticas, a trilha com maior entrada júnior fica na frente."""
    base = base_padrao()
    perfil = {pergunta.id: 3 for pergunta in base.perguntas}
    resultado = avaliar(base, perfil, com_sensibilidade=False)
    primeiro, segundo = resultado.ranking[0], resultado.ranking[1]
    if abs(primeiro.percentual - segundo.percentual) < 1e-9:
        assert base.trilha(primeiro.id).mercado["entrada_junior"] >= base.trilha(segundo.id).mercado["entrada_junior"]


def test_perfil_dominante_tem_alta_estabilidade():
    base = base_padrao()
    perfil = _carregar("perfil_produto.json")
    resultado = avaliar(base, perfil["respostas"], objetivo=perfil.get("objetivo"))
    assert resultado.sensibilidade["estabilidade"] >= 0.9


def test_cada_trilha_pode_ser_recomendada_por_um_perfil_extremo():
    """Sanidade da matriz: o perfil ideal de cada trilha leva essa trilha ao 1º lugar."""
    base = base_padrao()
    for trilha_id, trilha in base.trilhas.items():
        perfil: dict[str, float] = {}
        for pergunta in base.perguntas:
            peso = pergunta.peso_para(trilha_id)
            if peso >= 0.4:
                perfil[pergunta.id] = 5
            elif peso >= 0.1:
                perfil[pergunta.id] = 4
            elif peso > 0:
                perfil[pergunta.id] = 3
            elif peso <= -0.1:
                perfil[pergunta.id] = 1
            elif peso < 0:
                perfil[pergunta.id] = 2
            else:
                perfil[pergunta.id] = 3
        resultado = avaliar(base, perfil, com_sensibilidade=False)
        assert resultado.top.id == trilha_id, (
            f"perfil ideal de {trilha.nome} resultou em {resultado.top.nome} "
            f"({resultado.top.percentual}% vs {resultado.ranking[1].percentual}%)"
        )
