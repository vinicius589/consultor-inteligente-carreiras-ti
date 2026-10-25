"""Testes do motor de inferência: pontuação, certeza, penalidades e ordenação."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from consultor.base_conhecimento import base_padrao
from consultor.motor import avaliar, combinar_certeza, normalizar_resposta, pontuar

EXEMPLOS = Path(__file__).resolve().parents[1] / "exemplos"


def perfil_uniforme(valor: int = 3) -> dict[str, int]:
    base = base_padrao()
    return {pergunta.id: valor for pergunta in base.perguntas}


def test_normalizacao_da_escala():
    assert normalizar_resposta(1) == 0.0
    assert normalizar_resposta(5) == 1.0
    assert normalizar_resposta(3) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        normalizar_resposta(6)


def test_combinacao_de_fatores_de_certeza():
    assert combinar_certeza(None, 0.5) == 0.5
    assert combinar_certeza(0.5, 0.5) == pytest.approx(0.75)
    assert combinar_certeza(-0.5, -0.5) == pytest.approx(-0.75)
    # evidências opostas se cancelam parcialmente
    assert combinar_certeza(0.8, -0.8) == pytest.approx(0.0)


def test_ranking_tem_dez_trilhas_ordenadas_e_percentuais_validos():
    resultado = avaliar(base_padrao(), perfil_uniforme(4), com_sensibilidade=False)
    assert len(resultado.ranking) == 10
    percentuais = [t.percentual for t in resultado.ranking]
    assert percentuais == sorted(percentuais, reverse=True)
    assert all(0 <= p <= 100 for p in percentuais)
    assert resultado.top3 and len(resultado.top3) == 3


def test_resultado_e_deterministico():
    base = base_padrao()
    perfil = perfil_uniforme(4)
    primeiro = avaliar(base, perfil, com_sensibilidade=False).para_dict()
    segundo = avaliar(base, perfil, com_sensibilidade=False).para_dict()
    assert primeiro == segundo


def test_resposta_fora_da_escala_e_rejeitada():
    perfil = perfil_uniforme(3)
    perfil["q_logica"] = 9
    with pytest.raises(ValueError):
        avaliar(base_padrao(), perfil, com_sensibilidade=False)


def test_perfil_vazio_e_rejeitado():
    with pytest.raises(ValueError):
        avaliar(base_padrao(), {}, com_sensibilidade=False)


def test_respostas_parciais_funcionam():
    """O passo 2 da interface avalia antes de o usuário responder objetivos."""
    base = base_padrao()
    parciais = {pergunta.id: 4 for pergunta in base.perguntas[:8]}
    resultado = avaliar(base, parciais, com_sensibilidade=False)
    assert len(resultado.ranking) == 10
    assert 0 < resultado.cobertura <= 1


def test_penalidade_e_aplicada_em_perfil_conflitante():
    base = base_padrao()
    perfil = perfil_uniforme(3)
    perfil.update({"q_produto": 5, "q_usabilidade": 5, "q_comunicacao": 1})
    resultado = avaliar(base, perfil, com_sensibilidade=False)
    produto = resultado.por_id("produto")
    assert produto is not None
    assert any(regra.fator == pytest.approx(0.62) for regra in produto.penalidades)
    assert produto.forca > 0  # a afinidade com produto existia; a penalidade reduziu


def test_bonus_e_aplicado_quando_combinacao_e_coerente():
    base = base_padrao()
    perfil = perfil_uniforme(3)
    perfil.update({"q_infra": 5, "q_automacao": 5})
    resultado = avaliar(base, perfil, com_sensibilidade=False)
    devops = resultado.por_id("devops")
    assert devops is not None
    assert any(regra.id == "bon_devops_completo" for regra in devops.bonus)


def test_pontuar_devolve_mesmos_percentuais_do_ranking():
    base = base_padrao()
    perfil = perfil_uniforme(4)
    pontos = pontuar(base, perfil)
    resultado = avaliar(base, perfil, com_sensibilidade=False)
    for avaliada in resultado.ranking:
        assert pontos[avaliada.id] == pytest.approx(avaliada.percentual)


def test_personas_dos_exemplos_tem_a_trilha_esperada():
    import json

    esperado = {
        "perfil_analitico.json": "dados_ml",
        "perfil_frontend.json": "frontend",
        "perfil_devops.json": "devops",
        "perfil_produto.json": "produto",
        "perfil_seguranca.json": "seguranca",
        "perfil_backend.json": "backend",
    }
    base = base_padrao()
    for arquivo, trilha in esperado.items():
        perfil = json.loads((EXEMPLOS / arquivo).read_text(encoding="utf-8"))
        resultado = avaliar(
            base,
            perfil["respostas"],
            objetivo=perfil.get("objetivo"),
            modalidade=perfil.get("modalidade"),
            com_sensibilidade=False,
        )
        assert resultado.top.id == trilha, (
            f"{arquivo}: esperado {trilha}, obtido {resultado.top.id} "
            f"({resultado.top.percentual}% vs {resultado.ranking[1].percentual}%)"
        )


def test_sensibilidade_fica_entre_zero_e_um():
    base = base_padrao()
    perfil = json.loads((EXEMPLOS / "perfil_frontend.json").read_text(encoding="utf-8"))["respostas"]
    resultado = avaliar(base, perfil)
    estabilidade = resultado.sensibilidade["estabilidade"]
    assert 0.0 <= estabilidade <= 1.0
    assert resultado.sensibilidade["perturbacoes"] > 0
