# Matriz de pesos — perguntas × trilhas

Gerada automaticamente a partir de `data/perguntas.json` por `python tools/exportar_matriz.py`. Cada célula indica o peso da pergunta na trilha: valores positivos aproximam o perfil da trilha; valores negativos afastam. O traço (—) indica que a pergunta não pontua naquela trilha.

## Perguntas de afinidade

| # | Pergunta | Dimensão | Back | Front | Dados | EngDados | Seg | DevOps | Cloud | Mobile | QA | Prod |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Resolver problemas de lógica, depurar erros e insistir até a solução aparecer me dá satisfação. | Raciocínio lógico e depuração | 0,95 | 0,45 | 0,55 | 0,50 | 0,50 | 0,45 | 0,35 | 0,50 | 0,65 | 0,15 |
| 2 | Tenho boa afinidade com matemática, estatística e raciocínio quantitativo. | Matemática e estatística | 0,20 | -0,20 | 1,00 | 0,30 | 0,25 | 0,05 | 0,05 | — | 0,10 | — |
| 3 | Gosto de escrever código e ver uma funcionalidade funcionando do início ao fim. | Escrita de código | 1,00 | 0,85 | 0,55 | 0,55 | 0,30 | 0,50 | 0,25 | 0,85 | 0,45 | -0,25 |
| 4 | Tenho curiosidade sobre como APIs, bancos, filas e caches se integram em um sistema em produção. | Arquitetura e integração de sistemas | 0,72 | 0,18 | 0,18 | 0,36 | 0,45 | 0,54 | 0,45 | 0,23 | 0,27 | — |
| 5 | Sinto prazer em escolher cores, tipografia e organizar telas de forma agradável. | Design visual | — | 1,00 | 0,10 | -0,10 | -0,25 | -0,20 | -0,25 | 0,45 | 0,05 | 0,25 |
| 6 | Costumo perceber problemas de usabilidade e fico pensando em como melhorar a experiência da pessoa. | Experiência do usuário | — | 0,95 | — | — | -0,10 | -0,10 | -0,10 | 0,40 | 0,20 | 0,55 |
| 7 | Gosto de explorar bases de dados, montar gráficos e tirar conclusões a partir de números. | Análise de dados | 0,25 | 0,10 | 1,00 | 0,80 | 0,25 | 0,15 | 0,10 | — | 0,15 | 0,35 |
| 8 | Me atrai construir processos que coletam, limpam e organizam dados automaticamente. | Pipelines e engenharia de dados | 0,20 | — | 0,35 | 1,00 | 0,05 | 0,15 | 0,10 | -0,10 | — | -0,05 |
| 9 | Tenho paciência para configurar servidores, redes, containers e ambientes de desenvolvimento. | Infraestrutura e operação | 0,30 | -0,15 | 0,10 | 0,45 | 0,70 | 1,00 | 0,85 | -0,10 | 0,20 | -0,25 |
| 10 | Prefiro investir tempo automatizando uma tarefa a repeti-la manualmente todos os dias. | Automação | 0,14 | — | 0,09 | 0,49 | 0,27 | 0,90 | 0,41 | — | 0,41 | — |
| 11 | Me interesso por vulnerabilidades, ataques reais e mecanismos de defesa. | Segurança | 0,15 | -0,05 | 0,05 | 0,15 | 1,00 | 0,30 | 0,30 | — | 0,15 | -0,05 |
| 12 | Gosto de testar cenários, encontrar defeitos e garantir que nada quebre em produção. | Qualidade e testes | 0,30 | 0,30 | 0,10 | 0,35 | 0,20 | 0,25 | 0,15 | 0,30 | 1,00 | — |
| 13 | Me interessa decidir o que será construído, equilibrando negócio, usuários e esforço técnico. | Produto e negócio | — | 0,15 | 0,10 | — | — | -0,05 | 0,15 | 0,10 | 0,10 | 1,00 |
| 14 | Me sinto confortável apresentando ideias, negociando prazos e alinhando com outras áreas. | Comunicação e liderança | 0,05 | 0,30 | 0,05 | 0,05 | 0,15 | 0,10 | 0,20 | 0,10 | 0,25 | 0,90 |
| 15 | Tenho interesse específico em aplicativos de celular e nas restrições dessas plataformas. | Desenvolvimento mobile | — | 0,27 | -0,14 | -0,18 | — | -0,14 | -0,14 | 0,90 | — | — |
| 16 | Me interessa desenhar arquiteturas escaláveis e escolher serviços de nuvem. | Computação em nuvem | 0,09 | — | 0,09 | 0,32 | 0,23 | 0,49 | 0,90 | — | — | — |
| 17 | Não me incomodo em ter responsabilidade por sistemas críticos, com plantões e incidentes. | Operação crítica e plantão | — | -0,08 | — | 0,08 | 0,32 | 0,36 | 0,20 | — | — | -0,12 |

