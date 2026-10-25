"""Teste de fumaça da interface Streamlit (AppTest), percorrendo o wizard inteiro."""

from __future__ import annotations

from pathlib import Path

import pytest

streamlit = pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "app.py"

# Perfil com afinidade alta em infraestrutura e automação (DevOps/SRE).
NOTAS = {
    "q_logica": 5, "q_matematica": 2, "q_codigo": 4, "q_sistemas": 5, "q_visual": 1,
    "q_usabilidade": 2, "q_dados": 2, "q_eng_dados": 3, "q_infra": 5, "q_automacao": 5,
    "q_seguranca": 4, "q_qualidade": 3, "q_produto": 1, "q_comunicacao": 3, "q_mobile": 1,
    "q_nuvem": 4, "q_plantao": 4,
}


def _botao(at: AppTest, prefixo: str):
    candidatos = [b for b in at.button if b.label.startswith(prefixo)]
    assert candidatos, f"botão '{prefixo}' não encontrado: {[b.label for b in at.button]}"
    return candidatos[0]


def _campo(at: AppTest, etiqueta: str):
    for caixa in at.selectbox:
        if caixa.label == etiqueta:
            return caixa
    raise AssertionError(f"selectbox '{etiqueta}' não encontrado: {[c.label for c in at.selectbox]}")


def test_wizard_completo_gera_resultado():
    at = AppTest.from_file(str(APP), default_timeout=90)
    at.run()
    assert not at.exception, at.exception

    # Passo 1
    at.text_input[0].set_value("Ana Vitória")
    _campo(at, "Onde você está hoje?").select("Cursando graduação em TI")
    at.run()
    _botao(at, "Continuar para as afinidades").click().run()
    assert not at.exception, at.exception
    assert at.session_state["etapa"] == 1

    # Passo 2 — uma nota por pergunta
    assert len(at.radio) == 17, len(at.radio)
    for chave, nota in NOTAS.items():
        at.radio(key=f"resp_{chave}").set_value(nota)
    at.run()
    assert at.session_state["respostas"]["q_infra"] == 5
    _botao(at, "Continuar para os objetivos").click().run()
    assert not at.exception, at.exception
    assert at.session_state["etapa"] == 2

    # Passo 3 — objetivos e autoavaliação
    _campo(at, "Qual é o seu objetivo principal agora?").select("Conseguir o primeiro emprego em TI")
    _campo(at, "Qual nível você quer atingir no plano?").select("Júnior")
    at.run()
    for slider in at.select_slider:
        slider.set_value(1)
    at.run()
    _botao(at, "Gerar meu plano").click().run()

    assert not at.exception, at.exception
    assert at.session_state["etapa"] == 3
    resultado = at.session_state["resultado"]
    plano = at.session_state["plano"]
    assert resultado.top.id == "devops", resultado.top.nome
    assert plano.trilha_id == resultado.top.id
    assert len(plano.fases) == 3
    assert at.session_state["perfil_export"]["nome"] == "Ana Vitória"

    textos = " ".join(m.value for m in at.markdown)
    assert "Ranking de compatibilidade" in textos
    assert resultado.top.nome in textos
    assert len(at.metric) >= 4
    assert any("Baixar plano em Markdown" in d.label for d in at.get("download_button"))


def test_botao_recomecar_volta_ao_inicio():
    at = AppTest.from_file(str(APP), default_timeout=90)
    at.run()
    at.text_input[0].set_value("Teste")
    at.run()
    _botao(at, "Continuar para as afinidades").click().run()
    assert at.session_state["etapa"] == 1
    at.sidebar.button[0].click().run()
    assert not at.exception, at.exception
    assert any("Passo 1" in s.value for s in at.subheader)


def test_nome_sobrevive_ao_avancar_de_etapa():
    """Regressão: o estado do widget é descartado ao trocar de etapa."""
    at = AppTest.from_file(str(APP), default_timeout=90)
    at.run()
    at.text_input[0].set_value("Carla")
    _campo(at, "Horas por semana disponíveis para estudar").select("10 a 20 horas")
    at.run()
    _botao(at, "Continuar para as afinidades").click().run()
    for chave, nota in NOTAS.items():
        at.radio(key=f"resp_{chave}").set_value(nota)
    at.run()
    _botao(at, "Continuar para os objetivos").click().run()
    assert at.session_state["dados"]["nome"] == "Carla"
    assert at.session_state["dados"]["horas_semana"] == 20
