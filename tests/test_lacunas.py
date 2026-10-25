"""Testes da análise de lacunas (skill gap) por nível alvo."""

from __future__ import annotations

import pytest

from consultor.base_conhecimento import base_padrao
from consultor.lacunas import analisar_lacunas


def test_sem_conhecimento_todas_as_competencias_exigidas_sao_lacunas():
    base = base_padrao()
    analise = analisar_lacunas(base, "backend", {}, "junior")
    exigidas = [c for c in base.trilha("backend").competencias if c.nivel_necessario("junior") > 0]
    assert len(analise.lacunas) == len(exigidas)
    assert analise.cobertura == 0.0
    assert analise.criticas


def test_conhecimento_maximo_zera_as_lacunas():
    base = base_padrao()
    trilha = base.trilha("devops")
    conhecimentos = {c.id: 3 for c in trilha.competencias}
    analise = analisar_lacunas(base, "devops", conhecimentos, "junior")
    assert analise.lacunas == ()
    assert analise.cobertura == 100.0
    assert analise.pronto is True
    assert analise.horas_totais == 0


def test_ordem_por_prioridade_e_classificacoes_validas():
    base = base_padrao()
    analise = analisar_lacunas(base, "dados_ml", {"python": 1}, "junior")
    prioridades = [lacuna.prioridade for lacuna in analise.lacunas]
    assert prioridades == sorted(prioridades, reverse=True)
    assert {lacuna.classificacao for lacuna in analise.lacunas} <= {"crítica", "alta", "média", "baixa"}


def test_nivel_estagio_exige_menos_que_pleno():
    base = base_padrao()
    estagio = analisar_lacunas(base, "frontend", {}, "estagio")
    pleno = analisar_lacunas(base, "frontend", {}, "pleno")
    assert estagio.horas_totais < pleno.horas_totais
    assert estagio.cobertura >= pleno.cobertura


def test_nivel_invalido_falha():
    with pytest.raises(ValueError):
        analisar_lacunas(base_padrao(), "backend", {}, "senior")


def test_conhecimento_fora_da_escala_falha():
    with pytest.raises(ValueError):
        analisar_lacunas(base_padrao(), "backend", {"python": 7}, "junior")


def test_cobertura_e_parcial_quando_ha_conhecimento():
    base = base_padrao()
    trilha = base.trilha("backend")
    conhecimentos = {c.id: 2 for c in trilha.competencias_essenciais}
    analise = analisar_lacunas(base, "backend", conhecimentos, "junior")
    assert 0 < analise.cobertura < 100
    # Todas as essenciais estão no nível exigido para júnior (2).
    assert not analise.essenciais_pendentes


def test_lacunas_trazem_pratica_e_horas():
    base = base_padrao()
    analise = analisar_lacunas(base, "qa", {}, "junior")
    for lacuna in analise.lacunas:
        assert lacuna.horas_estimadas > 0
        assert lacuna.pratica
        assert lacuna.nome
