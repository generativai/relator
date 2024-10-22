from datetime import datetime
from crewai import Task


class RelatorioTasks():

    def analisar_conversa_task(self, agente, contexto):
        return Task(
            description='Analisar a conversa, entender contexto, capturar informações relevantes, identificar gaps e propor melhorias no relacionamento com cliente.',
            agent=agente,
            async_execution=True,
            context=contexto,
            expected_output=f"""Uma análise formatada em markdown, incluindo Objetivos, Resumo, 
                Análise, GAPs, Pendências, Avaliações e uma seção "Próximos passos:"
                Exemplo de saída: 
                '## Relatório do grupo <nome_do_grupo>\n\n
                **Dia: {datetime.now().date}**
                **Objetivos:** Objetivos da etapa...\n\n
                **Resumo:** Os participantes falaram sobre nicho...\n\n
                **Análise:**\n\n
                - O participante esteve empolgado e se mostrou...\n\n
                **GAPs:** Identifiquei os seguintes gaps...\n\n
                **Pendências:** Para atingir a etapa...\n\n
                **Avaliações:** Avaliações sobre a etapa e conversa...\n\n
                **Próximos passos:** Sugiro, para atingir a meta...
            """
        )

    def compile_task(self, agente, contexto, funcao_callback, init_projeto, prev_termino):
        return Task(
            description='Compilar o relatório',
            agent=agente,
            context=contexto,
            expected_output=f"""Um relatório completo em formato markdown, com estilo e layout consistentes.
                Exemplo de saída: 
                '# Relatório do grupo <nome_do_grupo>:\\n\\n
                - Data: {datetime.now().date}\\n
                - Projeto iniciado em: {init_projeto}\\n
                - Previsão de térimino {prev_termino}\\n\\n

                **Objetivos:** A IA teve grande destaque nos comerciais do Super Bowl deste ano...\\n\\n
                **Resumo do dia:**...\\n\\n
                **Análise de sentimentos:**...\\n\\n
                **GAPs:**...\\n\\n
                **Pendências:**...\\n\\n
                **Avaliações:**...\\n\\n
                **Próximos passos:**...\\n\\n
            """,
            callback=funcao_callback
        )

