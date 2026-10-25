# Relatório técnico — Consultor Inteligente de Carreiras em TI (v2)

**Sistema especialista baseado em regras com tratamento de incerteza e pontuação ponderada**

Projeto acadêmico · Inteligência Artificial · Centro Universitário Presidente Antônio Carlos — UNIPAC Barbacena
Versão 2.0 · outubro de 2026

---

## 1. Contextualização e objetivo

A primeira versão do projeto (Aula 08) usava regras SE–ENTÃO binárias: o usuário escolhia uma opção em
cada pergunta e o motor somava pontos inteiros para a carreira correspondente. O resultado era uma única
recomendação, sem percentual, sem noção de intensidade e sem plano de ação.

Esta versão responde à limitação central de sistemas especialistas clássicos: o mundo real raramente é
preto no branco. Um estudante pode gostar *moderadamente* de matemática, ter *muita* afinidade com design e
*nenhuma* com infraestrutura. O sistema agora:

- aceita respostas graduais (escala Likert de 1 a 5) em 17 perguntas de afinidade;
- calcula uma matriz de compatibilidade percentual para as 10 trilhas de tecnologia;
- trata incerteza com fatores de certeza (modelo de MYCIN) e regras de conflito;
- identifica lacunas de competência em relação ao nível alvo (estágio, júnior ou pleno);
- gera um roadmap pessoal com fases, recursos gratuitos, certificações e projetos de portfólio;
- explica cada resultado (evidências, penalidades, bônus e teste de sensibilidade).

Toda a base de conhecimento vive em arquivos JSON — nenhum peso, trilha ou regra está codificado no Python.

### 1.1 O que mudou em relação à versão anterior

| Aspecto | v1 (Aula 08) | v2 (esta versão) |
|---|---|---|
| Entrada | 5 perguntas de múltipla escolha | 3 etapas, 17 perguntas Likert + objetivos + autoavaliação |
| Motor | 38 regras SE–ENTÃO no Experta | motor próprio ponderado + fatores de certeza |
| Base de conhecimento | dentro do `.py` | 4 arquivos JSON validados no carregamento |
| Saída | 1 carreira + lista de motivos | Top 3 com %, ranking das 10, lacunas, roadmap, certificações, portfólio |
| Incerteza | inexistente | CF (MYCIN), penalidades, bônus, sensibilidade ±1 |
| Interface | formulário único | wizard em etapas com gráficos e exportação |

A versão anterior foi preservada em `legacy/`, com os testes originais, documentando a evolução do modelo.

---

## 2. Arquitetura

```
data/*.json  ──►  base_conhecimento.py  ──►  motor.py  ──►  lacunas.py  ──►  roadmap.py
(validação)        (dataclasses + regras)     (ranking)     (skill gap)      (plano)
                                                     │
                                          relatorio.py (Markdown/JSON)
                                                     │
                                        app.py (Streamlit)  ·  main.py (CLI)
```

| Módulo | Responsabilidade |
|---|---|
| `src/consultor/base_conhecimento.py` | Lê os 4 JSON, valida consistência e expõe dataclasses imutáveis |
| `src/consultor/motor.py` | Normalização, soma ponderada, CF, penalidades/bônus, ranking, confiança e sensibilidade |
| `src/consultor/lacunas.py` | Compara conhecimento declarado × exigido por senioridade, prioriza e estima horas |
| `src/consultor/roadmap.py` | Ordena por pré-requisitos, divide em fases, escolhe certificações e projetos |
| `src/consultor/relatorio.py` | Exporta plano em Markdown e resultado em JSON |
| `src/consultor/cli.py` | Execução sem interface (lote, testes, geração de relatórios) |
| `app.py` | Interface Streamlit em três passos + painel de resultados |

O carregamento é **fail-fast**: ids duplicados, pesos apontando para trilhas inexistentes, pergunta com
menos de duas trilhas positivas, competência sem recurso de estudo ou regra citando pergunta inexistente
interrompem a execução com mensagem explícita. Há testes dedicados a cada um desses casos.

---

## 3. Engenharia do conhecimento

### 3.1 Trilhas (10)

Back-end · Front-end & UI/UX · Ciência de Dados e ML · Engenharia de Dados · Cibersegurança · DevOps & SRE ·
Arquitetura em Nuvem · Mobile · QA · Gestão de Produtos.

Cada trilha em `data/trilhas.json` contém: resumo e descrição, 17 pesos de dimensão, 8 eixos para o gráfico
radar, competências (essenciais e complementares, com nível exigido por senioridade), tecnologias em ordem de
estudo, certificações com custo e link, projetos de portfólio com diferencial, sinais de mercado (entrada
júnior, volume de vagas, salário relativo, remoto, transição) e faixa salarial indicativa.

