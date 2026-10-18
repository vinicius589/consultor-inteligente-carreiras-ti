"""Motor de inferência do Consultor Inteligente de Carreiras em TI.

O projeto usa Experta para representar fatos e regras SE-ENTÃO.
Cada regra registra evidências que contribuem para a recomendação.
"""

from collections import defaultdict

try:
    # Compatibilidade para ambientes que ainda esperam collections.Mapping.
    import collections
    import collections.abc
    for nome in ("Mapping", "MutableMapping", "Sequence"):
        if not hasattr(collections, nome):
            setattr(collections, nome, getattr(collections.abc, nome))
    from experta import Fact, KnowledgeEngine, Rule, MATCH
except ImportError as erro:
    raise ImportError(
        "Não foi possível importar Experta. Instale as dependências com "
        "'pip install -r requirements.txt'."
    ) from erro


class Perfil(Fact):
    """Respostas informadas pelo usuário."""


class Evidencia(Fact):
    """Evidência produzida por uma regra de inferência."""


CARREIRAS = {
    "Desenvolvimento Back-end": "Construção da lógica de servidores, APIs, regras de negócio e integração com bancos de dados.",
    "Desenvolvimento Front-end & UI/UX": "Criação de interfaces web, layouts responsivos e experiências de uso.",
    "Ciência de Dados e Machine Learning": "Análise estatística, exploração de dados e criação de modelos preditivos.",
    "Engenharia de Dados": "Organização da infraestrutura de dados e construção de processos de coleta e transformação.",
    "Cibersegurança": "Proteção de sistemas, análise de vulnerabilidades e segurança de redes.",
    "DevOps & SRE": "Automação, integração e entrega contínua, monitoramento e confiabilidade de sistemas.",
    "Computação em Nuvem": "Planejamento e administração de infraestrutura escalável em serviços de nuvem.",
    "Desenvolvimento Mobile": "Criação de aplicativos para celulares e outros dispositivos móveis.",
    "Engenharia de Qualidade e Testes (QA)": "Verificação da qualidade de software, testes e prevenção de falhas.",
    "Gestão de Produtos": "Conexão entre necessidades de usuários, negócio, design e desenvolvimento.",
}

# As opções apresentadas na interface são associadas a valores usados pelas regras.
OPCOES = {
    "atividade": {
        "Criar interfaces e melhorar a experiência visual": "interfaces",
        "Programar regras, lógica e funcionalidades": "logica",
        "Analisar dados e encontrar padrões": "dados",
        "Organizar fluxos e preparar dados para uso": "pipeline",
        "Investigar falhas, riscos e vulnerabilidades": "seguranca",
        "Automatizar tarefas e manter sistemas funcionando": "automacao",
        "Configurar servidores, redes e infraestrutura": "infraestrutura",
        "Criar aplicativos para celulares": "mobile",
        "Testar programas e encontrar defeitos": "testes",
        "Planejar produtos e entender necessidades de usuários": "negocio",
    },
    "ferramenta": {
        "Python": "python",
        "JavaScript": "javascript",
        "Linux e redes": "linux",
        "SQL e ferramentas de dados": "dados",
        "Ferramentas de teste": "qa",
        "Git, automação e integração contínua": "devops",
        "Ferramentas de nuvem": "cloud",
        "Ferramentas de design e prototipação": "design",
        "Ainda sou iniciante / nenhuma em especial": "iniciante",
    },
    "entrega": {
        "Um produto ou interface que a pessoa usa": "produto",
        "A lógica e os serviços por trás do sistema": "servico",
        "Informações e análises que ajudam a decidir": "analise",
        "Dados organizados e disponíveis": "dados",
        "Sistemas protegidos contra ameaças": "protecao",
        "Infraestrutura estável e automatizada": "infra",
        "Aplicativo para celular": "app",
        "Software confiável e sem defeitos": "qualidade",
        "Direção e prioridades de um produto": "estrategia",
    },
    "ambiente": {
        "Desenvolvimento de software": "desenvolvimento",
        "Dados e pesquisa": "dados",
        "Segurança e investigação": "seguranca",
        "Infraestrutura, servidores ou nuvem": "infraestrutura",
        "Testes e melhoria contínua": "qualidade",
        "Negócios, usuários e planejamento": "negocio",
    },
}


