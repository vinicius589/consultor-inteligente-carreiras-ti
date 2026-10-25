"""Testes da base de conhecimento e da validação dos arquivos JSON."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from consultor.base_conhecimento import (
    PASTA_DADOS_PADRAO,
    ErroBaseConhecimento,
    base_padrao,
    carregar_base,
)


def test_base_padrao_tem_dez_trilhas_e_perguntas():
    base = base_padrao()
    assert len(base.trilhas) == 10
    assert len(base.perguntas) >= 15
    for trilha in base.trilhas.values():
        assert len(trilha.competencias) >= 6
        assert len(trilha.certificacoes) >= 2
        assert len(trilha.projetos) >= 2
        assert trilha.tecnologias


def test_toda_pergunta_aponta_para_trilhas_existentes():
    base = base_padrao()
    for pergunta in base.perguntas:
        desconhecidas = set(pergunta.pesos) - set(base.trilhas)
        assert not desconhecidas, f"{pergunta.id} aponta para {desconhecidas}"


def test_toda_competencia_tem_recurso_de_estudo():
    base = base_padrao()
    for trilha in base.trilhas.values():
        for competencia in trilha.competencias:
            recurso = base.recurso(competencia.id)
            assert recurso is not None, f"{competencia.id} sem recurso"
            assert recurso.recursos, f"{competencia.id} sem links"
            assert recurso.recursos[0]["url"].startswith("http")


def test_etapas_do_formulario_existem():
    base = base_padrao()
    ids = [etapa["id"] for etapa in base.etapas]
    assert ids == ["perfil", "afinidades", "objetivos"]
    assert base.campo("objetivo")["opcoes"]
    assert base.campo("nivel_alvo")["opcoes"]


def test_regras_citam_perguntas_e_trilhas_validas():
    base = base_padrao()
    for regra in (*base.penalidades, *base.bonus):
        assert regra.trilha in base.trilhas
        for pergunta_id in regra.quando:
            assert base.pergunta(pergunta_id) is not None


def test_carregar_base_de_pasta_inexistente_falha(tmp_path: Path):
    with pytest.raises(ErroBaseConhecimento):
        carregar_base(tmp_path / "nao-existe")


def test_json_invalido_gera_erro_claro(tmp_path: Path):
    for arquivo in PASTA_DADOS_PADRAO.glob("*.json"):
        shutil.copy(arquivo, tmp_path / arquivo.name)
    (tmp_path / "perguntas.json").write_text("{ nao é json", encoding="utf-8")
    with pytest.raises(ErroBaseConhecimento, match="JSON inválido"):
        carregar_base(tmp_path)


def test_peso_em_trilha_inexistente_e_rejeitado(tmp_path: Path):
    for arquivo in PASTA_DADOS_PADRAO.glob("*.json"):
        shutil.copy(arquivo, tmp_path / arquivo.name)
    caminho = tmp_path / "perguntas.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados["etapas"][1]["perguntas"][0]["pesos"]["trilha_fantasma"] = 0.5
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ErroBaseConhecimento, match="trilhas inexistentes"):
        carregar_base(tmp_path)


def test_pesos_discriminam_as_trilhas():
    """Nenhuma pergunta deve dar peso alto para todas as 10 trilhas."""
    base = base_padrao()
    for pergunta in base.perguntas:
        altos = [t for t, peso in pergunta.pesos.items() if peso >= 0.6]
        assert len(altos) <= 6, f"{pergunta.id} discrimina pouco: {altos}"