### 3.2 Perguntas e dimensões (17 × 17)

As 17 perguntas cobrem 17 dimensões latentes (lógica, matemática, código, sistemas, visual, usabilidade,
dados, engenharia de dados, infraestrutura, automação, segurança, qualidade, produto, comunicação, mobile,
nuvem e operação crítica). Os pesos por trilha estão em `data/perguntas.json`; a matriz completa, com
estatísticas de cobertura, é gerada por `tools/exportar_matriz.py` em
[`matriz-de-pesos.md`](matriz-de-pesos.md).

Pesos **negativos** modelam incompatibilidades: por exemplo, matemática alta reduz a aderência a Front-end
e a Gestão de Produtos, e codificação reduz a aderência a Produto. Isso evita que o motor recomende uma
trilha apenas porque o perfil é "bom em tudo".

### 3.3 Objetivos, modalidade e conflitos

`data/regras.json` guarda 16 penalidades, 10 bônus, 5 tabelas de ajuste por objetivo, 4 por modalidade de
trabalho, os níveis de senioridade e as mensagens interpretativas.

- **Penalidade** (–): `q_comunicacao ≤ 2` reduz Gestão de Produtos em 38%; `q_infra ≤ 2` reduz DevOps em 34%.
- **Bônus** (+): infraestrutura ≥ 4 *e* automação ≥ 4 elevam DevOps em 8%.
- **Objetivo**: "primeiro emprego" favorece QA e Front-end; "especialização" favorece Dados, Cloud e DevOps.
- **Modalidade**: preferência remota ajusta levemente trilhas com maior oferta remota.

---

## 4. Modelo de incerteza e pontuação

### 4.1 Normalização e força da trilha

Para cada resposta `r_q` na escala 1–5:

```
a_q = (r_q − 1) / 4                        →  a_q ∈ [0, 1]
B_t = Σ_q  w_qt · a_q                      (soma ponderada, w pode ser negativo)
M_t = Σ_{w_qt > 0} w_qt                    (máximo alcançável)
m_t = Σ_{w_qt < 0} w_qt                    (mínimo alcançável)
F_t = (B_t − m_t) / (M_t − m_t)            →  F_t ∈ [0, 1]
```

A normalização dentro da faixa `[m_t, M_t]` compara o perfil com o **melhor e o pior perfil possível
para aquela trilha**, e não com um ideal absoluto. É isso que permite comparar percentuais entre trilhas
com números diferentes de pesos.

### 4.2 Fatores de certeza (MYCIN)

Cada pergunta gera uma evidência escalada pelo maior peso da trilha:

```
e_qt = (w_qt / max|w_t|) · (2·a_q − 1)     →  e_qt ∈ [−1, 1]
```

As evidências são combinadas da mais forte para a mais fraca, na ordem clássica de MYCIN:

```
cf1, cf2 ≥ 0   →   cf1 + cf2·(1 − cf1)
cf1, cf2 < 0   →   cf1 + cf2·(1 + cf1)
sinais opostos →   (cf1 + cf2) / (1 − min(|cf1|, |cf2|))
```

O resultado `CF_t` mede a consistência do perfil em relação à trilha. Ele é usado como **certeza**
(`|CF_t|`) na composição da confiança final, e não como pontuação — a pontuação vem da soma ponderada.
Essa separação evita o problema clássico de CFs que saturam em 1,0 quando há muitas perguntas.

### 4.3 Penalidades, bônus e contexto

```
P_t = Π penalidades aplicadas        (0 < P_t ≤ 1)
K_t = Π bônus aplicados              (1 ≤ K_t ≤ 1,08)
O_t = ajuste de objetivo             (0,96 ≤ O_t ≤ 1,04)
D_t = ajuste de modalidade           (0,975 ≤ D_t ≤ 1,025)
G_t = F_t · P_t · K_t · O_t · D_t
```

Os ajustes de contexto foram deliberadamente suavizados (±4%) para **não distorcer a leitura absoluta**
do percentual: eles desempatam perfis parecidos, mas não transformam um perfil fraco em forte.

### 4.4 Calibração do percentual

```
percentual_t = 100 · τ · G_t^γ          com τ = 0,97 e γ = 0,70
```

- `τ = 0,97`: não existe compatibilidade perfeita; o teto é 97%.
- `γ = 0,70 < 1`: expande a parte alta da escala. Um perfil neutro (todas as respostas 3 → `F = 0,5`)
  resulta em **61%**, enquanto um perfil fortemente alinhado chega a 85–95%. Sem essa curva, um perfil
  neutro apareceria com 50% e um perfil excelente com 75%, comprimindo a informação útil.

Os parâmetros ficam em `data/regras.json` (`calibracao`) e podem ser alterados sem tocar no código.

