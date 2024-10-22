import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import TXTSearchTool
from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from datetime import datetime
import re
import pandas as pd
import psycopg2

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DEB_NAME")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

relatorio_dia = 3 # Correto = 1 day / Relatório de 1 dia atrás
dias_de_projeto = 30

# Define diretório de manipulação
hist_path = 'historico_chat'
agent_path = 'agent_results'

# Cria o diretório se ele não existir
if not os.path.exists(hist_path):
    os.makedirs(hist_path)
    print(f"Diretório '{hist_path}' criado.")

if not os.path.exists(agent_path):
    os.makedirs(agent_path)
    print(f"Diretório '{agent_path}' criado.")

    
def save_to_txt(file_name, file):
    """
    Salva as saídas do agente em um arquivo .txt.

    Parameters:
    file_name (str): O nome do arquivo onde as saídas serão salvas.
    goal (str): O objetivo do agente.
    backstory (str): A história de fundo do agente.
    """
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(file)  # Grava apenas o objetivo do agente

# Definir os parâmetros de conexão com o PostgreSQL
usuario = DB_USER
senha = DB_PASS
host = DB_HOST  
porta = DB_PORT           # Porta padrão do PostgreSQL
banco_de_dados = DB_NAME

# Função para criar um DataFrame a partir de uma tabela do banco de dados
def carregar_tabela_postgresql(nome_tabela):
    try:
        # Estabelecendo conexão com o banco de dados
        conn = psycopg2.connect(
            dbname=banco_de_dados,
            user=usuario,
            password=senha,
            host=host,
            port=porta
        )
        
        # Query para selecionar todos os dados da tabela desejada
        query = f"SELECT * FROM {nome_tabela};"
        
        # Lendo os dados diretamente no DataFrame
        df = pd.read_sql_query(query, conn)
        
        # Fechando a conexão
        conn.close()
        
        return df
    
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

## Função para criar um DataFrame a partir de uma tabela do banco de dados, permitindo parametrizar a condição WHERE
def carregar_tabela_com_where(nome_tabela, where_condition):
    try:
        # Estabelecendo conexão com o banco de dados
        conn = psycopg2.connect(
            dbname=banco_de_dados,
            user=usuario,
            password=senha,
            host=host,
            port=porta
        )
        
        # Query para selecionar os dados da tabela desejada com a condição WHERE
        query = f"SELECT * FROM {nome_tabela} WHERE {where_condition};"
        
        # Lendo os dados diretamente no DataFrame
        df = pd.read_sql_query(query, conn)
        
        # Fechando a conexão
        conn.close()
        
        return df
    
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# chat_history = carregar_tabela_com_where("chat_history_t",f"created_at::date = (CURRENT_DATE - INTERVAL '{relatorio_dia} day')") #Coreto = 1 day
chat_history = carregar_tabela_com_where("chat_history",f"created_at::date = '2024-02-16'") #Coreto = 1 day
people = carregar_tabela_postgresql("people")
groups = carregar_tabela_postgresql("groups")
packages = carregar_tabela_postgresql("packages")
departments = carregar_tabela_postgresql("departments")
# print('*'*5,chat_history)

# grupos
groups = groups.rename(columns={'description': 'group_description', 'created_at': 'group_created'})
groups_cols = ['group_id','group_jid', 'group_name', 'package_id', 'project_id', 'group_description', 'group_created']
groups = groups[groups_cols]

# pacotes
packages = packages.rename(columns={'description': 'package_description'})
packages_cols = ['package_id', 'package_name']
packages = packages[packages_cols]

# pessoas
people_cols = ['remote_jid', 'person_name','nickname','department_id','is_client']
people = people[people_cols]

# departamentos
departments = departments.rename(columns={'description': 'department_description'})
departments_cols = ['department_id', 'department_name','department_description']
departments = departments[departments_cols]

# Unindo pessoas e departamentos
person_dep = pd.merge(people, departments, on='department_id', how='left')
person_dep_cols = ['remote_jid', 'person_name','nickname','is_client','department_name']
person_dep = person_dep[person_dep_cols]

# Unindo historico e pessoas
chat_history = pd.merge(
    chat_history,
    person_dep,
    left_on='sender_id',  # Coluna do DataFrame chat_history
    right_on='remote_jid',  # Coluna do DataFrame person_dep
    how='left'  # Tipo de merge
)

# Unindo gupos e pacotes
grupos_pacotes = pd.merge(groups, packages, on='package_id', how='left')

# Unindo historico e grupos
chat_groups_history = pd.merge(
    chat_history,
    grupos_pacotes,
    left_on='groupJid',  # Coluna do DataFrame chat_history
    right_on='group_jid',  # Coluna do DataFrame person_dep
    how='left'  # Tipo de merge
)

chat_gh_cols = ['instance', 'receiver', 'sender_id','push_name','base64_data','sequence_number','group_jid','package_id','group_description','from_me']
chat_groups_history = chat_groups_history.drop(columns=chat_gh_cols)

dfs_groupJid = {}

