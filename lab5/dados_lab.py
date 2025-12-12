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
            "error_type",
            nargs="?",
            default="ALL",
            help="Tipo de erro a corrigir (padrão: ALL)"
        )

        args = parser.parse_args()
        argv = sys.argv

        self.numero_lab = int(re.search(r"\d+", argv[0]).group())
        self.lab_folder_path = f"./lab{self.numero_lab}"

        self.testcases_path = os.path.join(self.lab_folder_path, "testcases")
        self.student_errors_path = os.path.join(self.lab_folder_path, "erros-alunos")
        self.students_path = os.path.join(self.lab_folder_path, args.students_path)

        self.error_type_to_correct = args.error_type
        self.do_bronco_detection = args.bronco
        self.student_to_correct = args.student
        self.jump_to_student = args.jump_to_student

        self.compile_timeout = 5

        # Increase this if a testcase takes long to run
        self.run_timeout = 5

        self.student_folder_files = ["logs_correcao_auto.txt", "logs_correcao_bronco.txt", "outputs", ".cpp"]

        # The field in "saida*.json" which contains the correct order of output
        self.json_field_with_array = "order"

        self.array_regexes = {
            "lines": [
                r"^\s*(?:\d+|ERRO|AVISO|FICA PARA|AGENDA VAZIA)"
            ],
            "values": [
                r"^\s*(\S+)"
            ]
        }

        # If you want to use values in json field array to quickly build a regex
        # Which overwrites field lines of self.array_regexes
        self.use_json_to_get_line_patterns = False

        # Dict to find int values on the output txt
        # Keys need to be on the EXACT order
        self.value_to_regexes = {
            # "num_comparacoes": {
            #     "lines": [
            #         r"\bcomparacoes\b",
            #         r"\bfeitas\b"
            #     ],
            #     "values": [
            #         r"-?\d+"
            #     ]
            # }
        }

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
        self.ai_correction_criteria_lab6 = [
            """Encapsulamento e modularidade:
            - Não usar variáveis globais desnecessárias.
            - Função main NÃO deve acessar diretamente dados internos do grafo (matriz, vetores auxiliares).
            - Toda interação deve ser feita por funções públicas.
            - Funções auxiliares privadas devem ser usadas apenas dentro do TAD do grafo.""" ,

            """Uso obrigatório da estrutura-base fornecida:
            - Manter os tipos e estruturas sugeridas (matriz de adjacências, vetores de tarefas, etc.).
            - Não alterar a função main estruturalmente.
            - Assinaturas das funções públicas devem permanecer idênticas.
            - Qualquer mudança na main, nomes de funções ou parâmetros resulta em penalidade.""" ,

            """Funções públicas obrigatórias:
            Conferir se o aluno implementou TODAS as funções solicitadas, com assinaturas idênticas:
            - Verificar aciclicidade
            - Ordenação topológica
            - Cálculo do tempo mínimo do projeto
            - Determinação do caminho crítico
            A main não deve chamar funções privadas diretamente.""" ,

            """Verificação de aciclicidade:
            - Detectar ciclos corretamente usando DFS ou outro método adequado.
            - Caso haja ciclo, imprimir o ciclo encontrado e mensagem de impossibilidade.
            - Não deve continuar com cálculo do caminho crítico se houver ciclo.""" ,

            """Ordenação topológica:
            - Deve gerar uma ordenação válida do grafo acíclico.
            - A ordenação deve ser usada no cálculo do tempo mínimo.
            - Pode-se usar recursão aqui, conforme permitido.""" ,

            """Cálculo do tempo mínimo:
            - Deve usar a ordem topológica, sem recursão.
            - Considerar corretamente as durações e pré-requisitos.
            - O resultado deve corresponder ao menor tempo total do projeto.""" ,

            """Determinação do caminho crítico:
            - Identificar corretamente uma sequência de tarefas que não pode ter atrasos.
            - Caso haja múltiplos caminhos críticos, mostrar pelo menos um.
            - Mostrar as tarefas na ordem do caminho crítico.""" ,

            """Entrada e formato:
            - Ler arquivo de entrada 'entrada6.txt'.
            - Número máximo de tarefas: 52.
            - Descrições de tarefas: até 30 caracteres.
            - Tarefas identificadas por letra única.
            - Tarefa sem pré-requisito indicada por ponto.
            - Seguir exatamente o fluxo de leitura conforme roteiro.""" ,

            """Saída e alinhamento:
            - Arquivo saída: 'Lab6_seu_nome_e_sobrenomes.txt'.
            - Cabeçalhos e mensagens devem seguir o modelo do roteiro.
            - Mensagens para ciclos e avisos de impossibilidade devem ser claras e alinhadas.
            - Ordenação topológica e caminho crítico devem estar bem apresentadas.""" ,

            """Mensagens obrigatórias:
            - Informar se o grafo contém ciclos.
            - Mostrar ordenação topológica se acíclico.
            - Mostrar tempo mínimo do projeto.
            - Mostrar caminho crítico.
            - Mensagens podem variar em texto, mas alinhamento e clareza são obrigatórios.""" ,

            """Erros críticos:
            - Código não compila.
            - Main alterada estruturalmente.
            - Funções públicas ausentes ou com assinaturas diferentes.
            - Lógica do TAD ou cálculo do tempo mínimo incorretos.
            - Ciclos não detectados corretamente.""" ,

            """Implementações corretas, mas subótimas:
            - Cálculo do tempo mínimo ineficiente (complexidade maior que O(V+E)).
            - Ordenação topológica mal implementada ou repetitiva.
            - Verificação de aciclicidade usando loops desnecessários.
            - Caminho crítico obtido de forma lenta ou com lógica confusa.
            - Penalizar somente se houver impacto perceptível na performance, sem afetar a corretude funcional.""",
        ]


        # Put false if no report expected (the first .pdf file will be considered for each student)
        self.has_report = False