class ConsultorCarreiras(KnowledgeEngine):
    """Base de conhecimento com regras SE-ENTÃO."""

    def registrar(self, carreira, pontos, motivo):
        self.declare(Evidencia(carreira=carreira, pontos=pontos, motivo=motivo))

    # Back-end: regras 1 a 3
    @Rule(Perfil(atividade="logica"))
    def backend_logica(self):
        self.registrar("Desenvolvimento Back-end", 3, "Você prefere programar lógica e funcionalidades.")

    @Rule(Perfil(entrega="servico"))
    def backend_servicos(self):
        self.registrar("Desenvolvimento Back-end", 2, "Você valoriza a lógica e os serviços por trás do sistema.")

    @Rule(Perfil(ferramenta="python", ambiente="desenvolvimento"))
    def backend_python(self):
        self.registrar("Desenvolvimento Back-end", 1, "Sua afinidade com Python e desenvolvimento combina com essa trilha.")

    # Front-end/UI/UX: regras 4 a 6
    @Rule(Perfil(atividade="interfaces"))
    def frontend_interfaces(self):
        self.registrar("Desenvolvimento Front-end & UI/UX", 3, "Você prefere criar interfaces e cuidar da experiência visual.")

    @Rule(Perfil(ferramenta="javascript", entrega="produto"))
    def frontend_javascript(self):
        self.registrar("Desenvolvimento Front-end & UI/UX", 2, "JavaScript e a entrega de interfaces usadas pelo público combinam com essa área.")

    @Rule(Perfil(ferramenta="design"))
    def frontend_design(self):
        self.registrar("Desenvolvimento Front-end & UI/UX", 2, "Sua afinidade com design e prototipação favorece interfaces e experiência do usuário.")

    # Ciência de Dados e Machine Learning: regras 7 a 9
    @Rule(Perfil(atividade="dados", matematica="Alta"))
    def ciencia_dados_analise(self):
        self.registrar("Ciência de Dados e Machine Learning", 4, "Você gosta de analisar dados e tem alta afinidade com matemática.")

    @Rule(Perfil(entrega="analise"))
    def ciencia_dados_entrega(self):
        self.registrar("Ciência de Dados e Machine Learning", 2, "Você prefere entregar análises que apoiam decisões.")

    @Rule(Perfil(ferramenta="dados", matematica="Média"))
    def ciencia_dados_ferramentas(self):
        self.registrar("Ciência de Dados e Machine Learning", 2, "Sua afinidade com ferramentas de dados e matemática média combina com análise.")

    # Engenharia de Dados: regras 10 a 12
    @Rule(Perfil(atividade="pipeline"))
    def engenharia_dados_pipeline(self):
        self.registrar("Engenharia de Dados", 3, "Você prefere organizar fluxos e preparar dados para uso.")

    @Rule(Perfil(entrega="dados"))
    def engenharia_dados_entrega(self):
        self.registrar("Engenharia de Dados", 3, "Você quer entregar dados organizados e disponíveis.")

    @Rule(Perfil(ferramenta="dados", ambiente="dados"))
    def engenharia_dados_ambiente(self):
        self.registrar("Engenharia de Dados", 2, "Seu interesse por ferramentas e ambientes de dados combina com pipelines.")

    # Cibersegurança: regras 13 a 15
    @Rule(Perfil(atividade="seguranca"))
    def seguranca_investigacao(self):
        self.registrar("Cibersegurança", 3, "Você gosta de investigar falhas, riscos e vulnerabilidades.")

    @Rule(Perfil(entrega="protecao"))
    def seguranca_protecao(self):
        self.registrar("Cibersegurança", 3, "Sua prioridade é proteger sistemas contra ameaças.")

    @Rule(Perfil(ferramenta="linux", ambiente="seguranca"))
    def seguranca_linux(self):
        self.registrar("Cibersegurança", 2, "Linux, redes e investigação são uma combinação relevante para segurança.")

    # DevOps & SRE: regras 16 a 18
    @Rule(Perfil(atividade="automacao"))
    def devops_automacao(self):
        self.registrar("DevOps & SRE", 3, "Você prefere automatizar tarefas e manter sistemas funcionando.")

    @Rule(Perfil(ferramenta="devops", entrega="infra"))
    def devops_entrega(self):
        self.registrar("DevOps & SRE", 3, "Sua afinidade com automação e infraestrutura está alinhada a DevOps/SRE.")

    @Rule(Perfil(ambiente="infraestrutura", ferramenta="linux"))
    def devops_linux(self):
        self.registrar("DevOps & SRE", 2, "Linux e infraestrutura combinam com automação e confiabilidade.")

    # Computação em Nuvem: regras 19 a 21
    @Rule(Perfil(atividade="infraestrutura"))
    def cloud_infraestrutura(self):
        self.registrar("Computação em Nuvem", 2, "Você tem interesse em configurar servidores, redes e infraestrutura.")

    @Rule(Perfil(ferramenta="cloud"))
    def cloud_ferramentas(self):
        self.registrar("Computação em Nuvem", 4, "Sua afinidade com ferramentas de nuvem favorece essa trilha.")

    @Rule(Perfil(entrega="infra", ambiente="infraestrutura"))
    def cloud_entrega(self):
        self.registrar("Computação em Nuvem", 3, "Você prefere uma infraestrutura estável e escalável.")

    # Desenvolvimento Mobile: regras 22 a 24
    @Rule(Perfil(atividade="mobile"))
    def mobile_atividade(self):
        self.registrar("Desenvolvimento Mobile", 4, "Você prefere criar aplicativos para celulares.")

    @Rule(Perfil(entrega="app"))
    def mobile_entrega(self):
        self.registrar("Desenvolvimento Mobile", 3, "Seu resultado preferido é um aplicativo para dispositivos móveis.")

    @Rule(Perfil(ferramenta="javascript", ambiente="desenvolvimento", entrega="app"))
    def mobile_javascript(self):
        self.registrar("Desenvolvimento Mobile", 2, "JavaScript e interesse por aplicativos podem combinar com desenvolvimento multiplataforma.")

    # QA/Testes: regras 25 a 27
    @Rule(Perfil(atividade="testes"))
    def qa_atividade(self):
        self.registrar("Engenharia de Qualidade e Testes (QA)", 4, "Você gosta de testar programas e encontrar defeitos.")

    @Rule(Perfil(entrega="qualidade"))
    def qa_entrega(self):
        self.registrar("Engenharia de Qualidade e Testes (QA)", 3, "Você valoriza software confiável e com menos defeitos.")

    @Rule(Perfil(ferramenta="qa", ambiente="qualidade"))
    def qa_ferramentas(self):
        self.registrar("Engenharia de Qualidade e Testes (QA)", 3, "Sua afinidade com ferramentas de teste e melhoria contínua combina com QA.")

    # Gestão de Produtos: regras 28 a 30
    @Rule(Perfil(atividade="negocio"))
    def produto_atividade(self):
        self.registrar("Gestão de Produtos", 4, "Você prefere planejar produtos e entender as necessidades dos usuários.")

    @Rule(Perfil(entrega="estrategia"))
    def produto_entrega(self):
        self.registrar("Gestão de Produtos", 3, "Você prefere trabalhar com direção e prioridades de um produto.")

    @Rule(Perfil(ferramenta="design", ambiente="negocio"))
    def produto_design_negocio(self):
        self.registrar("Gestão de Produtos", 2, "Seu interesse por design e negócios combina com a integração entre usuários e desenvolvimento.")

    # Regras adicionais de desempate e reforço por afinidade.
    @Rule(Perfil(matematica="Alta", atividade="dados", ferramenta="python"))
    def reforco_analitico(self):
        self.registrar("Ciência de Dados e Machine Learning", 2, "A combinação de análise, matemática e Python reforça o perfil analítico.")

    @Rule(Perfil(matematica="Baixa", atividade="interfaces"))
    def reforco_visual(self):
        self.registrar("Desenvolvimento Front-end & UI/UX", 1, "A preferência visual pesa mais do que uma afinidade matemática alta para esta recomendação.")

    @Rule(Perfil(atividade="seguranca", ferramenta="linux", entrega="protecao"))
    def reforco_seguranca(self):
        self.registrar("Cibersegurança", 2, "Investigação, Linux e proteção aparecem juntos nas suas respostas.")

    @Rule(Perfil(atividade="automacao", ferramenta="devops", ambiente="infraestrutura"))
    def reforco_devops(self):
        self.registrar("DevOps & SRE", 2, "Automação, ferramentas de entrega e infraestrutura formam um perfil coerente de DevOps/SRE.")

    @Rule(Perfil(atividade="pipeline", ferramenta="dados", entrega="dados"))
    def reforco_engenharia_dados(self):
        self.registrar("Engenharia de Dados", 2, "Preparação, ferramentas e disponibilidade de dados reforçam essa trilha.")

    @Rule(Perfil(atividade="testes", ferramenta="qa", entrega="qualidade"))
    def reforco_qa(self):
        self.registrar("Engenharia de Qualidade e Testes (QA)", 2, "Atividade, ferramenta e resultado esperado estão alinhados com QA.")

    @Rule(Perfil(atividade="negocio", entrega="estrategia"))
    def reforco_produto(self):
        self.registrar("Gestão de Produtos", 2, "Planejamento e definição de prioridades aparecem juntos nas suas respostas.")


