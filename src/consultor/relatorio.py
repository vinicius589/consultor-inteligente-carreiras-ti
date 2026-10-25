"""Exportação dos resultados em Markdown e JSON."""

from __future__ import annotations

from datetime import date
from typing import Any

from .base_conhecimento import BaseConhecimento
from .motor import Resultado, TrilhaAvaliada
from .roadmap import PlanoAcao

ROTULO_CONFIANCA = {"alta": "alta", "media": "média", "baixa": "baixa"}
ROTULO_CUSTO = {"gratuito": "gratuito", "baixo": "baixo custo", "medio": "custo médio", "alto": "custo alto"}
ROTULO_DIFICULDADE = {"baixa": "baixa", "media": "média", "alta": "alta"}


def _pct(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",") + "%"


def _num(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _rotulo_campo(base: BaseConhecimento, campo_id: str, valor: Any) -> str:
    try:
        campo = base.campo(campo_id)
    except Exception:  # campo opcional ausente em versões antigas
        return str(valor)
    for opcao in campo.get("opcoes", []):
        if str(opcao["valor"]) == str(valor):
            return opcao["rotulo"]
    return str(valor)


def _motivos_da_trilha(avaliada: TrilhaAvaliada, base: BaseConhecimento) -> list[str]:
    limite = int(base.calibracao.get("max_justificativas", 5))
    motivos = [c.como_texto() for c in avaliada.pontos_fortes[:limite]]
    for regra in avaliada.bonus:
        motivos.append(f"Combinação identificada: {regra.justificativa}")
    for regra in avaliada.penalidades:
        motivos.append(
            f"Penalidade aplicada (fator {_num(regra.fator)}): {regra.justificativa}"
        )
    return motivos


def gerar_markdown(
    resultado: Resultado,
    plano: PlanoAcao,
    base: BaseConhecimento,
    perfil: dict[str, Any] | None = None,
    hoje: date | None = None,
) -> str:
    """Monta o plano de ação completo em Markdown."""
    perfil = perfil or {}
    hoje = hoje or date.today()
    top: TrilhaAvaliada = resultado.top
    trilha = base.trilha(top.id)

    linhas: list[str] = []
    adicionar = linhas.append

    nome = perfil.get("nome") or "Estudante"
    adicionar(f"# Plano de carreira em TI — {nome}")
    adicionar("")
    adicionar(
        f"*Gerado em {hoje.strftime('%d/%m/%Y')} · motor de inferência ponderada v2 "
        f"· base de conhecimento com {len(base.trilhas)} trilhas e {len(base.perguntas)} perguntas.*"
    )
    adicionar("")

    # -- resumo -------------------------------------------------------
    adicionar("## 1. Resultado da análise")
    adicionar("")
    adicionar(f"**Trilha recomendada: {trilha.nome} — {_pct(top.percentual)} de aderência.**")
    adicionar("")
    adicionar(trilha.descricao)
    adicionar("")
    adicionar("| Posição | Trilha | Compatibilidade |")
    adicionar("|---|---|---|")
    for posicao, avaliada in enumerate(resultado.top3, start=1):
        adicionar(f"| {posicao}º | {avaliada.nome} | {_pct(avaliada.percentual)} |")
    adicionar("")
    if resultado.empate:
        adicionar(f"> ⚠️ **Empate técnico:** {resultado.mensagem_confianca}")
        if resultado.desempate:
            adicionar(
                f"> Pergunta que mais separa as trilhas: “{resultado.desempate['pergunta']}”. "
                f"{resultado.desempate['acao']}"
            )
        adicionar("")
    adicionar(
        f"Confiança do resultado: **{ROTULO_CONFIANCA.get(resultado.nivel_confianca, resultado.nivel_confianca)}** "
        f"({_num(resultado.confianca)}). {resultado.mensagem_confianca}"
    )
    if resultado.sensibilidade.get("estabilidade") is not None:
        estabilidade = resultado.sensibilidade["estabilidade"]
        adicionar("")
        adicionar(
            f"Estabilidade: em {estabilidade * 100:.0f}% das simulações com variação de ±1 ponto "
            "nas respostas, a primeira colocada se manteve."
        )
    adicionar("")

    # -- ranking completo ---------------------------------------------
    adicionar("## 2. Ranking completo de compatibilidade")
    adicionar("")
    adicionar("| # | Trilha | Compatibilidade | Força | Certeza | Ajustes (objetivo × modalidade) |")
    adicionar("|---|---|---|---|---|---|")
    for posicao, avaliada in enumerate(resultado.ranking, start=1):
        adicionar(
            f"| {posicao} | {avaliada.nome} | {_pct(avaliada.percentual)} | "
            f"{_num(avaliada.forca)} | {_num(avaliada.certeza)} | "
            f"{_num(avaliada.ajuste_objetivo)} × {_num(avaliada.ajuste_modalidade)} |"
        )
    adicionar("")

    # -- justificativas -----------------------------------------------
    adicionar("## 3. Por que essa trilha")
    adicionar("")
    for motivo in _motivos_da_trilha(top, base):
        adicionar(f"- {motivo}")
    if top.pontos_atencao:
        adicionar("")
        adicionar("**Sinais de atenção:**")
        for contribuicao in [c for c in top.pontos_atencao if abs(c.peso) >= 0.15][:3]:
            adicionar(f"- {contribuicao.como_texto()} — puxou a aderência para baixo.")
    adicionar("")

    # -- eixos --------------------------------------------------------
    adicionar("## 4. Perfil por eixo")
    adicionar("")
    adicionar("| Eixo | Seu perfil | Trilha recomendada |")
    adicionar("|---|---|---|")
    for eixo in base.eixos:
        seu = resultado.eixos_usuario.get(eixo, 0.0)
        ideal = trilha.eixos.get(eixo, 0.0)
        adicionar(
            f"| {base.eixos_nomes.get(eixo, eixo)} | {seu * 100:.0f}% | {ideal * 100:.0f}% |"
        )
    adicionar("")

    # -- lacunas ------------------------------------------------------
    analise = plano.analise
    nivel_nome = base.niveis[plano.nivel_alvo]["rotulo"]
    adicionar(f"## 5. Lacunas para o nível {nivel_nome}")
    adicionar("")
    adicionar(
        f"Cobertura atual das competências exigidas: **{_pct(analise.cobertura)}**. "
        f"Esforço estimado: **{analise.horas_totais}h**."
    )
    adicionar("")
    if analise.lacunas:
        adicionar("| Prioridade | Competência | Atual → necessário | Lacuna | Horas | Classificação |")
        adicionar("|---|---|---|---|---|---|")
        for lacuna in analise.lacunas:
            adicionar(
                f"| {_num(lacuna.prioridade)} | {lacuna.nome} | {lacuna.nivel_atual} → "
                f"{lacuna.nivel_necessario} | {lacuna.lacuna} | {lacuna.horas_estimadas}h | "
                f"{lacuna.classificacao} |"
            )
    else:
        adicionar("Nenhuma lacuna: o perfil declarado já cobre o nível alvo nesta trilha.")
    adicionar("")
    if analise.cobertas:
        adicionar(
            "**Pontos fortes já demonstrados:** "
            + ", ".join(f"{c.nome} (nível {c.nivel_atual})" for c in analise.cobertas[:6])
            + "."
        )
        adicionar("")

    # -- roadmap ------------------------------------------------------
    adicionar("## 6. Roadmap personalizado")
    adicionar("")
    adicionar(plano.resumo)
    adicionar("")
    adicionar(f"{plano.mensagem_prazo}")
    adicionar("")
    if not plano.fases:
        adicionar("_Sem fases de estudo: siga para consolidação em projeto._")
        adicionar("")
    for fase in plano.fases:
        adicionar(f"### Fase {fase.numero} — {fase.titulo} (semanas {fase.semanas[0]}–{fase.semanas[1]})")
        adicionar("")
        adicionar(f"*Objetivo:* {fase.objetivo}")
        adicionar("")
        for item in fase.itens:
            adicionar(f"**{item.ordem}. {item.nome}** — {item.horas}h · lacuna {item.lacuna} · {item.classificacao}")
            adicionar("")
            adicionar(f"- Por que: {item.porque}")
            if item.recursos:
                for recurso in item.recursos:
                    adicionar(f"- Estudar: [{recurso['titulo']}]({recurso['url']}) ({recurso['tipo']})")
            if item.pratica:
                adicionar(f"- Prática: {item.pratica}")
            adicionar("")
        adicionar(f"**Entregável da fase:** {fase.entregavel}")
        adicionar("")

    # -- certificações ------------------------------------------------
    adicionar("## 7. Certificações recomendadas")
    adicionar("")
    if plano.certificacoes:
        for certificacao in plano.certificacoes:
            adicionar(
                f"- **[{certificacao['nome']}]({certificacao['link']})** — "
                f"nível {certificacao['nivel']}, {ROTULO_CUSTO.get(certificacao['custo'], certificacao['custo'])}. "
                f"{certificacao['porque']}"
            )
    else:
        adicionar("_Nenhuma certificação cadastrada para esta trilha._")
    adicionar("")

    # -- portfólio ----------------------------------------------------
    adicionar("## 8. Projetos para o portfólio")
    adicionar("")
    for projeto in plano.projetos:
        adicionar(f"### {projeto['titulo']} ({ROTULO_DIFICULDADE.get(projeto['dificuldade'], projeto['dificuldade'])})")
        adicionar("")
        adicionar(projeto["descricao"])
        adicionar("")
        if projeto.get("cobre"):
            nomes = [base.recurso(cid).nome if base.recurso(cid) else cid for cid in projeto["cobre"]]
            adicionar(f"- Fecha lacunas em: {', '.join(nomes)}.")
        adicionar(f"- Diferencial: {projeto['diferencial']}")
        adicionar("")

    # -- próximos passos ---------------------------------------------
    adicionar("## 9. Próximos passos")
    adicionar("")
    for indice, passo in enumerate(plano.proximos_passos, start=1):
        adicionar(f"{indice}. {passo}")
    adicionar("")

    # -- metodologia --------------------------------------------------
    adicionar("## 10. Como o resultado foi calculado")
    adicionar("")
    adicionar(
        "1. Cada resposta de afinidade (escala 1–5) foi normalizada para 0–1 e multiplicada pelo peso "
        "que a pergunta tem em cada uma das 10 trilhas."
    )
    adicionar(
        "2. Os pesos positivos e negativos definem a faixa possível de cada trilha; a pontuação bruta é "
        "normalizada dentro dessa faixa (0 a 1)."
    )
    adicionar(
        "3. As evidências foram combinadas por fatores de certeza (modelo de MYCIN), gerando a medida de "
        "consistência do perfil."
    )
    adicionar(
        "4. Regras de conflito aplicaram penalidades (perfis contraditórios) e bônus (combinações coerentes), "
        "e o objetivo/modalidade ajustaram a empregabilidade de cada trilha."
    )
    adicionar(
        "5. O percentual final usa a calibração da base (teto de "
        f"{float(base.calibracao.get('teto', 0.97)) * 100:.0f}% e expoente "
        f"{base.calibracao.get('expoente', 0.85)}), que comprime a base da escala."
    )
    adicionar("")
    adicionar(
        "> Este relatório é uma orientação construída a partir das suas respostas. Não é diagnóstico "
        "vocacional nem garantia de empregabilidade: use-o como hipótese de trabalho, não como veredito."
    )
    adicionar("")
    return "\n".join(linhas)


def gerar_json(
    resultado: Resultado, plano: PlanoAcao, perfil: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Versão estruturada do relatório, útil para integrações e testes."""
    return {
        "perfil": perfil or {},
        "resultado": resultado.para_dict(),
        "plano": plano.para_dict(),
    }
