"""Geração do roadmap personalizado, certificações e projetos de portfólio."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .base_conhecimento import BaseConhecimento, Trilha
from .lacunas import AnaliseLacunas, analisar_lacunas

SEMANAS_POR_MES = 4.345
HORAS_SEMANA_PADRAO = 10
ROTULO_DIFICULDADE = {"baixa": "baixa", "media": "média", "alta": "alta"}

TITULOS_FASES = (
    ("Fundação e primeira entrega", "Fechar as lacunas que bloqueiam qualquer prática da trilha."),
    ("Profundidade técnica", "Transformar fundamento em competência demonstrável em projeto."),
    ("Portfólio e entrada no mercado", "Consolidar entrega, narrativa e candidatura."),
)


@dataclass(frozen=True)
class ItemEstudo:
    ordem: int
    fase: int
    competencia_id: str
    nome: str
    nivel_atual: int
    nivel_necessario: int
    lacuna: int
    horas: int
    classificacao: str
    porque: str
    recursos: tuple[dict[str, str], ...]
    pratica: str

    def para_dict(self) -> dict[str, Any]:
        return {
            "ordem": self.ordem,
            "fase": self.fase,
            "competencia_id": self.competencia_id,
            "nome": self.nome,
            "nivel_atual": self.nivel_atual,
            "nivel_necessario": self.nivel_necessario,
            "lacuna": self.lacuna,
            "horas": self.horas,
            "classificacao": self.classificacao,
            "porque": self.porque,
            "recursos": list(self.recursos),
            "pratica": self.pratica,
        }


@dataclass(frozen=True)
class FasePlano:
    numero: int
    titulo: str
    objetivo: str
    semanas: tuple[int, int]
    itens: tuple[ItemEstudo, ...]
    entregavel: str
    horas: int

    def para_dict(self) -> dict[str, Any]:
        return {
            "numero": self.numero,
            "titulo": self.titulo,
            "objetivo": self.objetivo,
            "semanas": list(self.semanas),
            "horas": self.horas,
            "entregavel": self.entregavel,
            "itens": [i.para_dict() for i in self.itens],
        }


@dataclass(frozen=True)
class PlanoAcao:
    trilha_id: str
    trilha_nome: str
    nivel_alvo: str
    resumo: str
    fases: tuple[FasePlano, ...]
    certificacoes: tuple[dict[str, Any], ...]
    projetos: tuple[dict[str, Any], ...]
    proximos_passos: tuple[str, ...]
    horas_totais: int
    horas_semana: int
    semanas_estimadas: int
    prazo_meses: int
    alerta_prazo: bool
    mensagem_prazo: str
    analise: AnaliseLacunas

    def para_dict(self, incluir_analise: bool = True) -> dict[str, Any]:
        dados = {
            "trilha": self.trilha_id,
            "trilha_nome": self.trilha_nome,
            "nivel_alvo": self.nivel_alvo,
            "resumo": self.resumo,
            "horas_totais": self.horas_totais,
            "horas_semana": self.horas_semana,
            "semanas_estimadas": self.semanas_estimadas,
            "prazo_meses": self.prazo_meses,
            "alerta_prazo": self.alerta_prazo,
            "mensagem_prazo": self.mensagem_prazo,
            "fases": [f.para_dict() for f in self.fases],
            "certificacoes": list(self.certificacoes),
            "projetos": list(self.projetos),
            "proximos_passos": list(self.proximos_passos),
        }
        if incluir_analise:
            dados["analise"] = self.analise.para_dict()
        return dados


def _dividir_fases(itens: list[ItemEstudo], horas_semana: int) -> list[list[ItemEstudo]]:
    """Divide os itens em até 3 fases equilibrando horas e mantendo a ordem."""
    if not itens:
        return []
    if len(itens) <= 2:
        return [itens]
    n = len(itens)
    alvo = sum(i.horas for i in itens) / 3

    melhor: tuple[float, int, int] | None = None
    for i in range(1, n - 1):
        for j in range(i + 1, n):
            grupos = (itens[:i], itens[i:j], itens[j:])
            horas = [sum(item.horas for item in grupo) for grupo in grupos]
            desvio = sum((h - alvo) ** 2 for h in horas)
            if melhor is None or desvio < melhor[0]:
                melhor = (desvio, i, j)
    if melhor is None:
        return [itens]
    _, i, j = melhor
    return [itens[:i], itens[i:j], itens[j:]]


def _ordenar_por_prerequisitos(base: BaseConhecimento, itens: list[ItemEstudo]) -> list[ItemEstudo]:
    """Reordena os itens respeitando pré-requisitos, preservando a prioridade.

    Um item só entra quando todos os seus pré-requisitos que também estão no
    plano já foram incluídos. Se houver ciclo, o de maior prioridade entra mesmo
    assim (o plano nunca fica incompleto).
    """
    if not itens:
        return []
    por_id = {item.competencia_id: item for item in itens}
    restantes = list(itens)
    prontos: set[str] = set()
    ordenados: list[ItemEstudo] = []
    while restantes:
        escolhido: ItemEstudo | None = None
        for item in restantes:
            recurso = base.recurso(item.competencia_id)
            pendentes = set(recurso.prerequisitos if recurso else ()) & set(por_id)
            if pendentes <= prontos:
                escolhido = item
                break
        if escolhido is None:
            escolhido = restantes[0]
        ordenados.append(escolhido)
        prontos.add(escolhido.competencia_id)
        restantes.remove(escolhido)
    return [replace(item, ordem=indice) for indice, item in enumerate(ordenados, start=1)]


def _itens_de_estudo(base: BaseConhecimento, analise: AnaliseLacunas) -> list[ItemEstudo]:
    itens: list[ItemEstudo] = []
    for ordem, lacuna in enumerate(analise.lacunas, start=1):
        recurso = base.recurso(lacuna.competencia_id)
        if lacuna.essencial:
            porque = (
                f"Competência essencial da trilha: você está no nível {lacuna.nivel_atual} "
                f"e o alvo {analise.nivel_alvo} pede {lacuna.nivel_necessario}."
            )
        else:
            porque = (
                f"Competência complementar: fecha a diferença entre {lacuna.nivel_atual} "
                f"e {lacuna.nivel_necessario} e aparece em vagas da área."
            )
        itens.append(
            ItemEstudo(
                ordem=ordem,
                fase=0,
                competencia_id=lacuna.competencia_id,
                nome=lacuna.nome,
                nivel_atual=lacuna.nivel_atual,
                nivel_necessario=lacuna.nivel_necessario,
                lacuna=lacuna.lacuna,
                horas=lacuna.horas_estimadas,
                classificacao=lacuna.classificacao,
                porque=porque,
                recursos=recurso.recursos if recurso else (),
                pratica=recurso.pratica if recurso else "",
            )
        )
    return _ordenar_por_prerequisitos(base, itens)


def _escolher_certificacoes(trilha: Trilha, nivel_alvo: str, limite: int = 3) -> tuple[dict[str, Any], ...]:
    ordem_custo = {"gratuito": 0, "baixo": 1, "medio": 2, "alto": 3}
    nivel_preferido = "iniciante" if nivel_alvo in ("estagio", "junior") else "intermediario"
    ordenadas = sorted(
        trilha.certificacoes,
        key=lambda c: (
            0 if c.nivel == nivel_preferido else 1,
            ordem_custo.get(c.custo, 9),
        ),
    )
    escolhidas: list[dict[str, Any]] = []
    for certificacao in ordenadas[:limite]:
        motivo = certificacao.quando
        if certificacao.custo in ("gratuito", "baixo"):
            motivo += " Custo acessível para quem está começando."
        escolhidas.append(
            {
                "nome": certificacao.nome,
                "custo": certificacao.custo,
                "nivel": certificacao.nivel,
                "link": certificacao.link,
                "porque": motivo,
            }
        )
    return tuple(escolhidas)


def _escolher_projetos(
    trilha: Trilha, analise: AnaliseLacunas, limite: int = 3
) -> tuple[dict[str, Any], ...]:
    prioridade_por_competencia = {
        lacuna.competencia_id: lacuna.prioridade + (1.0 if lacuna.essencial else 0.0)
        for lacuna in analise.lacunas
    }
    ordem_dificuldade = {"baixa": 0, "media": 1, "alta": 2}
    pontuados: list[tuple[float, int, dict[str, Any]]] = []
    for projeto in trilha.projetos:
        cobertura = sum(prioridade_por_competencia.get(cid, 0.0) for cid in projeto.competencias)
        pontuados.append(
            (
                cobertura,
                -ordem_dificuldade.get(projeto.dificuldade, 1),
                {
                    "titulo": projeto.titulo,
                    "descricao": projeto.descricao,
                    "dificuldade": projeto.dificuldade,
                    "diferencial": projeto.diferencial,
                    "cobre": [
                        cid
                        for cid in projeto.competencias
                        if any(lacuna.competencia_id == cid for lacuna in analise.lacunas)
                    ],
                    "competencias": list(projeto.competencias),
                },
            )
        )
    pontuados.sort(key=lambda item: (-item[0], -item[1]))
    return tuple(p[2] for p in pontuados[:limite])


def _projeto_da_fase(
    projetos: tuple[dict[str, Any], ...], competencias: set[str], ja_usados: set[str]
) -> dict[str, Any] | None:
    """Escolhe o projeto que mais cobre as competências da fase."""
    melhor: tuple[int, dict[str, Any]] | None = None
    for projeto in projetos:
        if projeto["titulo"] in ja_usados:
            continue
        nota = len(set(projeto["competencias"]) & competencias)
        if melhor is None or nota > melhor[0]:
            melhor = (nota, projeto)
    return melhor[1] if melhor else None


def _semanas_por_fase(itens: list[ItemEstudo], horas_semana: int) -> list[tuple[int, int]]:
    semanas: list[tuple[int, int]] = []
    atual = 1
    for grupo in itens:
        horas = sum(item.horas for item in grupo)
        duracao = max(1, int(round(horas / max(horas_semana, 1))))
        semanas.append((atual, atual + duracao - 1))
        atual += duracao
    return semanas


def gerar_plano(
    base: BaseConhecimento,
    trilha_id: str,
    conhecimentos: dict[str, object],
    nivel_alvo: str = "junior",
    horas_semana: int = HORAS_SEMANA_PADRAO,
    prazo_meses: int = 6,
    objetivo: str | None = None,
) -> PlanoAcao:
    """Monta fases de estudo, certificações e portfólio a partir das lacunas."""
    trilha = base.trilha(trilha_id)
    horas_semana = max(1, int(horas_semana or HORAS_SEMANA_PADRAO))
    prazo_meses = max(1, int(prazo_meses or 6))
    analise = analisar_lacunas(base, trilha_id, conhecimentos, nivel_alvo)

    itens = _itens_de_estudo(base, analise)
    grupos = _dividir_fases(itens, horas_semana)
    projetos = _escolher_projetos(trilha, analise)
    # O plano sempre termina com fases de projeto e de mercado, mesmo quando há
    # poucas lacunas: fechar lacuna sem entrega não gera empregabilidade.
    while len(grupos) < 3:
        grupos.append([])
    periodos = _semanas_por_fase(grupos, horas_semana)

    fases: list[FasePlano] = []
    projetos_usados: set[str] = set()
    for indice, grupo in enumerate(grupos):
        numero = indice + 1
        titulo, objetivo_fase = TITULOS_FASES[min(indice, len(TITULOS_FASES) - 1)]
        com_fase = tuple(
            ItemEstudo(
                ordem=item.ordem,
                fase=numero,
                competencia_id=item.competencia_id,
                nome=item.nome,
                nivel_atual=item.nivel_atual,
                nivel_necessario=item.nivel_necessario,
                lacuna=item.lacuna,
                horas=item.horas,
                classificacao=item.classificacao,
                porque=item.porque,
                recursos=item.recursos,
                pratica=item.pratica,
            )
            for item in grupo
        )
        entregavel = "Documentar o aprendizado no README do repositório e publicar um commit por semana."
        competencias_fase = {item.competencia_id for item in grupo}
        projeto = _projeto_da_fase(projetos, competencias_fase, projetos_usados)
        if projeto is None and projetos:
            projeto = projetos[indice % len(projetos)]
        if projeto:
            projetos_usados.add(projeto["titulo"])
            if grupo:
                entregavel = f"Entregar o projeto “{projeto['titulo']}” ({ROTULO_DIFICULDADE.get(projeto['dificuldade'], projeto['dificuldade'])})."
            else:
                entregavel = (
                    f"Sem novas competências nesta fase: publicar “{projeto['titulo']}” "
                    "com README explicando decisões técnicas."
                )
        fases.append(
            FasePlano(
                numero=numero,
                titulo=titulo,
                objetivo=objetivo_fase,
                semanas=periodos[indice],
                itens=com_fase,
                entregavel=entregavel,
                horas=sum(item.horas for item in com_fase),
            )
        )

    horas_totais = sum(item.horas for item in itens)
    semanas_estimadas = max(periodos[-1][1], 4) if periodos else 4
    semanas_prazo = int(prazo_meses * SEMANAS_POR_MES)
    alerta = semanas_estimadas > semanas_prazo

    if not itens:
        mensagem = (
            f"Você já cobre o nível {base.niveis[nivel_alvo]['rotulo']} nas competências desta trilha. "
            "O plano passa a ser de consolidação: aprofundar o que já sabe e provar em projeto."
        )
    elif alerta:
        mensagem = (
            f"O plano completo pede cerca de {semanas_estimadas} semanas com {horas_semana}h/semana, "
            f"mas seu prazo é de {prazo_meses} meses (~{semanas_prazo} semanas). "
            "Priorize as lacunas críticas e trate o restante como segundo ciclo."
        )
    else:
        mensagem = (
            f"O plano cabe no seu prazo: cerca de {semanas_estimadas} semanas "
            f"com {horas_semana}h por semana."
        )

    if not itens:
        resumo = (
            f"Plano de consolidação para {trilha.nome}: foco em projeto, certificação e narrativa profissional."
        )
    else:
        resumo = (
            f"Faltam {len(analise.lacunas)} competências ({len(analise.criticas)} críticas) para o nível "
            f"{base.niveis[nivel_alvo]['rotulo']} em {trilha.nome}. "
            f"Total estimado: {horas_totais}h de estudo dirigido."
        )

    proximos_passos = gerar_proximos_passos(base, trilha, analise, horas_semana)
    certificacoes = _escolher_certificacoes(trilha, nivel_alvo)

    return PlanoAcao(
        trilha_id=trilha.id,
        trilha_nome=trilha.nome,
        nivel_alvo=nivel_alvo,
        resumo=resumo,
        fases=tuple(fases),
        certificacoes=certificacoes,
        projetos=projetos,
        proximos_passos=proximos_passos,
        horas_totais=horas_totais,
        horas_semana=horas_semana,
        semanas_estimadas=semanas_estimadas,
        prazo_meses=prazo_meses,
        alerta_prazo=alerta,
        mensagem_prazo=mensagem,
        analise=analise,
    )


def gerar_proximos_passos(
    base: BaseConhecimento, trilha: Trilha, analise: AnaliseLacunas, horas_semana: int
) -> tuple[str, ...]:
    """Três ações imediatas para começar sem depender de mais planejamento."""
    passos: list[str] = []
    passos.append(
        f"Criar um repositório público “{trilha.id}-portfolio” com README explicando o objetivo da trilha "
        f"{trilha.nome} e a rotina de {horas_semana}h semanais."
    )
    if analise.lacunas:
        primeira = analise.lacunas[0]
        recurso = base.recurso(primeira.competencia_id)
        titulo = recurso.recursos[0]["titulo"] if recurso and recurso.recursos else primeira.nome
        passos.append(
            f"Começar por {primeira.nome} (nível {primeira.nivel_atual} → {primeira.nivel_necessario}): "
            f"{titulo}. Meta: {primeira.horas_estimadas}h de prática deliberada."
        )
    else:
        passos.append(
            "Escolher uma competência já dominada e publicar um projeto que a demonstre em nível avançado."
        )
    if trilha.projetos:
        projeto = trilha.projetos[0]
        passos.append(
            f"Reservar a primeira entrega do portfólio: “{projeto.titulo}”. "
            f"Publicar com README, decisões técnicas e instruções de execução."
        )
    passos.append(
        "Ao fim de cada fase, revisar as lacunas: o plano deve ser recalculado, não seguido cegamente."
    )
    return tuple(passos)