### 4.5 Ranking, empate e confiança

Ordenação: percentual decrescente → empregabilidade de entrada (mercado) → nome.

```
margem        = p1 − p2
empate        = margem ≤ 2,5 pontos percentuais
confiança     = 0,6 · min(margem / 18, 1) + 0,4 · |CF_top|
níveis        = alta (≥ 0,62) · média (≥ 0,45) · baixa (< 0,45)
```

Quando há empate, o sistema **não força uma escolha**: apresenta as duas trilhas como co-recomendadas,
identifica a pergunta que mais as separa (maior diferença de peso) e sugere um teste prático com a
competência exclusiva da segunda colocada.

### 4.6 Análise de sensibilidade

Cada resposta é perturbada em −1 e +1 (respeitando os limites da escala) e o ranking é recalculado:
são 2 × 17 = 34 simulações por perfil. A **estabilidade** é a proporção de perturbações que mantêm a
primeira colocada. Ela aparece no relatório e explica, por exemplo, por que um perfil com margem de
0,1 ponto percentual é instável (46%) e um perfil de Produto é estável (100%).

---

## 5. Análise de lacunas (skill gap)

Para o nível alvo (estágio, júnior ou pleno), cada competência da trilha tem um nível exigido de 0 a 3:

```
lacuna_t     = max(0, nível_necessário − nível_atual)
prioridade   = (lacuna / 3) · peso · (1,25 se essencial)
horas        = horas_base · lacuna / nível_necessário
cobertura    = Σ peso · min(atual, necessário) / Σ peso · necessário
```

Classificação: **crítica** (essencial com lacuna ≥ 2), **alta** (essencial com lacuna 1, ou complementar
com lacuna ≥ 2), **média** (complementar com lacuna 1). O horário é derivado do esforço-base cadastrado
para cada competência em `data/recursos.json`.

---

## 6. Roadmap personalizado

1. **Ordenação por pré-requisitos** — cada competência declara pré-requisitos (ex.: Kubernetes exige Docker
   e Linux; Machine Learning exige Python e Estatística). O algoritmo escolhe, a cada passo, a maior
   prioridade cujos pré-requisitos que também estão no plano já foram incluídos. Se houver ciclo, a ordem
   por prioridade prevalece — o plano nunca fica incompleto.
2. **Divisão em fases** — busca exaustiva pelos dois pontos de corte que minimizam o desvio em relação a
   1/3 das horas totais por fase. As fases seguem nomes fixos: fundação, profundidade, portfólio.
3. **Fases de projeto** — quando há poucas lacunas, as fases restantes são preenchidas com projeto e
   candidatura, em vez de estudo artificial.
4. **Certificações** — ordenadas por aderência ao nível alvo e por custo, com justificativa do momento.
5. **Portfólio** — cada projeto recebe nota pelo quanto cobre as lacunas priorizadas; escolhe-se o melhor
   projeto para cada fase, sem repetição.
6. **Prazo** — `semanas = Σ horas / horas_semana`; se exceder o prazo declarado, o plano emite alerta e
   recomenda priorizar as lacunas críticas.

---

## 7. Interface

Wizard em três etapas (Streamlit), com barra de progresso e possibilidade de voltar sem perder respostas:

1. **Perfil pessoal** — nome, formação, experiência, horas semanais.
2. **Afinidades técnicas** — 17 perguntas Likert em cartões, com ajuda contextual e contador de respostas.
3. **Objetivos e conhecimentos** — objetivo, nível alvo, prazo, modalidade e autoavaliação 0–3 das
   competências das **três trilhas mais compatíveis** (filtro calculado em tempo real, o que evita pedir
   que o usuário avalie 57 competências).

O painel de resultado tem cinco abas: panorama (ranking em barras + radar perfil × trilha), justificativas,
lacunas, roadmap (com explorador de outra trilha) e exportação (Markdown e JSON).

---

## 8. Validação

**55 testes automatizados** (`pytest`), cobrindo:

| Arquivo | O que verifica |
|---|---|
| `tests/test_base_conhecimento.py` | 10 trilhas, integridade de ids, pesos órfãos, JSON inválido, competência sem recurso |
| `tests/test_motor.py` | normalização, CF, ordenação, determinismo, respostas parciais, 6 personas, sensibilidade |
| `tests/test_lacunas.py` | lacunas por nível, cobertura, ordenação, erros de entrada |
| `tests/test_roadmap.py` | 3 fases, pré-requisitos, certificações, alerta de prazo, consolidação, 10 trilhas |
| `tests/test_casos_limite.py` | perfil neutro, perfil contraditório, extremos, texto numérico, perfil ideal por trilha |
| `tests/test_relatorio.py` | seções do Markdown, links, JSON serializável, empate |
| `tests/test_app.py` | wizard completo pela interface (AppTest) e botão de reinício |

