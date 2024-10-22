import json
import os
import requests
from langchain.tools import tool
from dotenv import load_dotenv
from datetime import datetime
import re
import pandas as pd
import psycopg2



# Define diretório de manipulação
hist_path = 'historico_chat'

# Cria o diretório se ele não existir
if not os.path.exists(hist_path):
    os.makedirs(hist_path)
    print(f"Diretório '{hist_path}' criado.")
else:
    print(f"O diretório '{hist_path}' já existe.")
    
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
        


class SearchTools():

    @tool("Pesquisar no Conversas no DB")
    def search_internet(query):
        """Pesquisar conversas no banco de dados
        com base no dia anterior"""
        print("Pesquisando conversas...")

        load_dotenv()

        DB_USER = os.getenv("DB_USER")
        DB_PASS = os.getenv("DB_PASS")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")
        DB_NAME = os.getenv("DEB_NAME")
        
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

        
        
        
        top_result_to_return = 5
        url = "https://google.serper.dev/search"
        payload = json.dumps(
            {"q": query, "num": top_result_to_return, "tbm": "nws"})
        headers = {
            'X-API-KEY': os.environ['SERPER_API_KEY'],
            'content-type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        # verificar se existe a chave 'organic'
        if 'organic' not in response.json():
            return "Desculpe, não consegui encontrar nada sobre isso. Pode haver um erro com a sua chave de API do Serper."
        else:
            results = response.json()['organic']
            string = []
            print("Resultados:", results[:top_result_to_return])
            for result in results[:top_result_to_return]:
                try:
                    # Tentativa de extrair a data
                    date = result.get('date', 'Data não disponível')
                    string.append('\n'.join([
                        f"Título: {result['title']}",
                        f"Link: {result['link']}",
                        f"Data: {date}",  # Incluir a data na saída
                        f"Resumo: {result['snippet']}",
                        "\n-----------------"
                    ]))
                except KeyError:
                    next # type: ignore

            return '\n'.join(string)
