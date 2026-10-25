"""Motor de inferência ponderado com fatores de certeza.

O cálculo segue quatro camadas, todas parametrizadas pela base JSON:

1. **Pontuação ponderada** — cada resposta Likert (1..5) é normalizada para
   [0,1] e multiplicada pelo peso da pergunta para cada trilha (pesos podem ser
   negativos, representando características que afastam o perfil da trilha).
2. **Fator de certeza (MYCIN)** — as evidências de cada pergunta são combinadas
   por fatores de certeza, produzindo uma medida de consistência das respostas.
3. **Regras de conflito** — penalidades e bônus condicionais ajustam a força
   de cada trilha quando o perfil apresenta combinações contraditórias.
4. **Ajustes de contexto** — objetivo de carreira e modalidade de trabalho
   aplicam multiplicadores finais.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .base_conhecimento import BaseConhecimento, Pergunta, RegraCondicional, Trilha

ESCALA_MIN_PADRAO = 1
ESCALA_MAX_PADRAO = 5


# ----------------------------------------------------------------- utilidades


def normalizar_resposta(valor: float, escala: dict[str, Any] | None = None) -> float:
    """Converte uma resposta da escala Likert (1..5) para o intervalo [0,1]."""
    if isinstance(valor, bool):
        raise TypeError("Resposta booleana não é válida para a escala Likert")
    minimo = (escala or {}).get("min", ESCALA_MIN_PADRAO)
    maximo = (escala or {}).get("max", ESCALA_MAX_PADRAO)
    if maximo == minimo:
        raise ValueError("Escala inválida: mínimo igual ao máximo")
    if not (minimo <= float(valor) <= maximo):
        raise ValueError(f"Resposta {valor} fora da escala {minimo}..{maximo}")
    return (float(valor) - minimo) / (maximo - minimo)


def combinar_certeza(cf1: float | None, cf2: float) -> float:
    """Combina duas evidências pelo modelo de fatores de certeza de MYCIN."""
    if cf1 is None:
        return cf2
    if cf1 >= 0 and cf2 >= 0:
        return cf1 + cf2 * (1 - cf1)
    if cf1 < 0 and cf2 < 0:
        return cf1 + cf2 * (1 + cf1)
    denominador = 1 - min(abs(cf1), abs(cf2))
    if denominador == 0:
        return 0.0
    return (cf1 + cf2) / denominador


def _limitar(valor: float, minimo: float = 0.0, maximo: float = 1.0) -> float:
    return max(minimo, min(maximo, valor))


def _condicao_atendida(quando: dict[str, dict[str, float]], respostas: dict[str, float]) -> bool:
    for pergunta_id, condicao in quando.items():
        valor = respostas.get(pergunta_id)
        if valor is None:
            return False
        if "min" in condicao and valor < condicao["min"]:
            return False
        if "max" in condicao and valor > condicao["max"]:
            return False
        if "entre" in condicao:
            faixa = condicao["entre"]
            if isinstance(faixa, (list, tuple)) and len(faixa) == 2:
                if not (faixa[0] <= valor <= faixa[1]):
                    return False
            else:
                raise ValueError(f"Condição 'entre' inválida na pergunta {pergunta_id}")
    return True


# ------------------------------------------------------------------- modelos


@dataclass(frozen=True)
class Contribuicao:
    pergunta_id: str
    texto: str
    resposta: float
    peso: float
    evidencia: float

    def como_texto(self, escala_max: float = 5) -> str:
        peso = f"{self.peso:+.2f}".replace(".", ",")
        return (
            f"“{self.texto}” — você respondeu {self.resposta:g}/{escala_max:g} "
            f"(peso {peso} nesta trilha)"
        )


@dataclass(frozen=True)
class RegraAplicada:
    id: str
    fator: float
    justificativa: str


@dataclass(frozen=True)
class TrilhaAvaliada:
    id: str
    nome: str
    percentual: float
    forca: float
    certeza: float
    fator_certeza: float
    cobertura: float
    ajuste_objetivo: float
    ajuste_modalidade: float
    penalidades: tuple[RegraAplicada, ...] = ()
    bonus: tuple[RegraAplicada, ...] = ()
    contribuicoes: tuple[Contribuicao, ...] = ()
    pontos_fortes: tuple[Contribuicao, ...] = ()
    pontos_atencao: tuple[Contribuicao, ...] = ()

    @property
    def ajuste_total(self) -> float:
        return self.ajuste_objetivo * self.ajuste_modalidade

    def para_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "percentual": self.percentual,
            "forca": round(self.forca, 4),
            "certeza": round(self.certeza, 4),
            "fator_certeza": round(self.fator_certeza, 4),
            "cobertura": round(self.cobertura, 4),
            "ajuste_objetivo": self.ajuste_objetivo,
            "ajuste_modalidade": self.ajuste_modalidade,
            "penalidades": [r.__dict__ for r in self.penalidades],
            "bonus": [r.__dict__ for r in self.bonus],
            "pontos_fortes": [c.__dict__ for c in self.pontos_fortes],
            "pontos_atencao": [c.__dict__ for c in self.pontos_atencao],
        }


@dataclass(frozen=True)
class Resultado:
    ranking: tuple[TrilhaAvaliada, ...]
    eixos_usuario: dict[str, float]
    respostas: dict[str, float]
    confianca: float
    nivel_confianca: str
    mensagem_confianca: str
    cobertura: float
    empate: bool = False
    co_recomendadas: tuple[str, ...] = ()
    desempate: dict[str, Any] | None = None
    sensibilidade: dict[str, Any] = field(default_factory=dict)
    objetivo: str | None = None
    modalidade: str | None = None
    nivel_alvo: str = "junior"

    @property
    def top(self) -> TrilhaAvaliada:
        return self.ranking[0]

    @property
    def top3(self) -> tuple[TrilhaAvaliada, ...]:
        return self.ranking[:3]

    def por_id(self, trilha_id: str) -> TrilhaAvaliada | None:
        for avaliada in self.ranking:
            if avaliada.id == trilha_id:
                return avaliada
        return None

    def para_dict(self) -> dict[str, Any]:
        return {
            "top": self.top.id,
            "top3": [t.id for t in self.top3],
            "ranking": [t.para_dict() for t in self.ranking],
            "eixos_usuario": {k: round(v, 4) for k, v in self.eixos_usuario.items()},
            "confianca": round(self.confianca, 4),
            "nivel_confianca": self.nivel_confianca,
            "cobertura": round(self.cobertura, 4),
            "empate": self.empate,
            "co_recomendadas": list(self.co_recomendadas),
            "desempate": self.desempate,
            "sensibilidade": self.sensibilidade,
            "objetivo": self.objetivo,
            "modalidade": self.modalidade,
            "nivel_alvo": self.nivel_alvo,
            "respostas": dict(self.respostas),
        }


# --------------------------------------------------------------------- motor


def _respostas_validas(
    base: BaseConhecimento, respostas: dict[str, Any]
) -> dict[str, float]:
    """Filtra apenas respostas Likert conhecidas e numéricas."""
    validas: dict[str, float] = {}
    for pergunta in base.perguntas:
        valor = respostas.get(pergunta.id)
        if valor is None or valor == "":
            continue
        try:
            numero = float(valor)
        except (TypeError, ValueError) as erro:
            raise ValueError(f"Resposta inválida para {pergunta.id}: {valor!r}") from erro
        normalizar_resposta(numero, base.escala)  # valida a faixa
        validas[pergunta.id] = numero
    return validas


def _componentes_trilha(
    base: BaseConhecimento,
    trilha: Trilha,
    perguntas: Iterable[Pergunta],
    respostas: dict[str, float],
) -> dict[str, Any]:
    """Calcula força normalizada e fator de certeza de uma trilha."""
    bruto = 0.0
    maximo = 0.0
    minimo = 0.0
    peso_absoluto_respondido = 0.0
    peso_absoluto_total = 0.0
    maior_peso = 0.0
    evidencias: list[tuple[float, float]] = []

    for pergunta in perguntas:
        peso = pergunta.peso_para(trilha.id)
        if peso == 0:
            continue
        peso_absoluto_total += abs(peso)
        maior_peso = max(maior_peso, abs(peso))
        if pergunta.id not in respostas:
            continue
        alfa = normalizar_resposta(respostas[pergunta.id], base.escala)
        bruto += peso * alfa
        maximo += max(peso, 0.0)
        minimo += min(peso, 0.0)
        peso_absoluto_respondido += abs(peso)
        evidencias.append((peso, alfa))

    amplitude = maximo - minimo
    if amplitude <= 0 or peso_absoluto_respondido == 0:
        forca = 0.5
    else:
        forca = _limitar((bruto - minimo) / amplitude)

    # Fatores de certeza: evidência de cada pergunta, da mais forte para a mais fraca.
    cf: float | None = None
    if maior_peso > 0 and evidencias:
        escaladas = [(peso / maior_peso, alfa) for peso, alfa in evidencias]
        escaladas.sort(key=lambda item: -abs(item[0] * (2 * item[1] - 1)))
        for peso_norm, alfa in escaladas:
            evidencia = peso_norm * (2 * alfa - 1)
            cf = combinar_certeza(cf, evidencia)
    cf = 0.0 if cf is None else _limitar(cf, -1.0, 1.0)

    cobertura = peso_absoluto_respondido / peso_absoluto_total if peso_absoluto_total else 0.0
    return {
        "forca": forca,
        "cf": cf,
        "certeza": abs(cf),
        "cobertura": cobertura,
        "bruto": bruto,
    }


def _regras_aplicadas(
    regras: Iterable[RegraCondicional], trilha_id: str, respostas: dict[str, float]
) -> tuple[tuple[RegraAplicada, ...], float]:
    aplicadas: list[RegraAplicada] = []
    fator_total = 1.0
    for regra in regras:
        if regra.trilha != trilha_id:
            continue
        if _condicao_atendida(regra.quando, respostas):
            aplicadas.append(RegraAplicada(regra.id, regra.fator, regra.justificativa))
            fator_total *= regra.fator
    return tuple(aplicadas), fator_total


def _calibrar(forca_final: float, base: BaseConhecimento) -> float:
    calibracao = base.calibracao
    expoente = float(calibracao.get("expoente", 0.85))
    teto = float(calibracao.get("teto", 0.97))
    return round(100 * teto * (_limitar(forca_final) ** expoente), 1)


def pontuar(
    base: BaseConhecimento,
    respostas: dict[str, Any],
    objetivo: str | None = None,
    modalidade: str | None = None,
) -> dict[str, float]:
    """Atalho que devolve apenas o percentual de cada trilha (sem detalhes)."""
    validas = _respostas_validas(base, respostas)
    ajuste_obj = base.ajustes_objetivo.get(objetivo or "", {})
    ajuste_mod = base.ajustes_modalidade.get(modalidade or "", {})
    percentuais: dict[str, float] = {}
    for trilha in base.trilhas.values():
        componentes = _componentes_trilha(base, trilha, base.perguntas, validas)
        _, fator_penalidade = _regras_aplicadas(base.penalidades, trilha.id, validas)
        _, fator_bonus = _regras_aplicadas(base.bonus, trilha.id, validas)
        final = componentes["forca"] * fator_penalidade * fator_bonus
        final *= ajuste_obj.get(trilha.id, 1.0) * ajuste_mod.get(trilha.id, 1.0)
        percentuais[trilha.id] = _calibrar(final, base)
    return percentuais


def _ordenar(ranking: list[TrilhaAvaliada], base: BaseConhecimento) -> list[TrilhaAvaliada]:
    """Percentual desc; empate resolvido por empregabilidade de entrada e nome."""
    return sorted(
        ranking,
        key=lambda t: (
            -t.percentual,
            -base.trilha(t.id).mercado.get("entrada_junior", 0.0),
            t.nome,
        ),
    )


def _eixos_do_usuario(
    base: BaseConhecimento, respostas: dict[str, float]
) -> dict[str, float]:
    somas = {eixo: 0.0 for eixo in base.eixos}
    contagens = {eixo: 0 for eixo in base.eixos}
    for pergunta in base.perguntas:
        valor = respostas.get(pergunta.id)
        if valor is None:
            continue
        somas[pergunta.eixo] += normalizar_resposta(valor, base.escala)
        contagens[pergunta.eixo] += 1
    return {eixo: (somas[eixo] / contagens[eixo] if contagens[eixo] else 0.0) for eixo in base.eixos}


def _contribuicoes(
    base: BaseConhecimento, trilha: Trilha, respostas: dict[str, float]
) -> tuple[tuple[Contribuicao, ...], tuple[Contribuicao, ...], tuple[Contribuicao, ...]]:
    itens: list[Contribuicao] = []
    for pergunta in base.perguntas:
        valor = respostas.get(pergunta.id)
        if valor is None:
            continue
        peso = pergunta.peso_para(trilha.id)
        if peso == 0:
            continue
        alfa = normalizar_resposta(valor, base.escala)
        itens.append(
            Contribuicao(
                pergunta_id=pergunta.id,
                texto=pergunta.texto,
                resposta=valor,
                peso=peso,
                evidencia=peso * (alfa - 0.5),
            )
        )
    fortes = tuple(sorted((c for c in itens if c.evidencia > 0), key=lambda c: -c.evidencia))
    atencao = tuple(sorted((c for c in itens if c.evidencia < 0), key=lambda c: c.evidencia))
    return tuple(itens), fortes, atencao


def _sugerir_desempate(
    base: BaseConhecimento, trilha_a: Trilha, trilha_b: Trilha, respostas: dict[str, float]
) -> dict[str, Any] | None:
    """Aponta a pergunta que melhor separa duas trilhas empatadas."""
    melhor: tuple[Pergunta, float] | None = None
    for pergunta in base.perguntas:
        diferenca = abs(pergunta.peso_para(trilha_a.id) - pergunta.peso_para(trilha_b.id))
        if diferenca <= 0:
            continue
        if melhor is None or diferenca > melhor[1]:
            melhor = (pergunta, diferenca)
    if melhor is None:
        return None
    pergunta, diferenca = melhor
    resposta = respostas.get(pergunta.id)

    # Competência essencial presente em uma trilha e ausente na outra.
    competencias_a = {c.id for c in trilha_a.competencias_essenciais}
    competencias_b = {c.id for c in trilha_b.competencias_essenciais}
    exclusivas = sorted(competencias_b - competencias_a) or sorted(competencias_a - competencias_b)
    nomes_exclusivas = [base.recurso(cid).nome if base.recurso(cid) else cid for cid in exclusivas[:3]]

    return {
        "pergunta_id": pergunta.id,
        "pergunta": pergunta.texto,
        "diferenca_de_peso": round(diferenca, 3),
        "sua_resposta": resposta,
        "trilhas": [trilha_a.nome, trilha_b.nome],
        "competencias_decisivas": nomes_exclusivas,
        "acao": (
            f"Teste na prática: dedique duas semanas ao conteúdo de "
            f"{', '.join(nomes_exclusivas) if nomes_exclusivas else 'uma competência exclusiva da segunda trilha'} "
            f"e reavalie sua motivação. Se a tarefa parecer natural, a segunda trilha tende a ser a escolha."
        ),
    }


def _sensibilidade(
    base: BaseConhecimento,
    respostas: dict[str, float],
    objetivo: str | None,
    modalidade: str | None,
) -> dict[str, Any]:
    """Perturba cada resposta em ±1 ponto e mede a estabilidade do 1º lugar."""
    if not respostas:
        return {"perturbacoes": 0, "estabilidade": None, "alteracoes": []}
    min_escala = int(base.escala.get("min", ESCALA_MIN_PADRAO))
    max_escala = int(base.escala.get("max", ESCALA_MAX_PADRAO))
    base_pontos = pontuar(base, respostas, objetivo, modalidade)
    lider = max(base_pontos, key=lambda t: base_pontos[t])

    total = 0
    alteracoes: list[dict[str, Any]] = []
    for pergunta_id, valor in respostas.items():
        for delta in (-1, 1):
            novo = valor + delta
            if not (min_escala <= novo <= max_escala):
                continue
            total += 1
            simuladas = dict(respostas)
            simuladas[pergunta_id] = novo
            pontos = pontuar(base, simuladas, objetivo, modalidade)
            novo_lider = max(pontos, key=lambda t: pontos[t])
            if novo_lider != lider:
                alteracoes.append(
                    {
                        "pergunta_id": pergunta_id,
                        "de": valor,
                        "para": novo,
                        "novo_lider": novo_lider,
                        "novo_lider_percentual": pontos[novo_lider],
                    }
                )
    estabilidade = 1 - (len(alteracoes) / total) if total else None
    return {
        "perturbacoes": total,
        "estabilidade": round(estabilidade, 3) if estabilidade is not None else None,
        "lider": lider,
        "alteracoes": alteracoes[:5],
        "total_alteracoes": len(alteracoes),
    }


def avaliar(
    base: BaseConhecimento,
    respostas: dict[str, Any],
    objetivo: str | None = None,
    modalidade: str | None = None,
    nivel_alvo: str = "junior",
    com_sensibilidade: bool = True,
) -> Resultado:
    """Executa o motor completo e devolve ranking, confiança e justificativas."""
    validas = _respostas_validas(base, respostas)
    if not validas:
        raise ValueError("Nenhuma resposta de afinidade válida foi informada")

    ajustes_obj = base.ajustes_objetivo.get(objetivo or "", {})
    ajustes_mod = base.ajustes_modalidade.get(modalidade or "", {})

    avaliadas: list[TrilhaAvaliada] = []
    for trilha in base.trilhas.values():
        componentes = _componentes_trilha(base, trilha, base.perguntas, validas)
        penalidades, fator_penalidade = _regras_aplicadas(base.penalidades, trilha.id, validas)
        bonus, fator_bonus = _regras_aplicadas(base.bonus, trilha.id, validas)
        ajuste_objetivo = ajustes_obj.get(trilha.id, 1.0)
        ajuste_modalidade = ajustes_mod.get(trilha.id, 1.0)
        final = componentes["forca"] * fator_penalidade * fator_bonus * ajuste_objetivo * ajuste_modalidade
        contribuicoes, fortes, atencao = _contribuicoes(base, trilha, validas)
        avaliadas.append(
            TrilhaAvaliada(
                id=trilha.id,
                nome=trilha.nome,
                percentual=_calibrar(final, base),
                forca=componentes["forca"],
                certeza=componentes["certeza"],
                fator_certeza=componentes["cf"],
                cobertura=componentes["cobertura"],
                ajuste_objetivo=ajuste_objetivo,
                ajuste_modalidade=ajuste_modalidade,
                penalidades=penalidades,
                bonus=bonus,
                contribuicoes=contribuicoes,
                pontos_fortes=fortes,
                pontos_atencao=atencao,
            )
        )

    ranking = _ordenar(avaliadas, base)
    margem = ranking[0].percentual - ranking[1].percentual if len(ranking) > 1 else 100.0
    limiar = float(base.calibracao.get("limiar_empate", 3.0))
    empate = margem <= limiar

    confianca = _limitar(0.6 * min(margem / 18.0, 1.0) + 0.4 * ranking[0].certeza)
    if confianca >= float(base.calibracao.get("confianca_alta", 0.62)):
        nivel = "alta"
    elif confianca >= float(base.calibracao.get("confianca_media", 0.45)):
        nivel = "media"
    else:
        nivel = "baixa"

    if empate:
        mensagem = base.mensagens["empate"]
    elif nivel == "baixa":
        mensagem = base.mensagens["confianca_baixa"]
    elif nivel == "media":
        mensagem = base.mensagens.get("confianca_media", base.mensagens["confianca_alta"])
    else:
        mensagem = base.mensagens["confianca_alta"]

    cobertura = sum(t.cobertura for t in ranking) / len(ranking) if ranking else 0.0
    desempate = None
    if empate and len(ranking) > 1:
        desempate = _sugerir_desempate(
            base, base.trilha(ranking[0].id), base.trilha(ranking[1].id), validas
        )

    return Resultado(
        ranking=tuple(ranking),
        eixos_usuario=_eixos_do_usuario(base, validas),
        respostas=validas,
        confianca=round(confianca, 3),
        nivel_confianca=nivel,
        mensagem_confianca=mensagem,
        cobertura=round(cobertura, 3),
        empate=empate,
        co_recomendadas=tuple(t.id for t in ranking[:2]) if empate else (),
        desempate=desempate,
        sensibilidade=_sensibilidade(base, validas, objetivo, modalidade) if com_sensibilidade else {},
        objetivo=objetivo,
        modalidade=modalidade,
        nivel_alvo=nivel_alvo,
    )
