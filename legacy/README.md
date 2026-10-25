# Versão anterior (Aula 08) — motor com regras binárias no Experta

Este diretório guarda a primeira entrega do projeto, mantida como registro da evolução do modelo:

| Arquivo | Conteúdo |
|---|---|
| `sistema_especialista_experta.py` | 38 regras SE–ENTÃO, 10 carreiras e cálculo por soma de pontos inteiros |
| `test_personas_experta.py` | Testes das personas originais (executados apenas se o Experta estiver instalado) |
| `matriz_de_decisao.md` | Matriz de decisão da versão anterior |
| `requirements-experta.txt` | Dependências da versão anterior |

## Por que foi substituída

- A base de regras ficava dentro do Python, contrariando o requisito de desacoplamento do conhecimento.
- As respostas eram binárias (uma opção por pergunta), sem intensidade nem tratamento de incerteza.
- O resultado era uma única carreira com pontuação inteira, sem percentual, lacunas ou plano de ação.

A versão atual (`src/consultor/`) mantém o mesmo domínio de 10 trilhas, mas com motor ponderado, base JSON
e roadmap personalizado. Consulte o [relatório técnico](../docs/relatorio-tecnico.md) para a comparação completa.

## Como executar os testes antigos

```powershell
python -m pip install -r legacy\requirements-experta.txt
python -m pytest legacy -q
```
