# Resultados de validação

Saída de `python tools/benchmark.py`. Cada linha é um perfil de `exemplos/` executado pelo motor completo (ranking + lacunas + roadmap).

| Perfil | 1º lugar | % | 2º lugar | % | Margem | Confiança | Empate | Estabilidade | Lacunas | Horas | Semanas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `perfil_analitico.json` | Ciência de Dados e Machine Learning | 86,1% | Desenvolvimento Back-end | 79,6% | 6,5 | média (0,62) | não | 100% | 2 | 84h | 8 |
| `perfil_backend.json` | Desenvolvimento Back-end | 83,9% | Engenharia de Qualidade e Testes (QA) | 70,9% | 13,0 | alta (0,83) | não | 100% | 2 | 64h | 6 |
| `perfil_conflitante.json` | Ciência de Dados e Machine Learning | 75,9% | Cibersegurança | 75,8% | 0,1 | baixa (0,40) | sim | 46% | 7 | 262h | 26 |
| `perfil_devops.json` | DevOps & SRE | 91,5% | Arquitetura em Nuvem | 88,5% | 3,0 | média (0,50) | não | 100% | 9 | 151h | 13 |
| `perfil_frontend.json` | Desenvolvimento Front-end & UI/UX | 89,1% | Desenvolvimento Mobile | 81,7% | 7,4 | alta (0,65) | não | 100% | 5 | 127h | 12 |
| `perfil_neutro.json` | Engenharia de Qualidade e Testes (QA) | 61,4% | Desenvolvimento Back-end | 60,7% | 0,7 | baixa (0,02) | sim | 35% | 9 | 220h | 23 |
| `perfil_produto.json` | Gestão de Produtos | 91,8% | Desenvolvimento Front-end & UI/UX | 59,2% | 32,6 | alta (1,00) | não | 100% | 5 | 98h | 12 |
| `perfil_seguranca.json` | Cibersegurança | 84,6% | DevOps & SRE | 76,1% | 8,5 | alta (0,68) | não | 100% | 5 | 116h | 6 |

> Perfis `perfil_neutro.json` e `perfil_conflitante.json` são casos-limite: o primeiro responde 3 em todas as perguntas (empate por ausência de evidência) e o segundo combina afinidades contraditórias (design + infraestrutura + matemática em nível máximo).