### 8.1 Personas

Saída de `python tools/benchmark.py` (tabela completa em [`resultados-validacao.md`](resultados-validacao.md)):

| Perfil | 1º lugar | % | 2º lugar | % | Margem | Confiança |
|---|---|---|---|---|---|---|
| Analítico (matemática + dados) | Ciência de Dados e ML | 86,1% | Back-end | 79,6% | 6,5 | média |
| Visual (design + interface) | Front-end & UI/UX | 89,1% | Mobile | 81,7% | 7,4 | alta |
| Infraestrutura (Linux + automação) | DevOps & SRE | 91,5% | Arquitetura em Nuvem | 88,5% | 3,0 | média |
| Segurança (redes + defesa) | Cibersegurança | 84,6% | DevOps & SRE | 76,1% | 8,5 | alta |
| Negócios (produto + comunicação) | Gestão de Produtos | 91,8% | Front-end | 59,2% | 32,6 | alta |
| Back-end (lógica + código) | Back-end | 83,9% | QA | 70,9% | 13,0 | alta |

### 8.2 Casos-limite

**Perfil neutro** (todas as respostas 3): todos os percentuais entre 59% e 61%, empate técnico declarado,
confiança 0,02 (baixa) e mensagem explícita de que o resultado é hipótese inicial. Estabilidade 35%.

**Perfil contraditório** (design + infraestrutura + matemática todos em 5): Dados 75,9% × Segurança 75,8%,
margem de 0,1 ponto, empate detectado e desempate sugerido a partir da pergunta de maior diferença de peso.
Estabilidade 46% — o sistema **avisa** que a resposta é instável em vez de esconder a ambiguidade.

**Perfil ideal por trilha**: para cada uma das 10 trilhas, um perfil construído a partir dos próprios pesos
(respostas altas nas dimensões fortes, baixas nas negativas) leva essa trilha ao primeiro lugar. Esse teste
garante que nenhuma trilha é inalcançável pela matriz de pesos.

### 8.3 Propriedades verificadas

- percentuais sempre em [0, 100] e ranking sempre ordenado;
- duas execuções iguais produzem resultado idêntico (determinismo);
- respostas fora da escala e perfis vazios são rejeitados com mensagem clara;
- respostas parciais (só etapa 2) geram ranking com cobertura reduzida, sem erro;
- penalidade de Produto aplicada quando a comunicação é baixa, mantendo a força de afinidade intacta.

---

## 9. Limitações

- Os pesos foram calibrados por julgamento de especialista e validados por personas sintéticas; não houve
  validação estatística com amostra real de estudantes.
- As faixas salariais são estimativas de mercado, não dados oficiais.
- O sistema assume que a autoavaliação de competência é honesta; não há verificação prática.
- A estabilidade ±1 mede robustez local, não substitui um estudo de sensibilidade global dos pesos.
- Trilhas emergentes (IA generativa, plataforma, dados não estruturados) não estão separadas — foram
  absorvidas por Dados, DevOps e Back-end.

## 10. Trabalhos futuros

1. Coleta de respostas reais e calibração dos pesos por regressão logística ou AHP.
2. Teste adaptativo: perguntas escolhidas por ganho de informação (entropia) em vez de questionário fixo.
3. Comparação com um motor bayesiano ingênuo para medir concordância entre os modelos.
4. Integração com APIs de vagas para atualizar os sinais de mercado automaticamente.
5. Exportação em PDF com identidade visual institucional.

---

## 11. Como executar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python -m streamlit run app.py          # interface
python main.py --perfil exemplos\perfil_devops.json --saida plano.md   # CLI
python -m pytest                        # 55 testes
python tools\benchmark.py --saida docs\resultados-validacao.md
python tools\exportar_matriz.py --saida docs\matriz-de-pesos.md
```

Requer Python 3.10+ (testado em 3.13), Streamlit 1.37+, Plotly e Pandas.

---

## 12. Referências

- BUCHANAN, B. G.; SHORTLIFFE, E. H. *Rule-Based Expert Systems: The MYCIN Experiments*. Addison-Wesley, 1984.
- RUSSELL, S.; NORVIG, P. *Inteligência Artificial*. 3. ed. Elsevier, 2013. (cap. sobre sistemas especialistas)
- STREAMLIT. *Streamlit documentation*. Disponível em: https://docs.streamlit.io
- PYTHON SOFTWARE FOUNDATION. *The Python Tutorial*. Disponível em: https://docs.python.org/3/tutorial/
- SCIKIT-LEARN. *Getting started*. Disponível em: https://scikit-learn.org/stable/getting_started.html