#  Obter todos os valores únicos na coluna groupJid
grupos = chat_groups_history['groupJid'].unique()

# Para cada valor, filtrar e armazenar em um novo DataFrame
for g in grupos:
    df_grupos = chat_groups_history[chat_groups_history['groupJid'] == g]
    df_grupos = df_grupos.sort_values(by='created_at', ascending=True)
    dfs_groupJid[g] = df_grupos
    # print(g)
    
    # Cria arquivo txt
    file_name = f'{g}.txt'  # Nome do arquivo
    file_path = os.path.join(hist_path, file_name)  # Caminho completo para o arquivo

    # Transformando o DataFrame em um arquivo TXT
    df_grupos.to_csv(file_path, sep='\t', index=False)
    
    # Obter valores 
    group_id = df_grupos['group_id'].unique().tolist()
    group_id = group_id[0]

    group_jid = df_grupos['groupJid'].unique().tolist()
    group_jid = group_jid[0]

    group_name = df_grupos['group_name'].unique().tolist()
    group = group_name[0]

    package_name = df_grupos['package_name'].unique().tolist()
    package = package_name[0]

    print(group_id)
    print(group_jid)
    print(group)
    print(package)
    
    # Carrega relatórios anteriores
    relatorios_antigos = carregar_tabela_com_where('reports', f'group_id={group_id}')
    
    # Inicializar a string com as tags de abertura e fechamento
    relatorios_anteriores = """<relatorios_anteriores>
    """
    # Loop para percorrer cada linha do DataFrame relatorios_antigo
    for index, row in relatorios_antigos.iterrows():
        # Converter a linha em uma string no formato desejado e adicionar à string 'relatorios_anteriores'
        relatorios_anteriores += f"{row.to_string(index=False)}\n"

    # Fechar a tag de </relatorios_anteriores>
    relatorios_anteriores += "</relatorios_anteriores>"

    # Datas do projeto
    data_inicial = df_grupos.group_created.iloc[0].date()  
    data_inicial_formatada = data_inicial.strftime('%d/%m/%Y')
    
    data_final = data_inicial + pd.offsets.BDay(dias_de_projeto)  # Dias úteis
    data_final_formatada = data_final.date().strftime('%d/%m/%Y')  

    print(f'Data inicial do projeto: {data_inicial_formatada}')
    print(f'Data final prevista: {data_final_formatada}')
    
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
    5. Registrar dimínio;
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
    4.Solicitar mineração de produtos baseados no segmento e plataforma à equipe de desenvolvimento;

    # Etapa 03 - Prazo: 6 dias
    1. Aprovação de logo, caso solicite reajuste: Prazo de 1 dia;
    2. Envio de produtos minderados - Prazo: 2 dias;
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
    
    solicitacoes = f"""<solicitacoes>
    1. OBJETIVOS - Analise o histórico de conversas no whatsapp com base em <etapas></etapas> do projeto.\n
    2. GAP - Identificação de possíveis GAPs no relacionamento com o cliente.\n
    3. METODOLOGIA - Resumir o que ocorreu, analisar sentimentos de clientes e membros da equipe, identificar gaps, propor scripts e melhorias no atendimento.\n
    5. RESULTADOS - Identificar cronograma e cumprimento de prazos, bem como a satisfação do cliente.\n
    {etapas}</solicitacoes>\n
    """
    
    controles = """
    <controles>
    NÍVEIS DE CONTROLE:\n
    1. Entonação: Formal 
    5. Foco: Você deve responder sempre com foco nos objetivos das <etapas> buscando encontrar GAPs, atingir metas e cumprir prazos.
    6. Línga: Escreva sempre em português do Brasil, como brasileiros especialistas em gestão de negócios constumam escrever.
    7. Nível de originalidade: 10, onde 1 é pouco original e 10 é muito original. 
    8. Nível de abstração: 1, onde 1 é muito concreto e 10 é muito abstrato e irreal.
    </controles>\n
    """
    
    restricoes = """<restricoes>
    O QUE VOCÊ NÃO DEVE FAZER:\n
    1. Criar novas informações.
    2. Oferecer descontos.
    </restricoes>\n
    """
    
    # Modelo de relatório
    template = """<template>
    Relatório do Grupo: <nome_do_grupo> - Etapa: <etapa>\n
    Dia: <dia>\n
    Prazo: <prazo>
    1. Objetivos: Objetivos da etapa\n 
    2. Resumo do dia: Um resumo do que houve\n
    2. Análise de sentimento: Análise de sentimentos dos <clientes>\n
    3. GAPs: Os gaps identificados na relação com cliente, objetivos e etapas do projeto\n
    4. Pendências: As pendências do dia e da etapa\n 
    5. Avaliações: Avaliações sobre o dia e etapa\n
    6. Proposta de melhorias: Propostas\n
    </template>
    """
    
    agent_relator_goal = (
        "Ler conversas de whatsapp e extrair informações específicas conforme definido nas solicitações em <solicitacoes>. "
        f"Gerar um relatório em pt-BR de acordo com o modelo especificado em <template>.\n {solicitacoes} {template}"
    )

    agent_relator_backstory = (
        "Você é um especialista em processos de atendimento. "
        "Sua missão é analisar as conversas entre a equipe de trabalho e os clientes e extrair informações, "
        "identificar GAPs, entender o processo e as etapas do projeto, gerar insights, propor ações e  melhorias para alcançar, "
        "além dos objetivos principais, a satisfação do cliente. "
        "Sua função é fundamental para avaliar o trabalho da equipee otimizar processos. "
        "Ao responder as solicitações delimitadas por <solicitacoes></solicitacoes>, você deve levar em consideração as "
        "definições de controle em <controle></controle> e as restrições em <restricoes></restricoes>.\n\n"
        f"{solicitacoes} {restricoes} {controles}"
    )

    # Exibindo os resultados
    # save_to_txt('agent_relator_goal',agent_relator_goal)
    # save_to_txt(f'relator_{g}',agent_relator_backstory)
    
    def create_agent_relator(llm, tool):
        return Agent(
            role="Relator de conversas",
            goal=agent_relator_goal,
            backstory=agent_relator_backstory,
            tools=[tool],
            verbose=True,
            memory=False,
            llm=llm
        )
        
    agent_revisor_goal = (
        "Leia os dados extraídos pelo Agente Relator e verifique se o relatório foi produzido "
        "de acordo com o template proposto em <template>, com os dados solicitados em <solicitacoes>. "
        "Compare o relatório produzido pelo agente relator com relatórios anteriores se existirem "
        "em <relatorios_anteriores> Como resultado do seu trabalho, "
        "você deve retornar um relatório revisado no mesmo formato do "
        f"template proposto. {solicitacoes} {template} {relatorios_anteriores}"
    )

    agent_revisor_backstory = (
        "Você é um especialista em revisão de relatórios. "
        "Sua função é garantir que os dados extraídos reflitam as solicitações definidas em <solicitacoes> "
        "e estejam formatados de acordo com o template proposto em <template>. "
        "Sua atenção aos detalhes assegura que os resultados finais sejam precisos "
        f"conforme as expectativas. {solicitacoes} {template}"
    )

    # Exibindo os resultados
    # save_to_txt('agent_revisor_goal',agent_revisor_goal)
    # save_to_txt(f'revisor_{g}',agent_revisor_backstory)
    
    def create_agent_revisor(llm):
        return Agent(
            role="Revisor do relatório",
            goal=agent_revisor_goal,
            backstory=agent_revisor_backstory,
            verbose=True,
            memory=False,
            llm=llm
        )
    
    relator_task_description = (
        "Leia o arquivo e retorne um relatório com as solicitações definidas em <solicitacoes> "
        "usando o modelo definido em <template>. "
        f"{solicitacoes} {template}"
    )

    relator_task_expeted_output = (
        "Relatório com as solicitações definidas em <solicitacoes>"
        "usando o modelo definido em <template>. "
        f"{solicitacoes} {template}"
    )
    
    def relator_task(agent_relator):
        return Task(
            description=relator_task_description,
            expected_output=relator_task_expeted_output,
            agent=agent_relator,
            output_file=f'{agent_path}/t_rel_{g}.csv'
        )
        
    revisor_task_description = (
        "Revise o relatório produzido pelo agente revisor para garantir que ele esteja de acordo com o template definido em <template> " 
        " e contenha todas as informações solicitadas em <solicitacoes> "
        f"{solicitacoes} {template}"
    )
    revisor_task_expeted_output = (
        "Relatório revisado que esteja de acordo com o template definido em <template>"
        " e contenha todas as informações solicitações em <solicitacoes>"
        f"{solicitacoes} {template}"
    )
    
    def revisor_task(agent_revisor):
        return Task(
            description=relator_task_description,
            expected_output=relator_task_expeted_output,
            agent=agent_revisor,
            output_file=f'{agent_path}/t_rev_{g}.csv'
        )
    
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
    os.environ['GROQ_API_KEY'] = GROQ_API_KEY
    
    # gpt = ChatOpenAI(model="gpt-4")
    gpt = ChatGroq(model="groq/llama3-8b-8192")
    
    txt = file_path
    txt_tool = TXTSearchTool(txt)
    
    # relator
    agent_relator = create_agent_relator(gpt,txt_tool)
    task_relator = relator_task(agent_relator)
    # revisor
    agent_revisor = create_agent_revisor(gpt)
    task_revisor = revisor_task(agent_revisor)

    crew = Crew(
        agents=[agent_relator,agent_revisor],
        tasks=[task_relator,task_revisor],
        process=Process.sequential,
        output_log_file='logfile.csv'
    )

    ipt = {
        "solicitacoes": solicitacoes,
        "template": template,
        "restricoes": restricoes,
        "controles": controles,
    }

    results = crew.kickoff(inputs=ipt)
    
    #TODO: armazenar saida no banco de dados
    #TODO: enviar emails