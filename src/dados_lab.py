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

        # Define regexes for extracting arrays from output
        # "lines": list of regexes to match lines containing arrays
        # "values": list of regexes to extract values from matched lines
        self.array_regexes = {
            "lines": [],
            "values": []
        }

        # Function to compare student output with correct output
        # Should return (bool, str) where bool indicates if the output is correct
        # and str is a message describing the result
        def correction_function(student_values, answers_json):
            # TODO: Implement comparison logic for your specific lab
            # student_values: list of extracted values from student output
            # answers_json: dict with correct answers from saida{numero_lab}.json
            return True, "Output is correct"
        
        self.correction_function = correction_function

        # Leave empty if all outputs are of the format Lab{numero_lab}_Seu_Nome.txt
        # Add elements if they're of the format Lab{numero_lab}_Seu_Nome_out_type.txt
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
        # TODO: Add your lab-specific correction criteria
        self.ai_correction_criteria = []

        # Put false if no report expected (the first .pdf file will be considered for each student)
        self.has_report = False