def diagnosticar(perfil):
    """Executa as regras e retorna a trilha mais bem pontuada e suas justificativas."""
    motor = ConsultorCarreiras()
    motor.reset()
    motor.declare(Perfil(**perfil))
    motor.run()

    pontuacoes = defaultdict(int)
    motivos = defaultdict(list)
    for fato in motor.facts.values():
        if isinstance(fato, Evidencia):
            carreira = fato["carreira"]
            pontuacoes[carreira] += fato["pontos"]
            if fato["motivo"] not in motivos[carreira]:
                motivos[carreira].append(fato["motivo"])

    # Uma regra neutra garante resultado mesmo quando as respostas não combinam
    # com uma regra específica.
    if not pontuacoes:
        carreira = "Desenvolvimento Back-end"
        pontuacoes[carreira] = 1
        motivos[carreira].append("Não houve combinação forte; esta é uma sugestão inicial para explorar programação.")

    ordem = sorted(CARREIRAS, key=lambda nome: (-pontuacoes[nome], nome))
    melhor = ordem[0]
    if not motivos[melhor]:
        motivos[melhor] = ["Esta foi a trilha com maior pontuação entre as regras ativadas."]
    return {
        "carreira": melhor,
        "descricao": CARREIRAS[melhor],
        "pontuacao": pontuacoes[melhor],
        "motivos": motivos[melhor],
        "alternativas": [(nome, pontuacoes[nome]) for nome in ordem[1:4]],
        "pontuacoes": dict(pontuacoes),
    }
