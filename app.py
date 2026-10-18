import streamlit as st
from sistema_especialista import diagnosticar, OPCOES

st.set_page_config(page_title="Consultor de Carreiras em TI", page_icon="🧭", layout="centered")

st.title("🧭 Consultor Inteligente de Carreiras em TI")
st.write(
    "Responda às perguntas abaixo para receber uma sugestão de carreira. "
    "O resultado é uma orientação inicial, não uma decisão definitiva."
)

with st.form("formulario_perfil"):
    matematica = st.radio(
        "1. Como você avalia sua afinidade com matemática e estatística?",
        ["Baixa", "Média", "Alta"],
        horizontal=True,
    )
    atividade = st.selectbox(
        "2. Qual atividade mais combina com você?",
        list(OPCOES["atividade"].keys()),
    )
    ferramenta = st.selectbox(
        "3. Com qual linguagem ou ferramenta você tem mais afinidade atualmente?",
        list(OPCOES["ferramenta"].keys()),
    )
    entrega = st.selectbox(
        "4. Que tipo de resultado você prefere entregar?",
        list(OPCOES["entrega"].keys()),
    )
    ambiente = st.selectbox(
        "5. Em qual ambiente você teria mais interesse em trabalhar?",
        list(OPCOES["ambiente"].keys()),
    )
    enviado = st.form_submit_button("Analisar meu perfil", type="primary")

if enviado:
    perfil = {
        "matematica": matematica,
        "atividade": OPCOES["atividade"][atividade],
        "ferramenta": OPCOES["ferramenta"][ferramenta],
        "entrega": OPCOES["entrega"][entrega],
        "ambiente": OPCOES["ambiente"][ambiente],
    }
    resultado = diagnosticar(perfil)

    st.divider()
    st.subheader("Resultado da análise")
    st.success(f"Trilha recomendada: {resultado['carreira']}")
    st.write(resultado["descricao"])
    st.markdown("**Por que essa trilha foi recomendada?**")
    for motivo in resultado["motivos"]:
        st.write(f"- {motivo}")

    st.caption(
        f"Pontuação da recomendação: {resultado['pontuacao']}. "
        "A pontuação representa a combinação das respostas com as regras cadastradas."
    )
    with st.expander("Ver outras trilhas consideradas"):
        for carreira, pontos in resultado["alternativas"]:
            st.write(f"- {carreira}: {pontos} ponto(s)")

st.divider()
st.caption("Projeto acadêmico — Inteligência Artificial — UNIPAC Barbacena")
