"""Análise de lacunas (skill gap) entre o perfil atual e o nível alvo."""

from __future__ import annotations

from dataclasses import dataclass

from .base_conhecimento import BaseConhecimento, Trilha

NIVEIS_VALIDOS = (0, 1, 2, 3)


@dataclass(frozen=True)
class Lacuna:
    competencia_id: str
    nome: str
    essencial: bool
    peso: float
    nivel_atual: int
    nivel_necessario: int
    lacuna: int
    prioridade: float
    horas_estimadas: int
    classificacao: str
    pratica: str

    def para_dict(self) -> dict[str, object]:
        return {
            "competencia_id": self.competencia_id,
            "nome": self.nome,
            "essencial": self.essencial,
            "nivel_atual": self.nivel_atual,
            "nivel_necessario": self.nivel_necessario,
            "lacuna": self.lacuna,
            "prioridade": round(self.prioridade, 3),
            "horas_estimadas": self.horas_estimadas,
            "classificacao": self.classificacao,
        }


@dataclass(frozen=True)
class AnaliseLacunas:
    trilha_id: str
    trilha_nome: str
    nivel_alvo: str
    cobertura: float
    lacunas: tuple[Lacuna, ...]
    cobertas: tuple[Lacuna, ...]
    horas_totais: int

    @property
    def criticas(self) -> tuple[Lacuna, ...]:
        return tuple(lacuna for lacuna in self.lacunas if lacuna.classificacao == "crítica")

    @property
    def essenciais_pendentes(self) -> tuple[Lacuna, ...]:
        return tuple(lacuna for lacuna in self.lacunas if lacuna.essencial)

    @property
    def pronto(self) -> bool:
        return not self.lacunas

    def para_dict(self) -> dict[str, object]:
        return {
            "trilha": self.trilha_id,
            "nivel_alvo": self.nivel_alvo,
            "cobertura": round(self.cobertura, 1),
            "horas_totais": self.horas_totais,
            "lacunas": [lacuna.para_dict() for lacuna in self.lacunas],
            "cobertas": [lacuna.para_dict() for lacuna in self.cobertas],
        }


def _normalizar_nivel(valor: object) -> int:
    try:
        nivel = int(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    if nivel not in NIVEIS_VALIDOS:
        raise ValueError(f"Nível de conhecimento inválido: {valor!r} (use 0 a 3)")
    return nivel


def _classificar(essencial: bool, lacuna: int, prioridade: float) -> str:
    if lacuna <= 0:
        return "ok"
    if essencial:
        return "crítica" if lacuna >= 2 else "alta"
    if lacuna >= 2:
        return "alta"
    return "média"


def analisar_lacunas(
    base: BaseConhecimento,
    trilha_id: str,
    conhecimentos: dict[str, object],
    nivel_alvo: str = "junior",
) -> AnaliseLacunas:
    """Compara o conhecimento declarado com o exigido para o nível alvo."""
    trilha: Trilha = base.trilha(trilha_id)
    if nivel_alvo not in base.niveis:
        raise ValueError(f"Nível alvo desconhecido: {nivel_alvo}")

    lacunas: list[Lacuna] = []
    cobertas: list[Lacuna] = []
    soma_necessaria = 0.0
    soma_coberta = 0.0
    horas_totais = 0

    for competencia in trilha.competencias:
        nivel_atual = _normalizar_nivel(conhecimentos.get(competencia.id, 0))
        nivel_necessario = competencia.nivel_necessario(nivel_alvo)
        recurso = base.recurso(competencia.id)
        horas_base = recurso.horas_base if recurso else 20
        pratica = recurso.pratica if recurso else ""

        peso = competencia.peso
        if nivel_necessario > 0:
            soma_necessaria += peso * nivel_necessario
            soma_coberta += peso * min(nivel_atual, nivel_necessario)

        lacuna = max(0, nivel_necessario - nivel_atual)
        prioridade = (lacuna / 3.0) * peso * (1.25 if competencia.essencial else 1.0)
        horas = int(round(horas_base * (lacuna / max(nivel_necessario, 1)))) if lacuna else 0
        horas_totais += horas
        item = Lacuna(
            competencia_id=competencia.id,
            nome=recurso.nome if recurso else competencia.id,
            essencial=competencia.essencial,
            peso=peso,
            nivel_atual=nivel_atual,
            nivel_necessario=nivel_necessario,
            lacuna=lacuna,
            prioridade=prioridade,
            horas_estimadas=horas,
            classificacao=_classificar(competencia.essencial, lacuna, prioridade),
            pratica=pratica,
        )
        if lacuna > 0:
            lacunas.append(item)
        elif nivel_necessario > 0:
            cobertas.append(item)

    lacunas.sort(key=lambda lacuna: (-lacuna.prioridade, -int(lacuna.essencial), lacuna.nome))
    cobertas.sort(key=lambda lacuna: (-lacuna.peso, lacuna.nome))
    cobertura = 100 * (soma_coberta / soma_necessaria) if soma_necessaria else 100.0
    return AnaliseLacunas(
        trilha_id=trilha.id,
        trilha_nome=trilha.nome,
        nivel_alvo=nivel_alvo,
        cobertura=round(min(cobertura, 100.0), 1),
        lacunas=tuple(lacunas),
        cobertas=tuple(cobertas),
        horas_totais=horas_totais,
    )


def compatibilidade_por_competencia(
    base: BaseConhecimento, trilha_id: str, conhecimentos: dict[str, object], nivel_alvo: str = "junior"
) -> dict[str, object]:
    """Resumo usado pela interface: cobertura, pendências e pontos fortes."""
    analise = analisar_lacunas(base, trilha_id, conhecimentos, nivel_alvo)
    return {
        "cobertura": analise.cobertura,
        "total_lacunas": len(analise.lacunas),
        "criticas": len(analise.criticas),
        "pronto": analise.pronto,
        "horas_totais": analise.horas_totais,
    }
