from crewai import Agent

class RelatorioAgentes():
    def relator_agente(self):
        return Agent(
            role='Relator',
            verbose=True,
        )

    def analista_agente(self, data_inicial, data_final):
        etapas = f"""<etapas>
        Projeto iniciado em: {data_inicial}
        Estimativa de término: {data_final}

        # Etapa 01 - Prazo: 2 dias
        1. Apresentação do atendimento;
        2. Envio do cronograma com prazos;
        3. Definição de nicho:
            3.1. indicar o uso de apenas um ou nichos que se relacionem entre si;
            2.2. caso cliente não tenha nicho em mente, indicar um.
        4. Definir nome;
        5. Registrar domínio;
        6. Referências de Criação de Logo;
            6.1 Identificar se cliente possui referências;
            6.2 Enviar referências;
            6.3 Definir paleta de cores;
        7. Solicitar a equipe de desenvolvimento a criação de logo;
        8. Solicitar ao cliente credenciais de acesso às plataformas a serem integradas:
            Exemplos: aliexpress, appmax, hostinger, facebookt, instagram, yampi, dsers, plataforma de e-comerce;
            - caso tenha domínio registrado, acesso à plataforma de registro;

        # Etapa 02 - Prazo: 2 dias
        1. Definir Categoria;
        2. Buscar e/ou informar referências para layout do e-commerce:
            - Sugerir um de nossos templates: `https://gifthype.com.br/` e  `https://clothingoficial.com.br/`
        3. Escolha da plataforma de mineração:
            Disponíveis: Dropi, Dslite, Dsers, Printful.
        4. Solicitar mineração de produtos baseados no segmento e plataforma à equipe de desenvolvimento;

        # Etapa 03 - Prazo: 6 dias
        1. Aprovação de logo, caso solicite reajuste: Prazo de 1 dia;
        2. Envio de produtos minerados - Prazo: 2 dias;
        3. Envio da precificação padrão utilizada:
            - ( Valor do produto minerado + frete ) * Dólar(R$5,60) * 1,8
        4. Aprovação de produtos;
        5. Solicitar cadastro de produtos no e-commerce;
        6. Solicitar criação de loja:
            - Requisitos:
                - Referência de layout;
                - Acessos das contas que serão integradas à loja
                - Informações do briefing comercial
                - Qualquer outra informação útil que possa agregar na criação do layout
        7. Solicitar desenvolvimento  de banners:
            - Requisitos:
                - Link da loja
                - Referências para criação dos banners
                - Qualquer outra informação útil que possa agregar na criação dos banners

        # Etapa 04 - Prazo: 1 dia
        1. Marcar call para apresentar o ecommerce;
        2. Confirmar call no Google Agenda;
        3. Definir produtos para campanhas de marketing:
            - Caso não exista preferência de produtos pelo cliente, sugerir produtos para as campanhas;
            - Solicitar criação de criativos.

        # Etapa 05 - Prazo: 2 dias após a call
        1. Transferência da loja para o cliente:
            - Loja criada em ambiente de desenvolvimento deve ser transferida para uma conta configurada pelo cliente e ativada pelo mesmo.

        # Etapa 06 - Prazo: 4 dias úteis
        1. Aprovação de criativos:
            Quando aprovado, informar marketing via "Monday" que já pode-se configurar contas de anúncio
            - Requisitos:
                - Contas de anúncio configuradas

        # Etapa 07 - Prazo: 4 dias úteis
        1. Lançar campanhas: 
            Depois de configurar as contas, o marketing enviará ao cliente um link para que ele adicione a forma de pagamento dos anúncios.
        2. Relatório de finalização do projeto

        # Etapa 08 - Dia 18 ao 30 dia 
        1. Acompanhamento e otimização das campanhas, 
        2. Envio de feedback semanal 
        </etapas>
        """
        return Agent(
            role='Analista de contexto',
            goal='Analisar o contexto do histórico de conversas no whatsapp e gerar um relatório detalhado em markdown',
            backstory=f"""Com um olhar crítico e habilidade para simplificar informações complexas, você fornece análises
            perspicazes das etapas por onde o projeto passou e objetivos a alcançar. Use as datas e o guia de etapas de 
            processo para construir o relatório. {etapas}""",
            verbose=True,
            allow_delegation=True,
        )
