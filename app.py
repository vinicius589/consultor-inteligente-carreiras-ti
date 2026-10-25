"""Interface web do Consultor Inteligente de Carreiras em TI (Streamlit).

Fluxo em três etapas (wizard):
    1. Perfil pessoal
    2. Afinidades técnicas (escala Likert 1–5)
    3. Objetivos e conhecimentos atuais

O resultado traz ranking de compatibilidade, justificativas, lacunas de
competência e um roadmap com certificações e projetos de portfólio.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))

from consultor.base_conhecimento import (  # noqa: E402
    BaseConhecimento,
    ErroBaseConhecimento,
    base_padrao,
)
from consultor.motor import Resultado, avaliar  # noqa: E402
from consultor.relatorio import gerar_json, gerar_markdown  # noqa: E402
from consultor.roadmap import PlanoAcao, gerar_plano  # noqa: E402

COR_PRIMARIA = "#4338ca"
COR_DESTAQUE = "#0ea5e9"
COR_NEUTRA = "#cbd5f5"

ROTULO_CONFIANCA = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
ROTULO_CUSTO = {"gratuito": "gratuito", "baixo": "baixo custo", "medio": "custo médio", "alto": "custo alto"}
ROTULO_NIVEL = {"iniciante": "iniciante", "intermediario": "intermediário", "avancado": "avançado"}
ROTULO_DIFICULDADE = {"baixa": "baixa", "media": "média", "alta": "alta"}
ROTULO_TIPO = {
    "curso": "curso",
    "documentacao": "documentação",
    "pratica": "prática",
    "artigo": "artigo",
    "livro": "livro",
    "certificacao": "certificação",
    "dados": "dados",
}

st.set_page_config(
    page_title="Consultor Inteligente de Carreiras em TI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem; padding-bottom: 3rem;}
      .zwork-eyebrow {font-size: 0.78rem; letter-spacing: 0.14em; text-transform: uppercase;
                      color: #6366f1; font-weight: 600; margin-bottom: .2rem;}
      .zwork-question {font-weight: 600; font-size: 0.98rem; line-height: 1.35; min-height: 3.1rem;}
      .zwork-help {color: #64748b; font-size: 0.82rem; margin-top: -.3rem;}
      div[data-testid="stMetricValue"] {font-size: 1.6rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ utilidades


def pct(valor: float, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",") + "%"


def num(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


@st.cache_resource(show_spinner=False)
def carregar_base_streamlit() -> BaseConhecimento:
    return base_padrao()


@st.cache_data(show_spinner=False)
def perfis_de_exemplo() -> dict[str, dict[str, Any]]:
    """Perfis prontos em exemplos/, usados no modo demonstração e nos prints."""
    perfis: dict[str, dict[str, Any]] = {}
    for caminho in sorted((RAIZ / "exemplos").glob("*.json")):
        try:
            perfis[caminho.stem] = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
    return perfis


def aplicar_perfil(base: BaseConhecimento, perfil: dict[str, Any]) -> None:
    """Carrega um perfil completo e calcula o resultado, sem passar pelo wizard."""
    for chave in list(st.session_state.keys()):
        if chave.startswith(("resp_", "campo_", "nivel_")):
            del st.session_state[chave]
    respostas = {chave: float(valor) for chave, valor in (perfil.get("respostas") or {}).items()}
    conhecimentos = {chave: int(valor) for chave, valor in (perfil.get("conhecimentos") or {}).items()}
    dados = {
        campo: perfil[campo]
        for campo in ("nome", "formacao", "experiencia", "horas_semana", "objetivo",
                      "nivel_alvo", "prazo", "prazo_meses", "modalidade")
        if campo in perfil
    }
    if "prazo_meses" in dados and "prazo" not in dados:
        dados["prazo"] = dados["prazo_meses"]
    st.session_state["respostas"] = respostas
    st.session_state["conhecimentos"] = conhecimentos
    st.session_state["dados"] = dados
    resultado = avaliar(
        base,
        respostas,
        objetivo=perfil.get("objetivo"),
        modalidade=perfil.get("modalidade"),
        nivel_alvo=perfil.get("nivel_alvo", "junior"),
    )
    plano = gerar_plano(
        base,
        resultado.top.id,
        conhecimentos,
        nivel_alvo=perfil.get("nivel_alvo", "junior"),
        horas_semana=int(perfil.get("horas_semana") or 10),
        prazo_meses=int(perfil.get("prazo_meses") or 6),
        objetivo=perfil.get("objetivo"),
    )
    st.session_state["resultado"] = resultado
    st.session_state["plano"] = plano
    st.session_state["perfil_export"] = {**perfil, "respostas": respostas, "conhecimentos": conhecimentos}
    st.session_state["modo_demo"] = perfil.get("nome") or "exemplo"
    st.session_state["etapa"] = 3


def reiniciar() -> None:
    for chave in list(st.session_state.keys()):
        del st.session_state[chave]
    st.query_params.clear()
    st.rerun()


def etapa_atual() -> int:
    return int(st.session_state.get("etapa", 0))


def ir_para(etapa: int) -> None:
    st.session_state["etapa"] = etapa
    st.rerun()


def dados_do_formulario() -> dict[str, Any]:
    """Valores já confirmados nos formulários (não dependem do estado do widget)."""
    return st.session_state.setdefault("dados", {})


def respostas_likert(base: BaseConhecimento) -> dict[str, float]:
    guardadas = st.session_state.get("respostas", {})
    return {
        pergunta.id: float(guardadas[pergunta.id])
        for pergunta in base.perguntas
        if pergunta.id in guardadas
    }


def valor_campo(base: BaseConhecimento, campo_id: str):
    campo = base.campo(campo_id)
    if campo_id in dados_do_formulario():
        return dados_do_formulario()[campo_id]
    padrao = campo.get("padrao")
    if campo["tipo"] == "selecao" and padrao is None:
        padrao = campo["opcoes"][0]["valor"]
    return padrao


# ---------------------------------------------------------------- componentes


def cabecalho(base: BaseConhecimento) -> None:
    st.markdown('<div class="zwork-eyebrow">UNIPAC Barbacena · Inteligência Artificial</div>', unsafe_allow_html=True)
    st.title("🧭 Consultor Inteligente de Carreiras em TI")
    st.write(
        f"Sistema especialista com raciocínio ponderado sobre **{len(base.trilhas)} trilhas** e "
        f"**{len(base.perguntas)} perguntas** de afinidade. O resultado é uma hipótese de trabalho, "
        "não um veredito vocacional."
    )


def barra_lateral(base: BaseConhecimento) -> None:
    with st.sidebar:
        st.markdown("### Sua jornada")
        etapa = etapa_atual()
        passos = [
            ("1. Perfil pessoal", "Quem você é hoje"),
            ("2. Afinidades técnicas", "17 perguntas em escala 1–5"),
            ("3. Objetivos e conhecimentos", "Para onde quer ir"),
            ("Resultado", "Ranking, lacunas e roadmap"),
        ]
        for indice, (titulo, descricao) in enumerate(passos):
            icone = "✅" if indice < etapa else ("▶️" if indice == etapa else "⚪")
            st.markdown(
                f"{icone} **{titulo}**  \n<span style='color:#64748b;font-size:.8rem'>{descricao}</span>",
                unsafe_allow_html=True,
            )
        st.divider()
        st.caption(
            f"Base de conhecimento: {len(base.trilhas)} trilhas · {len(base.perguntas)} perguntas · "
            f"{len(base.recursos)} competências mapeadas."
        )
        with st.expander("Como o cálculo funciona"):
            st.markdown(
                "1. Cada resposta (1–5) é normalizada para 0–1.\n"
                "2. O peso de cada pergunta varia por trilha (há pesos negativos).\n"
                "3. A pontuação bruta é normalizada dentro da faixa possível da trilha.\n"
                "4. Fatores de certeza (MYCIN) medem a consistência do perfil.\n"
                "5. Penalidades, bônus e objetivos ajustam o resultado final."
            )
        with st.expander("Modo demonstração"):
            st.caption(
                "Carregue um perfil pronto de `exemplos/` para ver o resultado sem responder ao "
                "questionário. Também funciona pela URL: `?perfil=perfil_devops`."
            )
            exemplos = perfis_de_exemplo()
            if exemplos:
                escolha = st.selectbox(
                    "Perfil de exemplo",
                    list(exemplos),
                    format_func=lambda chave: exemplos[chave].get("nome", chave),
                    key="seletor_demo",
                )
                if st.button("Carregar perfil de exemplo", width="stretch"):
                    aplicar_perfil(base, exemplos[escolha])
                    st.rerun()
        if st.button("Recomeçar", width="stretch"):
            reiniciar()


def _explicar_segundo(avaliada, resultado: "Resultado", base: BaseConhecimento) -> str:
    """Explica por que uma trilha ficou atrás, olhando onde ela perdeu mais pontos."""
    top = resultado.top
    margem = top.percentual - avaliada.percentual
    candidatas = [
        pergunta
        for pergunta in base.perguntas
        if pergunta.peso_para(avaliada.id) >= 0.2 and pergunta.id in resultado.respostas
    ]
    if not candidatas:
        return f"Ficou {num(margem, 1)} pontos atrás da recomendada, sem sinal específico que a sustente."
    # Onde a trilha deixou mais pontos na mesa: peso alto com resposta baixa.
    mais_fraca = max(
        candidatas,
        key=lambda pergunta: pergunta.peso_para(avaliada.id) * (1 - resultado.respostas[pergunta.id] / 5.0),
    )
    resposta = resultado.respostas[mais_fraca.id]
    peso = num(mais_fraca.peso_para(avaliada.id))
    if margem <= 5:
        return (
            f"Ficou apenas {num(margem, 1)} pontos atrás: é uma alternativa real, não um descarte. "
            f"O que mais a segurou foi “{mais_fraca.texto}” ({resposta:g}/5, peso {peso})."
        )
    return (
        f"Ficou {num(margem, 1)} pontos atrás. Onde perdeu mais pontos foi em “{mais_fraca.texto}” "
        f"({resposta:g}/5, peso {peso} nesta trilha)."
    )


def cartao_trilha(avaliada, base: BaseConhecimento, posicao: int) -> None:
    with st.container(border=True):
        st.markdown(f"**{posicao}º · {avaliada.nome} — {pct(avaliada.percentual)}**")
        st.caption(base.trilha(avaliada.id).resumo)
        st.caption(f"certeza {num(avaliada.certeza)} · força {num(avaliada.forca)}")


# ------------------------------------------------------------------- gráficos


def grafico_ranking(resultado: Resultado) -> go.Figure:
    nomes = [t.nome for t in resultado.ranking][::-1]
    valores = [t.percentual for t in resultado.ranking][::-1]
    cores = [COR_DESTAQUE if t.id == resultado.top.id else COR_NEUTRA for t in resultado.ranking][::-1]
    figura = go.Figure(
        go.Bar(
            x=valores,
            y=nomes,
            orientation="h",
            marker_color=cores,
            text=[pct(v) for v in valores],
            textposition="outside",
            cliponaxis=False,
            hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        )
    )
    figura.update_layout(
        height=380,
        margin=dict(l=10, r=30, t=10, b=10),
        xaxis=dict(range=[0, 112], title="Compatibilidade (%)", gridcolor="#eef2ff"),
        yaxis=dict(title=""),
        plot_bgcolor="white",
        showlegend=False,
    )
    return figura


def grafico_radar(resultado: Resultado, base: BaseConhecimento) -> go.Figure:
    eixos = list(base.eixos)
    nomes = [base.eixos_nomes.get(e, e) for e in eixos]
    trilha = base.trilha(resultado.top.id)
    seu = [resultado.eixos_usuario.get(e, 0) * 100 for e in eixos]
    ideal = [trilha.eixos.get(e, 0) * 100 for e in eixos]
    figura = go.Figure()
    figura.add_trace(
        go.Scatterpolar(
            r=seu + [seu[0]],
            theta=nomes + [nomes[0]],
            fill="toself",
            name="Seu perfil",
            line_color=COR_DESTAQUE,
            fillcolor="rgba(14,165,233,0.22)",
        )
    )
    figura.add_trace(
        go.Scatterpolar(
            r=ideal + [ideal[0]],
            theta=nomes + [nomes[0]],
            fill="toself",
            name=f"Perfil de {trilha.nome}",
            line_color=COR_PRIMARIA,
            fillcolor="rgba(67,56,202,0.10)",
        )
    )
    figura.update_layout(
        height=420,
        margin=dict(l=40, r=40, t=30, b=30),
        polar=dict(radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor="#e2e8f0")),
        legend=dict(orientation="h", y=-0.12),
    )
    return figura


# --------------------------------------------------------------------- etapas


def etapa_perfil(base: BaseConhecimento) -> None:
    st.subheader("Passo 1 · Perfil pessoal")
    st.caption("Contexto rápido. Nada aqui decide sozinho o resultado, mas calibra o plano de estudos.")

    campos = base.etapa("perfil")["campos"]
    coletados: dict[str, Any] = {}
    colunas = st.columns(2)
    for indice, campo in enumerate(campos):
        with colunas[indice % 2]:
            atual = valor_campo(base, campo["id"])
            chave = f"campo_{campo['id']}"
            if campo["tipo"] == "texto":
                st.session_state.setdefault(chave, str(atual or ""))
                coletados[campo["id"]] = st.text_input(campo["rotulo"], key=chave)
            else:
                rotulos = [opcao["rotulo"] for opcao in campo["opcoes"]]
                valores = [opcao["valor"] for opcao in campo["opcoes"]]
                padrao = rotulos[valores.index(atual)] if atual in valores else rotulos[0]
                st.session_state.setdefault(chave, padrao)
                escolhido = st.selectbox(campo["rotulo"], rotulos, key=chave)
                coletados[campo["id"]] = valores[rotulos.index(escolhido)]

    if st.button("Continuar para as afinidades →", type="primary", width="stretch"):
        dados_do_formulario().update(coletados)
        ir_para(1)


def etapa_afinidades(base: BaseConhecimento) -> None:
    st.subheader("Passo 2 · Afinidades técnicas")
    st.caption(
        "Marque o quanto cada frase tem a ver com você: **1** = nada a ver, **5** = totalmente a ver. "
        "Não existe resposta certa — responda pelo que você gosta de fazer, não pelo que parece mais "
        "empregável."
    )

    respostas = st.session_state.setdefault("respostas", {})
    respondidas = sum(1 for p in base.perguntas if p.id in respostas)
    st.progress(respondidas / len(base.perguntas), text=f"{respondidas} de {len(base.perguntas)} respondidas")

    colunas = st.columns(2)
    for indice, pergunta in enumerate(base.perguntas):
        with colunas[indice % 2]:
            with st.container(border=True):
                st.markdown(f'<div class="zwork-question">{pergunta.texto}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="zwork-help">{pergunta.ajuda}</div>', unsafe_allow_html=True)
                chave = f"resp_{pergunta.id}"
                st.session_state.setdefault(chave, int(respostas.get(pergunta.id, 3)))
                escolha = st.radio(
                    "Nota",
                    options=[1, 2, 3, 4, 5],
                    horizontal=True,
                    label_visibility="collapsed",
                    key=chave,
                )
                respostas[pergunta.id] = escolha
    st.caption("Escala: 1 nada a ver · 2 pouco · 3 neutro · 4 bastante · 5 totalmente a ver.")

    col_voltar, col_continuar = st.columns([1, 2])
    with col_voltar:
        voltar = st.button("← Voltar", width="stretch")
    with col_continuar:
        continuar = st.button("Continuar para os objetivos →", type="primary", width="stretch")

    if voltar:
        ir_para(0)
    if continuar:
        if not respostas:
            st.warning("Responda as perguntas de afinidade para continuar.")
        else:
            ir_para(2)


def _competencias_do_top3(base: BaseConhecimento) -> list[tuple[str, list]]:
    preliminar = avaliar(base, respostas_likert(base), com_sensibilidade=False)
    grupos: list[tuple[str, list]] = []
    vistos: set[str] = set()
    for avaliada in preliminar.top3:
        itens = []
        for competencia in base.trilha(avaliada.id).competencias:
            if competencia.id in vistos:
                continue
            vistos.add(competencia.id)
            itens.append(competencia)
        grupos.append((avaliada.id, itens))
    return grupos


def etapa_objetivos(base: BaseConhecimento) -> None:
    st.subheader("Passo 3 · Objetivos e conhecimentos")
    st.caption(
        "As escolhas desta etapa ajustam o ranking e definem o nível alvo do plano. "
        "A autoavaliação abaixo já está filtrada pelas trilhas mais compatíveis com suas afinidades."
    )

    campos = base.etapa("objetivos")["campos"]
    coletados: dict[str, Any] = {}
    conhecimentos = st.session_state.setdefault("conhecimentos", {})

    colunas = st.columns(2)
    for indice, campo in enumerate(campos):
        with colunas[indice % 2]:
            atual = valor_campo(base, campo["id"])
            rotulos = [opcao["rotulo"] for opcao in campo["opcoes"]]
            valores = [opcao["valor"] for opcao in campo["opcoes"]]
            padrao = rotulos[valores.index(atual)] if atual in valores else rotulos[0]
            chave = f"campo_{campo['id']}"
            st.session_state.setdefault(chave, padrao)
            escolhido = st.selectbox(campo["rotulo"], rotulos, key=chave)
            coletados[campo["id"]] = valores[rotulos.index(escolhido)]

    st.divider()
    st.markdown("**Seu conhecimento atual**")
    escala_niveis = base.autoavaliacao["escala"]
    st.caption(base.autoavaliacao["descricao"])

    try:
        grupos = _competencias_do_top3(base)
    except ValueError:
        st.error("Volte ao passo 2 e responda as afinidades antes de continuar.")
        grupos = []

    trilha_principal = grupos[0][0] if grupos else None
    for trilha_id, competencias in grupos:
        trilha = base.trilha(trilha_id)
        with st.expander(f"Competências de {trilha.nome}", expanded=trilha_id == trilha_principal):
            if not competencias:
                st.caption("Todas as competências desta trilha já apareceram nos outros grupos.")
                continue
            for competencia in competencias:
                recurso = base.recurso(competencia.id)
                nome = recurso.nome if recurso else competencia.id
                tipo = "essencial" if competencia.essencial else "complementar"
                chave = f"nivel_{competencia.id}"
                st.session_state.setdefault(chave, int(conhecimentos.get(competencia.id, 0)))
                conhecimentos[competencia.id] = st.select_slider(
                    f"{nome} ({tipo})",
                    options=[0, 1, 2, 3],
                    format_func=lambda valor: f"{valor} · {escala_niveis[str(valor)]}",
                    key=chave,
                )

    col_voltar, col_finalizar = st.columns([1, 2])
    with col_voltar:
        voltar = st.button("← Voltar", width="stretch")
    with col_finalizar:
        finalizar = st.button("Gerar meu plano de carreira →", type="primary", width="stretch")

    if voltar:
        ir_para(1)
    if finalizar:
        dados_do_formulario().update(coletados)
        with st.spinner("Calculando ranking, lacunas e roadmap..."):
            try:
                resultado = avaliar(
                    base,
                    respostas_likert(base),
                    objetivo=valor_campo(base, "objetivo"),
                    modalidade=valor_campo(base, "modalidade"),
                    nivel_alvo=valor_campo(base, "nivel_alvo"),
                    com_sensibilidade=True,
                )
                plano = gerar_plano(
                    base,
                    resultado.top.id,
                    conhecimentos,
                    nivel_alvo=valor_campo(base, "nivel_alvo"),
                    horas_semana=int(valor_campo(base, "horas_semana") or 10),
                    prazo_meses=int(valor_campo(base, "prazo") or 6),
                    objetivo=valor_campo(base, "objetivo"),
                )
            except ValueError as erro:
                st.error(f"Não foi possível calcular: {erro}")
            else:
                st.session_state["resultado"] = resultado
                st.session_state["plano"] = plano
                st.session_state["perfil_export"] = {
                    **dados_do_formulario(),
                    "nome": valor_campo(base, "nome"),
                    "respostas": respostas_likert(base),
                    "conhecimentos": dict(conhecimentos),
                }
                ir_para(3)


# ------------------------------------------------------------------- resultado


def painel_resultado(base: BaseConhecimento) -> None:
    resultado: Resultado | None = st.session_state.get("resultado")
    perfil = st.session_state.get("perfil_export", {})
    if resultado is None:
        st.warning("Nenhum resultado calculado. Volte ao passo 1 para preencher o perfil.")
        if st.button("Ir para o passo 1"):
            ir_para(0)
        return

    st.subheader("Resultado da análise")
    if st.session_state.get("modo_demo"):
        st.info(
            f"Perfil de demonstração carregado: **{st.session_state['modo_demo']}**. "
            "Clique em *Recomeçar* para responder ao questionário com seu próprio perfil."
        )
    nome = perfil.get("nome") or "Estudante"
    st.write(f"**{nome}**, seu perfil foi comparado com {len(base.trilhas)} trilhas de tecnologia.")

    top = resultado.top
    segundo = resultado.ranking[1]
    st.markdown(f"### 🎯 {top.nome}")
    st.caption(base.trilha(top.id).resumo)

    col1, col2, col3 = st.columns(3)
    col1.metric("Aderência da 1ª trilha", pct(top.percentual))
    col2.metric("2ª opção", pct(segundo.percentual))
    col3.metric("Confiança", ROTULO_CONFIANCA.get(resultado.nivel_confianca, resultado.nivel_confianca))
    estabilidade = resultado.sensibilidade.get("estabilidade")
    detalhe = f"1ª: {top.nome} · 2ª: {segundo.nome} · índice de confiança {num(resultado.confianca)}"
    if estabilidade is not None:
        detalhe += f" · estabilidade {estabilidade * 100:.0f}% em variações de ±1 ponto"
    st.caption(detalhe)

    if resultado.empate:
        st.warning(f"**Empate técnico.** {resultado.mensagem_confianca}")
        if resultado.desempate:
            with st.container(border=True):
                st.markdown("**Teste de desempate sugerido**")
                st.write(f"Pergunta que mais separa as duas trilhas: *“{resultado.desempate['pergunta']}”*.")
                st.write(resultado.desempate["acao"])
    elif resultado.nivel_confianca == "baixa":
        st.info(resultado.mensagem_confianca)

    st.divider()

    aba_panorama, aba_justificativas, aba_lacunas, aba_roadmap, aba_exportar = st.tabs(
        ["📊 Panorama", "🔍 Justificativas", "🧩 Lacunas", "🗺️ Roadmap", "⬇️ Exportar"]
    )

    with aba_panorama:
        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.markdown("**Ranking de compatibilidade**")
            st.plotly_chart(grafico_ranking(resultado), width="stretch")
        with col_dir:
            st.markdown("**Seu perfil × perfil da trilha**")
            st.plotly_chart(grafico_radar(resultado, base), width="stretch")

        st.markdown("**Top 3 em detalhe**")
        colunas = st.columns(3)
        for indice, avaliada in enumerate(resultado.top3):
            with colunas[indice]:
                cartao_trilha(avaliada, base, indice + 1)

        with st.expander("Ver as 10 trilhas e os ajustes aplicados"):
            tabela = pd.DataFrame(
                [
                    {
                        "Trilha": t.nome,
                        "Compatibilidade": pct(t.percentual),
                        "Força": num(t.forca),
                        "Certeza": num(t.certeza),
                        "Ajuste objetivo": num(t.ajuste_objetivo),
                        "Ajuste modalidade": num(t.ajuste_modalidade),
                    }
                    for t in resultado.ranking
                ]
            )
            st.dataframe(tabela, width="stretch", hide_index=True)

    with aba_justificativas:
        st.markdown(f"**Por que {top.nome}**")
        for contribuicao in top.pontos_fortes[:5]:
            st.markdown(f"- {contribuicao.como_texto()}")
        for regra in top.bonus:
            st.success(f"Combinação identificada: {regra.justificativa}")
        for regra in top.penalidades:
            st.warning(f"Penalidade aplicada (fator {num(regra.fator)}): {regra.justificativa}")

        if top.pontos_atencao:
            st.markdown("**Sinais de atenção**")
            for contribuicao in [c for c in top.pontos_atencao if abs(c.peso) >= 0.15][:3]:
                st.markdown(f"- {contribuicao.como_texto()} — puxou a aderência para baixo.")

        st.divider()
        st.markdown("**O que afastou cada trilha do topo**")
        for avaliada in resultado.ranking[1:6]:
            motivos = [r.justificativa for r in avaliada.penalidades]
            texto = "; ".join(motivos) if motivos else _explicar_segundo(avaliada, resultado, base)
            st.markdown(f"- **{avaliada.nome}** ({pct(avaliada.percentual)}): {texto}")

    with aba_lacunas:
        plano: PlanoAcao | None = st.session_state.get("plano")
        if plano is None:
            st.info("Plano indisponível.")
        else:
            analise = plano.analise
            nivel_rotulo = base.niveis[plano.nivel_alvo]["rotulo"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Cobertura do nível", pct(analise.cobertura))
            col2.metric("Lacunas", f"{len(analise.lacunas)}", f"{len(analise.criticas)} críticas")
            col3.metric("Esforço estimado", f"{analise.horas_totais}h")

            if analise.lacunas:
                tabela = pd.DataFrame(
                    [
                        {
                            "Prioridade": num(lacuna.prioridade),
                            "Competência": lacuna.nome,
                            "Atual": lacuna.nivel_atual,
                            "Necessário": lacuna.nivel_necessario,
                            "Lacuna": lacuna.lacuna,
                            "Horas": lacuna.horas_estimadas,
                            "Classificação": lacuna.classificacao,
                        }
                        for lacuna in analise.lacunas
                    ]
                )
                st.dataframe(tabela, width="stretch", hide_index=True)
                st.caption(f"Referência: nível {nivel_rotulo} da trilha {plano.trilha_nome}.")
            else:
                st.success(f"Você já cobre o nível {nivel_rotulo} nas competências desta trilha.")

            if analise.cobertas:
                st.markdown("**Pontos fortes já demonstrados**")
                st.write(", ".join(f"{c.nome} (nível {c.nivel_atual})" for c in analise.cobertas[:8]))

    with aba_roadmap:
        plano = st.session_state.get("plano")
        if plano is None:
            st.info("Plano indisponível.")
        else:
            opcoes = {t.id: t.nome for t in resultado.ranking}
            with st.expander("Explorar o plano de outra trilha"):
                escolhida = st.selectbox(
                    "Trilha",
                    list(opcoes),
                    index=list(opcoes).index(resultado.top.id),
                    format_func=lambda tid: opcoes[tid],
                    key="explorar_trilha",
                )
                if escolhida != plano.trilha_id:
                    plano = gerar_plano(
                        base,
                        escolhida,
                        perfil.get("conhecimentos", {}),
                        nivel_alvo=valor_campo(base, "nivel_alvo"),
                        horas_semana=int(valor_campo(base, "horas_semana") or 10),
                        prazo_meses=int(valor_campo(base, "prazo") or 6),
                    )

            st.markdown(f"### {plano.trilha_nome}")
            st.write(plano.resumo)
            if plano.alerta_prazo:
                st.warning(plano.mensagem_prazo)
            else:
                st.info(plano.mensagem_prazo)

            for fase in plano.fases:
                titulo = f"Fase {fase.numero} — {fase.titulo} (semanas {fase.semanas[0]}–{fase.semanas[1]})"
                with st.expander(titulo, expanded=fase.numero == 1):
                    st.caption(fase.objetivo)
                    if not fase.itens:
                        st.write("Sem novas competências: fase dedicada a projeto e portfólio.")
                    for item in fase.itens:
                        st.markdown(
                            f"**{item.ordem}. {item.nome}** · {item.horas}h · lacuna {item.lacuna} · "
                            f"{item.classificacao}"
                        )
                        st.caption(item.porque)
                        for recurso in item.recursos:
                            tipo = ROTULO_TIPO.get(recurso["tipo"], recurso["tipo"])
                            st.markdown(f"- [{recurso['titulo']}]({recurso['url']}) · {tipo}")
                        if item.pratica:
                            st.caption(f"Prática: {item.pratica}")
                    st.success(f"Entregável: {fase.entregavel}")

            col_cert, col_proj = st.columns(2)
            with col_cert:
                st.markdown("**Certificações**")
                for certificacao in plano.certificacoes:
                    custo = ROTULO_CUSTO.get(certificacao["custo"], certificacao["custo"])
                    nivel = ROTULO_NIVEL.get(certificacao["nivel"], certificacao["nivel"])
                    st.markdown(
                        f"- [{certificacao['nome']}]({certificacao['link']}) — {custo} · nível {nivel}"
                    )
            with col_proj:
                st.markdown("**Projetos de portfólio**")
                for projeto in plano.projetos:
                    dificuldade = ROTULO_DIFICULDADE.get(projeto["dificuldade"], projeto["dificuldade"])
                    st.markdown(
                        f"- **{projeto['titulo']}** ({dificuldade}) — {projeto['diferencial']}"
                    )

            st.markdown("**Próximos passos**")
            for indice, passo in enumerate(plano.proximos_passos, start=1):
                st.markdown(f"{indice}. {passo}")

    with aba_exportar:
        plano = st.session_state.get("plano")
        if plano is not None:
            markdown = gerar_markdown(resultado, plano, base, perfil)
            dados = gerar_json(resultado, plano, perfil)
            col_md, col_json = st.columns(2)
            with col_md:
                st.download_button(
                    "Baixar plano em Markdown",
                    data=markdown.encode("utf-8"),
                    file_name="plano-carreira-ti.md",
                    mime="text/markdown",
                    width="stretch",
                )
            with col_json:
                st.download_button(
                    "Baixar resultado em JSON",
                    data=json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8"),
                    file_name="resultado-consultor-carreiras.json",
                    mime="application/json",
                    width="stretch",
                )
            with st.expander("Pré-visualizar o relatório"):
                st.markdown(markdown)


# ------------------------------------------------------------------------ main


def main() -> None:
    try:
        base = carregar_base_streamlit()
    except ErroBaseConhecimento as erro:
        st.error(f"Falha ao carregar a base de conhecimento: {erro}")
        st.stop()
        return

    demo = st.query_params.get("perfil")
    if isinstance(demo, list):
        demo = demo[0] if demo else None
    if demo and not st.session_state.get("demo_aplicada"):
        exemplo = perfis_de_exemplo().get(str(demo).replace(".json", ""))
        st.session_state["demo_aplicada"] = True
        if exemplo:
            aplicar_perfil(base, exemplo)
        else:
            st.warning(f"Perfil de exemplo desconhecido: {demo}")

    cabecalho(base)
    barra_lateral(base)

    etapa = etapa_atual()
    if etapa == 0:
        etapa_perfil(base)
    elif etapa == 1:
        etapa_afinidades(base)
    elif etapa == 2:
        etapa_objetivos(base)
    else:
        painel_resultado(base)

    st.divider()
    st.caption(
        "Projeto acadêmico · Inteligência Artificial · UNIPAC Barbacena · "
        "motor de inferência ponderada com fatores de certeza (v2)."
    )


if __name__ == "__main__":
    main()
