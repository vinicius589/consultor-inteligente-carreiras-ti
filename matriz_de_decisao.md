# Matriz de decisão — Consultor de Carreiras em TI

A matriz abaixo resume os principais sinais considerados pelo sistema. As regras completas estão no arquivo `sistema_especialista.py`.

| Trilha | Atividade relacionada | Ferramenta/afinidade | Entrega valorizada |
|---|---|---|---|
| Desenvolvimento Back-end | Lógica e funcionalidades | Python | Serviços e regras por trás do sistema |
| Front-end & UI/UX | Interfaces e experiência visual | JavaScript ou design | Produto/interface usado pelo público |
| Ciência de Dados e Machine Learning | Análise de dados | Ferramentas de dados e matemática média/alta | Análises para apoiar decisões |
| Engenharia de Dados | Preparação e organização de dados | SQL/ferramentas de dados | Dados organizados e disponíveis |
| Cibersegurança | Investigar riscos e vulnerabilidades | Linux e redes | Proteção contra ameaças |
| DevOps & SRE | Automação e confiabilidade | Git, automação e integração contínua | Infraestrutura estável e automatizada |
| Computação em Nuvem | Servidores, redes e infraestrutura | Ferramentas de nuvem | Infraestrutura escalável |
| Desenvolvimento Mobile | Aplicativos para celulares | JavaScript pode apoiar multiplataforma | Aplicativo móvel |
| QA/Testes | Testar e encontrar defeitos | Ferramentas de teste | Software confiável |
| Gestão de Produtos | Planejamento e necessidades dos usuários | Design e visão de negócio | Estratégia e prioridades |

## Como a inferência funciona

1. A interface coleta cinco respostas do usuário.
2. As respostas são inseridas como um fato `Perfil`.
3. As regras `@Rule` do Experta verificam combinações de respostas.
4. Cada regra ativada registra uma evidência com carreira, pontuação e justificativa.
5. O sistema soma as evidências, escolhe a trilha com maior pontuação e mostra os principais motivos.

A afinidade matemática é usada especialmente para distinguir um perfil voltado à análise estatística de outros perfis ligados a dados. Engenharia de Dados recebe mais peso quando a preferência é organizar, preparar e disponibilizar dados.
