# Consultor Inteligente de Carreiras em TI

Projeto acadêmico da disciplina de Inteligência Artificial da UNIPAC Barbacena, desenvolvido em Python com as bibliotecas Experta e Streamlit.

## Objetivo

Desenvolver um sistema especialista baseado em regras lógicas que analisa as respostas do usuário e recomenda uma trilha de carreira na área de Tecnologia da Informação, apresentando justificativas para a recomendação.

## Trilhas de carreira

O sistema considera dez áreas profissionais:

1. Desenvolvimento Back-end
2. Desenvolvimento Front-end e UI/UX
3. Ciência de Dados e Machine Learning
4. Engenharia de Dados
5. Cibersegurança
6. DevOps e SRE
7. Computação em Nuvem
8. Desenvolvimento Mobile
9. Engenharia de Qualidade e Testes (QA)
10. Gestão de Produtos

## Como funciona

A interface apresenta cinco perguntas relacionadas a:

- Afinidade com matemática e estatística.
- Atividades de maior interesse.
- Linguagens de programação e ferramentas.
- Tipo de resultado que o usuário prefere entregar.
- Ambiente de trabalho de maior interesse.

As respostas são analisadas por regras lógicas implementadas com a biblioteca Experta. Cada regra ativada pode acrescentar pontos a uma carreira e registrar uma justificativa.

O projeto possui 38 regras, incluindo 20 regras cruzadas que combinam duas ou mais características do perfil.

Ao final da análise, o sistema apresenta a trilha recomendada, sua descrição, os motivos da recomendação, a pontuação e outras opções consideradas.

## Tecnologias utilizadas

- **Python:** linguagem de programação utilizada no projeto.
- **Experta:** biblioteca utilizada para implementar fatos, regras e o motor de inferência.
- **Streamlit:** biblioteca utilizada para criar a interface web.
- **Unittest:** ferramenta utilizada nos testes automatizados.
- **Git e GitHub:** controle de versão e armazenamento do código-fonte.

## Estrutura do projeto

- `app.py`: interface da aplicação.
- `sistema_especialista.py`: fatos, regras e motor de inferência.
- `matriz_de_decisao.md`: resumo dos critérios de decisão.
- `tests/test_personas.py`: testes automatizados dos perfis.
- `requirements.txt`: dependências necessárias para executar o projeto.
- `.gitignore`: arquivos e pastas que não devem ser versionados.

## Como executar no Windows

### 1. Requisitos

Tenha o Python instalado. A versão 3.10 é recomendada para favorecer a compatibilidade com a biblioteca Experta.

O Git também é necessário para clonar o repositório.

### 2. Baixar o projeto

Abra o PowerShell e execute:

```powershell
git clone https://github.com/vinicius589/consultor-inteligente-carreiras-ti.git
cd consultor-inteligente-carreiras-ti
```

### 3. Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar as dependências

Com o ambiente virtual ativado, execute:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Iniciar a aplicação

Execute:

```powershell
python -m streamlit run app.py
```

A aplicação poderá ser acessada pelo endereço local exibido no terminal, normalmente:

http://localhost:8501

Para encerrar a aplicação, pressione `Ctrl + C` no terminal em que ela está rodando.

## Testes automatizados

O projeto possui dez testes automatizados que verificam se diferentes perfis recebem as recomendações esperadas, abrangendo as dez trilhas de carreira.

Para executar os testes, utilize:

```powershell
python -m unittest discover -s tests -v
```

Quando todas as verificações passam, o resultado final apresenta `OK`.

## Matriz de decisão

O arquivo `matriz_de_decisao.md` apresenta um resumo das relações entre as atividades, ferramentas e resultados valorizados em cada trilha profissional.

A pontuação é calculada pelas regras cadastradas no motor de inferência. A recomendação é uma orientação inicial baseada nas respostas fornecidas pelo usuário.

## Repositório no GitHub

O código-fonte está disponível em:

https://github.com/vinicius589/consultor-inteligente-carreiras-ti

## Observação

Este projeto tem finalidade acadêmica. As recomendações ajudam o usuário a explorar possibilidades profissionais na área de Tecnologia da Informação, mas não substituem pesquisa, experiência prática ou orientação profissional.