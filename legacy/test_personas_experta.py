"""Testes da versão anterior (motor Experta, Aula 08).

Mantidos como registro da fase de regras binárias. São ignorados quando a
biblioteca Experta não está instalada, para não afetar a suíte atual.

Para executar:
    python -m pip install -r legacy/requirements-experta.txt
    python -m pytest legacy -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

experta = pytest.importorskip("experta", reason="Experta não instalada (versão legada)")

from sistema_especialista_experta import OPCOES, diagnosticar  # noqa: E402


def perfil(atividade, ferramenta, entrega, ambiente, matematica="Média"):
    return {
        "matematica": matematica,
        "atividade": OPCOES["atividade"][atividade],
        "ferramenta": OPCOES["ferramenta"][ferramenta],
        "entrega": OPCOES["entrega"][entrega],
        "ambiente": OPCOES["ambiente"][ambiente],
    }


class TestePersonas(unittest.TestCase):
    def test_perfil_analitico(self):
        resultado = diagnosticar(perfil(
            "Analisar dados e encontrar padrões",
            "Python",
            "Informações e análises que ajudam a decidir",
            "Dados e pesquisa",
            "Alta",
        ))
        self.assertEqual(resultado["carreira"], "Ciência de Dados e Machine Learning")

    def test_perfil_seguranca(self):
        resultado = diagnosticar(perfil(
            "Investigar falhas, riscos e vulnerabilidades",
            "Linux e redes",
            "Sistemas protegidos contra ameaças",
            "Segurança e investigação",
        ))
        self.assertEqual(resultado["carreira"], "Cibersegurança")

    def test_perfil_visual(self):
        resultado = diagnosticar(perfil(
            "Criar interfaces e melhorar a experiência visual",
            "JavaScript",
            "Um produto ou interface que a pessoa usa",
            "Desenvolvimento de software",
            "Baixa",
        ))
        self.assertEqual(resultado["carreira"], "Desenvolvimento Front-end & UI/UX")

    def test_perfil_negocios(self):
        resultado = diagnosticar(perfil(
            "Planejar produtos e entender necessidades de usuários",
            "Ferramentas de design e prototipação",
            "Direção e prioridades de um produto",
            "Negócios, usuários e planejamento",
        ))
        self.assertEqual(resultado["carreira"], "Gestão de Produtos")

    def test_perfil_nuvem_regra_cruzada(self):
        resultado = diagnosticar(perfil(
            "Configurar servidores, redes e infraestrutura",
            "Ferramentas de nuvem",
            "Infraestrutura estável e automatizada",
            "Infraestrutura, servidores ou nuvem",
        ))
        self.assertEqual(resultado["carreira"], "Computação em Nuvem")
        self.assertEqual(resultado["pontuacao"], 11)

    def test_perfil_backend(self):
        resultado = diagnosticar(perfil(
            "Programar regras, lógica e funcionalidades",
            "Python",
            "A lógica e os serviços por trás do sistema",
            "Desenvolvimento de software",
        ))
        self.assertEqual(resultado["carreira"], "Desenvolvimento Back-end")

    def test_perfil_engenharia_dados(self):
        resultado = diagnosticar(perfil(
            "Organizar fluxos e preparar dados para uso",
            "SQL e ferramentas de dados",
            "Dados organizados e disponíveis",
            "Dados e pesquisa",
        ))
        self.assertEqual(resultado["carreira"], "Engenharia de Dados")

    def test_perfil_devops(self):
        resultado = diagnosticar(perfil(
            "Automatizar tarefas e manter sistemas funcionando",
            "Git, automação e integração contínua",
            "Infraestrutura estável e automatizada",
            "Infraestrutura, servidores ou nuvem",
        ))
        self.assertEqual(resultado["carreira"], "DevOps & SRE")

    def test_perfil_mobile(self):
        resultado = diagnosticar(perfil(
            "Criar aplicativos para celulares",
            "JavaScript",
            "Aplicativo para celular",
            "Desenvolvimento de software",
        ))
        self.assertEqual(resultado["carreira"], "Desenvolvimento Mobile")

    def test_perfil_qa(self):
        resultado = diagnosticar(perfil(
            "Testar programas e encontrar defeitos",
            "Ferramentas de teste",
            "Software confiável e sem defeitos",
            "Testes e melhoria contínua",
        ))
        self.assertEqual(resultado["carreira"], "Engenharia de Qualidade e Testes (QA)")


if __name__ == "__main__":
    unittest.main()
