"""Testes do gerador de roadmap, certificações e portfólio."""

from __future__ import annotations

from consultor.base_conhecimento import base_padrao
from consultor.roadmap import gerar_plano


def _itens_em_ordem(plano) -> list[str]:
    ordem: list[str] = []
    for fase in plano.fases:
        for item in fase.itens:
            ordem.append(item.competencia_id)
    return ordem


def test_plano_sempre_tem_tres_fases_e_cronograma_coerente():
    base = base_padrao()
    plano = gerar_plano(base, "devops", {}, "junior", horas_semana=10, prazo_meses=6)
    assert len(plano.fases) == 3
    assert plano.horas_totais > 0
    assert plano.semanas_estimadas >= 4
    # as fases são contínuas e não se sobrepõem
    anterior = 0
    for fase in plano.fases:
        assert fase.semanas[0] > anterior
        assert fase.semanas[1] >= fase.semanas[0]
        anterior = fase.semanas[1]


def test_pre_requisitos_aparecem_antes_no_cronograma():
    base = base_padrao()
    plano = gerar_plano(base, "devops", {}, "junior", horas_semana=10)
    ordem = _itens_em_ordem(plano)
    assert ordem.index("docker") < ordem.index("kubernetes")
    assert ordem.index("git") < ordem.index("ci_cd")
    assert ordem.index("linux") < ordem.index("docker")


def test_plano_de_dados_respeita_prerequisitos_de_python_e_estatistica():
    base = base_padrao()
    plano = gerar_plano(base, "dados_ml", {}, "junior", horas_semana=12)
    ordem = _itens_em_ordem(plano)
    assert ordem.index("python") < ordem.index("pandas")
    assert ordem.index("estatistica") < ordem.index("machine_learning")


def test_certificacoes_e_projetos_vem_com_justificativa():
    base = base_padrao()
    plano = gerar_plano(base, "cloud", {}, "junior")
    assert len(plano.certificacoes) >= 2
    for certificacao in plano.certificacoes:
        assert certificacao["link"].startswith("http")
        assert certificacao["porque"]
    assert len(plano.projetos) >= 2
    for projeto in plano.projetos:
        assert projeto["titulo"]
        assert projeto["diferencial"]


def test_alerta_quando_prazo_e_curto_para_a_carga_horaria():
    base = base_padrao()
    apertado = gerar_plano(base, "devops", {}, "pleno", horas_semana=5, prazo_meses=3)
    assert apertado.alerta_prazo is True
    assert "prazo" in apertado.mensagem_prazo
    folgado = gerar_plano(base, "devops", {}, "pleno", horas_semana=30, prazo_meses=24)
    assert folgado.alerta_prazo is False


def test_plano_de_consolidacao_quando_nao_ha_lacunas():
    base = base_padrao()
    trilha = base.trilha("qa")
    conhecimentos = {c.id: 3 for c in trilha.competencias}
    plano = gerar_plano(base, "qa", conhecimentos, "junior")
    assert plano.analise.lacunas == ()
    assert len(plano.fases) == 3
    assert plano.projetos
    assert "consolida" in plano.resumo.lower()


def test_carga_horaria_invalida_e_normalizada():
    base = base_padrao()
    plano = gerar_plano(base, "backend", {}, "junior", horas_semana=0, prazo_meses=0)
    assert plano.horas_semana >= 1
    assert plano.prazo_meses >= 1


def test_todas_as_trilhas_geram_plano_completo():
    base = base_padrao()
    for trilha_id in base.ids_trilhas:
        plano = gerar_plano(base, trilha_id, {}, "junior")
        assert len(plano.fases) == 3, trilha_id
        assert plano.projetos, trilha_id
        assert plano.certificacoes, trilha_id
        assert plano.proximos_passos, trilha_id
        assert _itens_em_ordem(plano), trilha_id