## Perfil de dimensões por trilha

| Dimensão | Back | Front | Dados | EngDados | Seg | DevOps | Cloud | Mobile | QA | Prod |
|---|---|---|---|---|---|---|---|---|---|---|
| Raciocínio lógico e depuração | 0,95 | 0,45 | 0,55 | 0,50 | 0,50 | 0,45 | 0,35 | 0,50 | 0,65 | 0,15 |
| Matemática e estatística | 0,20 | -0,20 | 1,00 | 0,30 | 0,25 | 0,05 | 0,05 | — | 0,10 | — |
| Escrita de código | 1,00 | 0,85 | 0,55 | 0,55 | 0,30 | 0,50 | 0,25 | 0,85 | 0,45 | -0,25 |
| Arquitetura e integração de sistemas | 0,80 | 0,20 | 0,20 | 0,40 | 0,50 | 0,60 | 0,50 | 0,25 | 0,30 | 0,05 |
| Design visual | — | 1,00 | 0,10 | -0,10 | -0,25 | -0,20 | -0,25 | 0,45 | 0,05 | 0,25 |
| Experiência do usuário | — | 0,95 | — | — | -0,10 | -0,10 | -0,10 | 0,40 | 0,20 | 0,55 |
| Análise de dados | 0,25 | 0,10 | 1,00 | 0,80 | 0,25 | 0,15 | 0,10 | — | 0,15 | 0,35 |
| Pipelines e engenharia de dados | 0,20 | — | 0,35 | 1,00 | 0,05 | 0,15 | 0,10 | -0,10 | — | -0,05 |
| Infraestrutura e operação | 0,30 | -0,15 | 0,10 | 0,45 | 0,70 | 1,00 | 0,85 | -0,10 | 0,20 | -0,25 |
| Automação | 0,15 | 0,05 | 0,10 | 0,55 | 0,30 | 1,00 | 0,45 | 0,05 | 0,45 | -0,05 |
| Segurança | 0,15 | -0,05 | 0,05 | 0,15 | 1,00 | 0,30 | 0,30 | — | 0,15 | -0,05 |
| Qualidade e testes | 0,30 | 0,30 | 0,10 | 0,35 | 0,20 | 0,25 | 0,15 | 0,30 | 1,00 | — |
| Produto e negócio | — | 0,15 | 0,10 | — | — | -0,05 | 0,15 | 0,10 | 0,10 | 1,00 |
| Comunicação e liderança | 0,05 | 0,30 | 0,05 | 0,05 | 0,15 | 0,10 | 0,20 | 0,10 | 0,25 | 0,90 |
| Desenvolvimento mobile | — | 0,30 | -0,15 | -0,20 | -0,05 | -0,15 | -0,15 | 1,00 | — | 0,05 |
| Computação em nuvem | 0,10 | — | 0,10 | 0,35 | 0,25 | 0,55 | 1,00 | — | 0,05 | — |
| Operação crítica e plantão | 0,05 | -0,10 | -0,05 | 0,10 | 0,40 | 0,45 | 0,25 | -0,05 | 0,05 | -0,15 |

## Estatísticas de cobertura

| Trilha | Perguntas com peso | Peso positivo total | Peso negativo total |
|---|---|---|---|
| Desenvolvimento Back-end | 12 | 4,34 | — |
| Desenvolvimento Front-end & UI/UX | 14 | 4,55 | -0,48 |
| Ciência de Dados e Machine Learning | 15 | 4,31 | -0,14 |
| Engenharia de Dados | 15 | 5,40 | -0,28 |
| Cibersegurança | 15 | 4,67 | -0,35 |
| DevOps & SRE | 17 | 5,25 | -0,49 |
| Arquitetura em Nuvem | 17 | 4,46 | -0,48 |
| Desenvolvimento Mobile | 11 | 3,83 | -0,20 |
| Engenharia de Qualidade e Testes (QA) | 13 | 3,98 | — |
| Gestão de Produtos | 11 | 3,20 | -0,72 |
