# Consultor Inteligente de Carreiras em TI

Projeto acadêmico da disciplina Inteligência Artificial — UNIPAC Barbacena.

## Objetivo

Criar um sistema especialista baseado em regras que entrevista o usuário e recomenda uma entre dez trilhas de carreira em TI, apresentando justificativas para a decisão.

## Tecnologias

- Python 3.10 (recomendado para compatibilidade com a biblioteca Experta)
- Experta: fatos, motor de inferência e regras `@Rule`
- Streamlit: interface web
- Git/GitHub: controle de versão e publicação do projeto

## Arquivos

- `app.py`: interface web.
- `sistema_especialista.py`: fatos, regras e motor de inferência.
- `requirements.txt`: dependências.
- `tests/test_personas.py`: testes com quatro perfis.
- `matriz_de_decisao.md`: resumo de como as respostas se relacionam às carreiras.

## Instalação no Windows

1. Instale o Python 3.10 e marque a opção **Add Python to PATH** durante a instalação.
2. Extraia a pasta do projeto.
3. Abra o terminal dentro da pasta do projeto.
4. Crie e ative um ambiente virtual:

```bash
py -3.10 -m venv .venv
.venv\Scripts\activate
```

5. Instale as dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. Inicie a interface:

```bash
streamlit run app.py
```

O Streamlit abrirá a aplicação no navegador. Se não abrir automaticamente, copie o endereço local que aparecer no terminal (normalmente `http://localhost:8501`).

## Testes com personas

Com as dependências instaladas, execute:

```bash
python -m unittest discover -s tests -v
```

Os testes conferem quatro perfis representativos. Caso o ambiente apresente erro ao instalar a biblioteca Experta, confirme que está usando Python 3.10 e que instalou os pacotes pelo `requirements.txt`.

## Publicar no GitHub

1. Crie um repositório novo no GitHub, por exemplo `consultor-carreiras-ti`.
2. Não é necessário adicionar um README pelo site, porque o projeto já contém um.
3. No terminal, dentro da pasta do projeto, execute:

```bash
git init
git add .
git commit -m "Implementa consultor inteligente de carreiras em TI"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/consultor-carreiras-ti.git
git push -u origin main
```

Substitua `SEU-USUARIO` pelo seu nome de usuário do GitHub e use a URL real do repositório que você criou.

## Observação

As regras representam uma matriz inicial de decisão construída para fins didáticos. As sugestões ajudam a explorar possibilidades, mas não substituem pesquisa, experiência prática ou orientação profissional.
