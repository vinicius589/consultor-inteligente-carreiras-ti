"""Executa o motor e o gerador de plano para um perfil completo."""

from __future__ import annotations

from typing import Any

from .base_conhecimento import BaseConhecimento, base_padrao
from .motor import Resultado, avaliar
from .roadmap import PlanoAcao, gerar_plano


def executar(
    perfil: dict[str, Any],
    base: BaseConhecimento | None = None,
    com_sensibilidade: bool = True,
) -> tuple[Resultado, PlanoAcao]:
    """Roda o ranking e monta o plano de ação de um perfil já carregado.

    ``perfil`` segue o formato dos arquivos em ``exemplos/``: ``respostas`` é
    obrigatório; ``conhecimentos``, ``objetivo``, ``modalidade``, ``nivel_alvo``,
    ``horas_semana`` e ``prazo_meses`` são opcionais.
    """
    base = base or base_padrao()
    respostas = perfil.get("respostas") or {}
    nivel_alvo = perfil.get("nivel_alvo", "junior")
    resultado = avaliar(
        base,
        respostas,
        objetivo=perfil.get("objetivo"),
        modalidade=perfil.get("modalidade"),
        nivel_alvo=nivel_alvo,
        com_sensibilidade=com_sensibilidade,
    )
    plano = gerar_plano(
        base,
        resultado.top.id,
        perfil.get("conhecimentos") or {},
        nivel_alvo=nivel_alvo,
        horas_semana=int(perfil.get("horas_semana") or 10),
        prazo_meses=int(perfil.get("prazo_meses") or 6),
        objetivo=perfil.get("objetivo"),
    )
    return resultado, plano
