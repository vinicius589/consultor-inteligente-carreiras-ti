"""Carregamento e validação da base de conhecimento (arquivos JSON).

Nenhuma regra, peso ou característica de trilha fica no código Python: tudo vem
de ``data/*.json``. Este módulo apenas interpreta e valida esses arquivos.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_DADOS_PADRAO = RAIZ_PROJETO / "data"

ARQUIVOS = ("trilhas.json", "perguntas.json", "regras.json", "recursos.json")


class ErroBaseConhecimento(ValueError):
    """Erro de consistência na base de conhecimento."""


@dataclass(frozen=True)
class Competencia:
    id: str
    essencial: bool
    peso: float
    niveis: dict[str, int]

    def nivel_necessario(self, nivel: str) -> int:
        return int(self.niveis.get(nivel, 0))


@dataclass(frozen=True)
class Certificacao:
    nome: str
    custo: str
    nivel: str
    link: str
    quando: str


@dataclass(frozen=True)
class Projeto:
    titulo: str
    descricao: str
    competencias: tuple[str, ...]
    dificuldade: str
    diferencial: str


@dataclass(frozen=True)
class Trilha:
    id: str
    nome: str
    resumo: str
    descricao: str
    dimensoes: dict[str, float]
    eixos: dict[str, float]
    competencias: tuple[Competencia, ...]
    tecnologias: tuple[str, ...]
    certificacoes: tuple[Certificacao, ...]
    projetos: tuple[Projeto, ...]
    mercado: dict[str, float]
    salario_junior: str
    areas_atuacao: tuple[str, ...]

    @property
    def competencias_essenciais(self) -> tuple[Competencia, ...]:
        return tuple(c for c in self.competencias if c.essencial)

    def competencia(self, competencia_id: str) -> Competencia | None:
        for c in self.competencias:
            if c.id == competencia_id:
                return c
        return None


@dataclass(frozen=True)
class Pergunta:
    id: str
    dimensao: str
    eixo: str
    texto: str
    ajuda: str
    pesos: dict[str, float]

    def peso_para(self, trilha_id: str) -> float:
        return float(self.pesos.get(trilha_id, 0.0))


@dataclass(frozen=True)
class RegraCondicional:
    id: str
    trilha: str
    quando: dict[str, dict[str, float]]
    fator: float
    justificativa: str


@dataclass(frozen=True)
class Recurso:
    nome: str
    categoria: str
    horas_base: int
    recursos: tuple[dict[str, str], ...]
    pratica: str
    prerequisitos: tuple[str, ...] = ()


@dataclass(frozen=True)
class BaseConhecimento:
    trilhas: dict[str, Trilha]
    eixos: tuple[str, ...]
    eixos_nomes: dict[str, str]
    dimensoes: dict[str, str]
    perguntas: tuple[Pergunta, ...]
    etapas: tuple[dict[str, Any], ...]
    escala: dict[str, Any]
    autoavaliacao: dict[str, Any]
    penalidades: tuple[RegraCondicional, ...]
    bonus: tuple[RegraCondicional, ...]
    ajustes_objetivo: dict[str, dict[str, float]]
    ajustes_modalidade: dict[str, dict[str, float]]
    niveis: dict[str, dict[str, str]]
    mensagens: dict[str, str]
    calibracao: dict[str, Any]
    recursos: dict[str, Recurso]
    _perguntas_por_id: dict[str, Pergunta] = field(default_factory=dict, repr=False)

    # -- consultas -----------------------------------------------------
    def trilha(self, trilha_id: str) -> Trilha:
        try:
            return self.trilhas[trilha_id]
        except KeyError as erro:
            raise ErroBaseConhecimento(f"Trilha inexistente: {trilha_id}") from erro

    def pergunta(self, pergunta_id: str) -> Pergunta | None:
        return self._perguntas_por_id.get(pergunta_id)

    def recurso(self, competencia_id: str) -> Recurso | None:
        return self.recursos.get(competencia_id)

    @property
    def ids_trilhas(self) -> tuple[str, ...]:
        return tuple(self.trilhas)

    def etapa(self, etapa_id: str) -> dict[str, Any]:
        for etapa in self.etapas:
            if etapa["id"] == etapa_id:
                return etapa
        raise ErroBaseConhecimento(f"Etapa inexistente: {etapa_id}")

    def campo(self, campo_id: str) -> dict[str, Any]:
        for etapa in self.etapas:
            for campo in etapa.get("campos", []):
                if campo["id"] == campo_id:
                    return campo
        raise ErroBaseConhecimento(f"Campo inexistente: {campo_id}")


def _ler_json(caminho: Path) -> dict[str, Any]:
    if not caminho.exists():
        raise ErroBaseConhecimento(f"Arquivo não encontrado: {caminho}")
    try:
        with caminho.open(encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError as erro:
        raise ErroBaseConhecimento(f"JSON inválido em {caminho.name}: {erro}") from erro


def _validar_ids_unicos(itens: Iterable[dict[str, Any]], rotulo: str) -> None:
    vistos: set[str] = set()
    for item in itens:
        identificador = item["id"]
        if identificador in vistos:
            raise ErroBaseConhecimento(f"{rotulo} com id duplicado: {identificador}")
        vistos.add(identificador)


def _montar_trilhas(dados: dict[str, Any]) -> tuple[dict[str, Trilha], tuple[str, ...], dict[str, str], dict[str, str]]:
    trilhas_brutas = dados.get("trilhas") or []
    if not trilhas_brutas:
        raise ErroBaseConhecimento("trilhas.json não contém trilhas")
    _validar_ids_unicos(trilhas_brutas, "Trilha")

    trilhas: dict[str, Trilha] = {}
    for bruta in trilhas_brutas:
        competencias = tuple(
            Competencia(
                id=c["id"],
                essencial=bool(c["essencial"]),
                peso=float(c["peso"]),
                niveis={nivel: int(valor) for nivel, valor in c["niveis"].items()},
            )
            for c in bruta["competencias"]
        )
        if len(competencias) < 6:
            raise ErroBaseConhecimento(f"Trilha {bruta['id']} tem menos de 6 competências")
        trilha = Trilha(
            id=bruta["id"],
            nome=bruta["nome"],
            resumo=bruta["resumo"],
            descricao=bruta["descricao"],
            dimensoes={k: float(v) for k, v in bruta["dimensoes"].items()},
            eixos={k: float(v) for k, v in bruta["eixos"].items()},
            competencias=competencias,
            tecnologias=tuple(bruta["tecnologias"]),
            certificacoes=tuple(
                Certificacao(
                    nome=c["nome"], custo=c["custo"], nivel=c["nivel"], link=c["link"], quando=c["quando"]
                )
                for c in bruta["certificacoes"]
            ),
            projetos=tuple(
                Projeto(
                    titulo=p["titulo"],
                    descricao=p["descricao"],
                    competencias=tuple(p["competencias"]),
                    dificuldade=p["dificuldade"],
                    diferencial=p["diferencial"],
                )
                for p in bruta["projetos"]
            ),
            mercado={k: float(v) for k, v in bruta["mercado"].items()},
            salario_junior=bruta["salario_junior"],
            areas_atuacao=tuple(bruta["areas_atuacao"]),
        )
        trilhas[trilha.id] = trilha

    eixos = tuple(dados["eixos"])
    eixos_nomes = dict(dados["eixos_nomes"])
    dimensoes = dict(dados["dimensoes"])
    for trilha in trilhas.values():
        faltando = set(eixos) - set(trilha.eixos)
        if faltando:
            raise ErroBaseConhecimento(f"Trilha {trilha.id} sem eixos: {sorted(faltando)}")
        desconhecidas = set(trilha.dimensoes) - set(dimensoes)
        if desconhecidas:
            raise ErroBaseConhecimento(f"Trilha {trilha.id} usa dimensões desconhecidas: {sorted(desconhecidas)}")
    return trilhas, eixos, eixos_nomes, dimensoes


def _montar_perguntas(
    dados: dict[str, Any], trilhas: dict[str, Trilha], eixos: tuple[str, ...]
) -> tuple[tuple[Pergunta, ...], tuple[dict[str, Any], ...], dict[str, Any], dict[str, Any]]:
    etapas = tuple(dados["etapas"])
    etapa_afinidades = next((e for e in etapas if e["id"] == "afinidades"), None)
    if etapa_afinidades is None:
        raise ErroBaseConhecimento("perguntas.json não tem a etapa 'afinidades'")

    brutas = etapa_afinidades.get("perguntas") or []
    if len(brutas) < 10:
        raise ErroBaseConhecimento("A etapa de afinidades precisa de pelo menos 10 perguntas")
    _validar_ids_unicos(brutas, "Pergunta")

    perguntas: list[Pergunta] = []
    for bruta in brutas:
        pesos = {tid: float(peso) for tid, peso in bruta["pesos"].items()}
        ids_invalidos = set(pesos) - set(trilhas)
        if ids_invalidos:
            raise ErroBaseConhecimento(
                f"Pergunta {bruta['id']} aponta para trilhas inexistentes: {sorted(ids_invalidos)}"
            )
        if len([p for p in pesos.values() if p > 0]) < 2:
            raise ErroBaseConhecimento(f"Pergunta {bruta['id']} não discrimina nenhuma trilha")
        if bruta["eixo"] not in eixos:
            raise ErroBaseConhecimento(f"Pergunta {bruta['id']} usa eixo desconhecido: {bruta['eixo']}")
        perguntas.append(
            Pergunta(
                id=bruta["id"],
                dimensao=bruta["dimensao"],
                eixo=bruta["eixo"],
                texto=bruta["texto"],
                ajuda=bruta.get("ajuda", ""),
                pesos=pesos,
            )
        )

    # Toda trilha precisa ser coberta por pelo menos 8 perguntas.
    for trilha in trilhas.values():
        cobertura = sum(1 for p in perguntas if abs(p.peso_para(trilha.id)) > 0)
        if cobertura < 8:
            raise ErroBaseConhecimento(f"Trilha {trilha.id} é citada em apenas {cobertura} perguntas")

    return tuple(perguntas), etapas, dict(dados["escala"]), dict(dados["autoavaliacao"])


def _montar_regras(
    dados: dict[str, Any], trilhas: dict[str, Trilha], perguntas_por_id: dict[str, Pergunta]
) -> tuple[tuple[RegraCondicional, ...], tuple[RegraCondicional, ...]]:
    def converter(brutas: Iterable[dict[str, Any]], rotulo: str) -> tuple[RegraCondicional, ...]:
        regras: list[RegraCondicional] = []
        for bruta in brutas:
            if bruta["trilha"] not in trilhas:
                raise ErroBaseConhecimento(f"{rotulo} {bruta['id']} aponta para trilha inexistente")
            for pergunta_id, condicao in bruta["quando"].items():
                if pergunta_id not in perguntas_por_id:
                    raise ErroBaseConhecimento(f"{rotulo} {bruta['id']} usa pergunta inexistente: {pergunta_id}")
                chaves = set(condicao) - {"min", "max", "entre"}
                if chaves:
                    raise ErroBaseConhecimento(f"{rotulo} {bruta['id']} tem condição inválida: {sorted(chaves)}")
            if not 0 < float(bruta["fator"]) <= 1.5:
                raise ErroBaseConhecimento(f"{rotulo} {bruta['id']} tem fator fora da faixa (0, 1.5]")
            regras.append(
                RegraCondicional(
                    id=bruta["id"],
                    trilha=bruta["trilha"],
                    quando={pid: {k: float(v) for k, v in cond.items()} for pid, cond in bruta["quando"].items()},
                    fator=float(bruta["fator"]),
                    justificativa=bruta["justificativa"],
                )
            )
        return tuple(regras)

    return converter(dados["penalidades"], "Penalidade"), converter(dados["bonus"], "Bônus")


def _montar_recursos(dados: dict[str, Any]) -> dict[str, Recurso]:
    recursos: dict[str, Recurso] = {}
    for identificador, bruto in dados["competencias"].items():
        recursos[identificador] = Recurso(
            nome=bruto["nome"],
            categoria=bruto["categoria"],
            horas_base=int(bruto["horas_base"]),
            recursos=tuple(dict(r) for r in bruto["recursos"]),
            pratica=bruto["pratica"],
            prerequisitos=tuple(bruto.get("prerequisitos", ())),
        )
    return recursos


def carregar_base(pasta_dados: str | Path | None = None) -> BaseConhecimento:
    """Lê e valida os quatro arquivos JSON da base de conhecimento."""
    pasta = Path(pasta_dados) if pasta_dados else PASTA_DADOS_PADRAO
    trilhas_json = _ler_json(pasta / "trilhas.json")
    perguntas_json = _ler_json(pasta / "perguntas.json")
    regras_json = _ler_json(pasta / "regras.json")
    recursos_json = _ler_json(pasta / "recursos.json")

    trilhas, eixos, eixos_nomes, dimensoes = _montar_trilhas(trilhas_json)
    perguntas, etapas, escala, autoavaliacao = _montar_perguntas(perguntas_json, trilhas, eixos)
    perguntas_por_id = {p.id: p for p in perguntas}
    penalidades, bonus = _montar_regras(regras_json, trilhas, perguntas_por_id)
    recursos = _montar_recursos(recursos_json)

    ajustes_objetivo = {obj: {t: float(v) for t, v in valores.items()} for obj, valores in regras_json["ajustes_objetivo"].items()}
    ajustes_modalidade = {mod: {t: float(v) for t, v in valores.items()} for mod, valores in regras_json["ajustes_modalidade"].items()}
    for nome, tabela in (("ajustes_objetivo", ajustes_objetivo), ("ajustes_modalidade", ajustes_modalidade)):
        for chave, valores in tabela.items():
            desconhecidas = set(valores) - set(trilhas)
            if desconhecidas:
                raise ErroBaseConhecimento(f"{nome}[{chave}] cita trilhas inexistentes: {sorted(desconhecidas)}")

    # Toda competência de toda trilha precisa ter recurso de estudo.
    for trilha in trilhas.values():
        for competencia in trilha.competencias:
            if competencia.id not in recursos:
                raise ErroBaseConhecimento(
                    f"Competência sem recurso de estudo: {competencia.id} (trilha {trilha.id})"
                )

    return BaseConhecimento(
        trilhas=trilhas,
        eixos=eixos,
        eixos_nomes=eixos_nomes,
        dimensoes=dimensoes,
        perguntas=perguntas,
        etapas=etapas,
        escala=escala,
        autoavaliacao=autoavaliacao,
        penalidades=penalidades,
        bonus=bonus,
        ajustes_objetivo=ajustes_objetivo,
        ajustes_modalidade=ajustes_modalidade,
        niveis=dict(regras_json["niveis"]),
        mensagens=dict(regras_json["mensagens"]),
        calibracao=dict(regras_json["calibracao"]),
        recursos=recursos,
        _perguntas_por_id=perguntas_por_id,
    )


@lru_cache(maxsize=1)
def base_padrao() -> BaseConhecimento:
    """Base carregada uma única vez por processo."""
    return carregar_base()
