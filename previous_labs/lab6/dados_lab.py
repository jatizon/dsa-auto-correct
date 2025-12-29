import argparse
import sys
import os
import re

class DadosLab:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Correcao de lab"
        )

        parser.add_argument(
            "students_path", 
            help="Pasta com os alunos a serem corrigidos"
        )

        parser.add_argument(
            "-s", "--student",
            help="Corrigir apenas um aluno específico"
        )

        parser.add_argument(
            "-b", "--bronco",
            action="store_true",
            help="Ativa detecção de bronco"
        )

        parser.add_argument(
            "-j", "--jump_to_student",
            help="Pular para um aluno específico e continuar a partir dele"
        )

        parser.add_argument(
            "-t", "--testcases_folder",
            default="testcases",
            help="Pasta com os testcases a serem corrigidos"
        )


        parser.add_argument(
            "error_type",
            nargs="?",
            default="ALL",
            help="Tipo de erro a corrigir (padrão: ALL)"
        )

        args = parser.parse_args()
        argv = sys.argv

        self.numero_lab = int(re.search(r"\d+", argv[0]).group())
        self.lab_folder_path = f"./lab{self.numero_lab}"

        self.testcases_path = os.path.join(self.lab_folder_path, args.testcases_folder)
        self.student_errors_path = os.path.join(self.lab_folder_path, "erros-alunos")
        self.students_path = os.path.join(self.lab_folder_path, args.students_path)

        self.error_type_to_correct = args.error_type
        self.do_bronco_detection = args.bronco
        self.student_to_correct = args.student
        self.jump_to_student = args.jump_to_student

        #
        # EDIT BELOW THIS LINE
        #

        self.compile_timeout = 20

        # Increase this if a testcase takes long to run
        self.run_timeout = 10

        self.student_folder_files = ["logs_correcao_auto.txt", "logs_correcao_bronco.txt", "outputs", ".cpp"]

        self.array_regexes = {
            "lines": [
                r".*semanas.*",             # line containing the word "semanas" (minimum time line)
                r"^\s*[A-Za-z] [A-Za-z] ",
                r"^\s*[A-Za-z]( {2,}|\t)"
            ],
            "values": [
                r"\d+(?=\s+semanas)",      # extract the number that appears before "semanas"
                r"^\s*(?:[A-Z](?:\s+[A-Z])*)(?=\s*$)", # regex to extract a sequence of uppercase letters separated by spaces
                r"([A-Za-z])(?=\s)"        # capture a single letter that is followed by whitespace
            ]
        }

        # Function to compare student output with correct output
        # Change if needed
        def correction_function(student_values, answers_json):
            print(student_values)
            print(answers_json['order'])
            if answers_json['tem_ciclo'] == True:
                #see if matches any in answers json order array
                for order in answers_json['order']:
                    if student_values == order:
                        return True, "Ordem ciclo CORRETA"
                    return False, "Ordem ciclo ERRADA"
            else:
                ordem_topologica_correta = True
                tempo_minimo_correto = True
                caminho_critico_correto = True
                
                if student_values == []:
                    ordem_topologica_correta = False
                else:
                    if student_values[0]== []:
                        ordem_topologica_correta = False
                    student_topological_order = student_values[0].split()
                    successor_list = answers_json['vertices_que_sucedem']
                    if len(student_topological_order) != len(answers_json['order'][0].split()):
                        ordem_topologica_correta = False
                    else:
                        for i, vertex in enumerate(student_topological_order):
                            if vertex not in successor_list:
                                ordem_topologica_correta = False
                                break
                            for successor in successor_list[vertex]:
                                if successor not in student_topological_order[i+1:]:
                                    ordem_topologica_correta = False
                                    break
                            if not ordem_topologica_correta:
                                break
                            for vertex_before in student_topological_order[:i]:
                                if vertex_before in successor_list[vertex]:
                                    ordem_topologica_correta = False
                                    break
                            if not ordem_topologica_correta:
                                break
                
                # Verifica tempo mínimo (elemento 1)
                if len(student_values) < 2 or student_values[1] != answers_json['order'][1]:
                    tempo_minimo_correto = False
                
                # Verifica caminho crítico (elementos 2 em diante)
                if len(student_values) < len(answers_json['order']) or student_values[2:] != answers_json['order'][2:]:
                    caminho_critico_correto = False
                msg_ordem = "Ordem topológica CORRETA" if ordem_topologica_correta else "Ordem topológica ERRADA"
                msg_tempo = "tempo mínimo CORRETO" if tempo_minimo_correto else "tempo mínimo ERRADO"
                msg_caminho = "caminho crítico CORRETO" if caminho_critico_correto else "caminho crítico ERRADO"
                print(msg_ordem, msg_tempo, msg_caminho)
                mensagem = f"{msg_ordem}, {msg_tempo}, {msg_caminho}"
                tudo_ok = ordem_topologica_correta and tempo_minimo_correto and caminho_critico_correto
                return tudo_ok, mensagem
        
        self.correction_function = correction_function

        # Leave empty if al outputs are of the format   _Seu_Nome.txt
        # Add element "out_type" if they're of the format Labn_Seu_Nome_out_type.txt
        self.output_types = []

        self.ai_correction_introduction_prompt = '''
            Você é um corretor de códigos automatizado. Seu objetivo é corrigir o código do aluno com base nos critérios que serão fornecidos no final.

            Instruções importantes:
            1. Você deve seguir exatamente o modelo de resposta fornecido.
            2. Analise o código do aluno e verifique cada critério.
            3. Sempre forneça feedback detalhado, explicando os erros.
            4. Não adicione informações extras fora do modelo de resposta.

            Como você deve responder (siga exatamente esse formato):
            1. Se o critério estiver correto, escreva:
            [OK]: Nome do critério
            <linha em branco>

            2. Se o critério estiver errado, escreva:
            [ERROU]: Nome do critério
            Justificativa: Explique detalhadamente o erro
            <linha em branco>

            3. Sempre coloque exatamente **uma linha em branco** entre critérios consecutivos.

            4. Não use nenhuma outra formatação ou caracteres extras.

            5. Por exemplo, se um critério fosse "Não usar printf", você escreveria:
            [OK]: Não usar printf

            OU

            [ERROU]: Não usar printf
            Justificativa: Usou printf

            COMENTARIOS:
            Ao final da correção, inclua uma seção chamada "COMENTARIOS" onde você menciona apenas problemas relevantes do código do aluno. 
            - Só mencione problemas que realmente impactem eficiência, legibilidade, manutenção ou corretude do programa.
            - Não mencione pequenas subotimizações, escolhas de estilo ou detalhes que não afetam o funcionamento.
            - Exemplos de pontos a mencionar: alocação ineficiente, uso excessivo de memória, algoritmos com complexidade maior do que o necessário, trocas de strings feitas de forma arriscada.
            - Não mencionar novamente pontos que pertencem aos critérios de correção na seção comentários
            - Se não houver pontos relevantes a comentar, indique que não há observações significativas.

            Instruções de formatação de linha:
            1. Sempre que uma linha de código ou comentário tiver mais de 150 caracteres, quebre a linha para continuar na linha seguinte, usando recuo adequado para manter a legibilidade.
            2. Evite linhas muito longas; prefira múltiplas linhas curtas.
            3. Não quebre as instruções de formato de resposta (como [OK]: ou [ERROU]:) em múltiplas linhas.
            4. A quebra de linha deve usar um caractere literal de nova linha (\n) e manter a indentação consistente.

            **Instrução Geral sobre Tabelas e Gráficos em PDF/Imagem:**  
            Se algum dado necessário para a correção (como tabela, gráfico ou outro resultado) estiver enviado como imagem ou em PDF de forma que não seja possível ler os valores, considere que o critério correspondente **não pôde ser conferido**.  
            - Avisar no critério de correção que a informação não foi encontrada.  
            - Para avaliação, priorizar tabelas ou análises textuais que sejam legíveis.  
            - Se houver números/textos suficientes para avaliação do raciocínio ou coerência, use-os para julgar o relatório.  
            - Essa regra se aplica a tabelas de resultados, gráficos de tempo ou comparações, e qualquer outra informação enviada como imagem.  
            - Se houver outras informações no relatório que te permitam corrigir esse critério, considerá-las
            '''

        # Each element is an instruction for the ai agent
        self.ai_correction_criteria = [

        """Modularização e estrutura de código:
        - Separação clara de funções para:
            - Ler entrada
            - Verificar ciclos
            - Ordenação topológica
            - Cálculo do tempo mínimo
            - Determinação do caminho crítico
        - Não usar variáveis globais desnecessárias.
        - Estruturas (struct ou typedef) utilizadas corretamente.""" ,

        """Leitura e armazenamento das tarefas:
        - Vetor/matriz para armazenar tarefas e pré-requisitos.
        - Cada tarefa possui nome, duração e lista de dependências.
        - Nenhuma informação é perdida ou sobrescrita indevidamente.""" ,

        """Verificação de ciclos:
        - Detecta corretamente ciclos no grafo.
        - Usa algoritmo adequado (DFS ou equivalente).
        - Evita loops infinitos e acessos indevidos ao vetor/matriz.""" ,

        """Ordenação topológica:
        - Produz uma sequência válida respeitando todas as dependências.
        - Implementação correta usando DFS ou outro método apropriado.
        - Ordem das tarefas respeita todas as arestas do grafo.""" ,

        """Cálculo do tempo mínimo:
        - Percorre grafo em ordem topológica (não recursivamente).
        - Soma corretamente durações acumuladas.
        - Determina o tempo mínimo total do projeto.
        - Não acessa dados indevidos fora das funções.""" ,

        """Determinação do caminho crítico:
        - Identifica corretamente tarefas críticas (folga zero).
        - Calcula corretamente uma sequência de caminho crítico.
        - Não acessa diretamente estruturas internas de forma indevida.""" ,

        """Funções e assinaturas:
        - Todas as funções principais estão implementadas com assinaturas corretas.
        - Funções auxiliares (se houver) não violam a modularidade.
        - Main apenas chama as funções públicas, sem lógica própria do algoritmo.""" ,

        """Eficiência e implementação:
        - Algoritmos corretos, sem complexidade desnecessária:
            - Verificação de ciclos eficiente.
            - Ordenação topológica sem percorrer repetidamente o grafo.
            - Cálculo de tempo mínimo e caminho crítico linear ou próximo disso.
        - Evita acessos ou cálculos repetidos desnecessários.""" ,

        """Erros críticos no código:
        - Lógica do grafo incorreta (arestas não respeitadas).
        - Cálculo do tempo mínimo errado.
        - Caminho crítico incorreto.
        - Acessos inválidos a vetores ou ponteiros.
        - Violação grave da modularidade."""
        ]   

        # Put false if no report expected (the first .pdf file will be considered for each student)
        self.has_report = False

