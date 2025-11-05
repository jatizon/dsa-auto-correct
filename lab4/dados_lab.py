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

        self.compile_timeout = 5

        # Increase this if a testcase takes long to run
        self.run_timeout = 5

        self.student_folder_files = ["logs_correcao_auto.txt", "logs_correcao_bronco.txt", "outputs", ".cpp", ".pdf", ".PDF"]

        # The field in "saida*.json" which contains the correct order of output
        self.json_field_with_array = "order"

        self.array_regexes = {
            "lines": [],
            "values": [
                r"^(.*\S).*$"
            ]
        }

        # If you want to use values in json field array to quickly build a regex
        # Which overwrites field lines of self.array_regexes
        self.use_json_to_get_line_patterns = True

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

        # Leave empty if al outputs are of the format Labn_Seu_Nome.txt
        # Add element "out_type" if they're of the format Labn_Seu_Nome_out_type.txt
        self.output_types = ["merge", "bubble", "quick"]

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
            4. A quebra de linha deve usar um caractere literal de nova linha (\n) e manter a indentação consistente.\
            
            '''

        # Each element is an instruction for the ai agent
        self.ai_correction_criteria = [
            """BubbleSort não otimizado:
            Verificar se o aluno implementou o BubbleSort clássico com dois loops aninhados
            e SEM otimização de early-exit (sem flag 'troca' que gera break).""",

            """MergeSort:
            Verificar se a implementação corresponde à estrutura do MergeSort fornecido no classroom,
            respeitando os seguintes pontos:
            1. Divida o vetor ou lista ao meio.
            2. Ordene recursivamente a metade esquerda e a metade direita.
            3. Intercale (merge) as duas metades ordenadas em ordem crescente, usando uma estrutura temporária para armazenar os elementos antes de copiá-los de volta.
            4. A recursão deve parar quando a sublista tiver 0 ou 1 elemento.
            5. A implementação pode usar qualquer tipo de dado (inteiros, strings, etc.), mas não pode usar outro algoritmo de ordenação pronto.""",

            """QuickSort:
            Verificar se a implementação corresponde à estrutura do QuickSort fornecido no classroom,
            respeitando os seguintes pontos:
            1. Escolha um elemento do vetor como pivô (por exemplo, o primeiro elemento).
            2. Particione o vetor de forma que todos os elementos menores que o pivô fiquem à esquerda e todos os maiores ou iguais fiquem à direita.
            3. Ordene recursivamente as sublistas à esquerda e à direita do pivô.
            4. A recursão deve parar quando a sublista tiver 0 ou 1 elemento.
            5. A implementação pode usar qualquer tipo de dado (inteiros, strings, etc.), mas deve manter a lógica de partition/pivô conforme o código base, sem usar funções de ordenação prontas.""",

            """Substituição de strcmp por compara:
            Verificar que todas as comparações entre strings utilizam a função 'compara'
            e que não há chamadas diretas a 'strcmp'.""",

            """Definição e incremento do contador dentro de compara:
            Verificar que existe a função 'int compara(const char *a, const char *b)'
            que incrementa o contador e retorna o resultado da comparação entre as strings.""",

            """Vetor de strings (sem vetor de ponteiros):
            Verificar que o programa utiliza um vetor contínuo de caracteres
            (ex.: 'char (*vet)[51]' e 'malloc(n * 51)') e NÃO um 'char **' com malloc individual por string. 
            OK se houver um único malloc que aloca todo o bloco de memória para as n strings.
            ERRO se houver malloc dentro de um loop, alocando memória separadamente para cada string.""",

            """Troca por strcpy (não permuta ponteiros):
            OK se as trocas entre strings são realizadas usando strcpy com um buffer temporário.
            ERRO se a ordenação é feita trocando ponteiros (ex.: 'vet[i] = vet[j]').""",

            """Contagem de comparações correta:
            Verificar que o número de comparações é incrementado apenas dentro da função 'compara'
            e que todas as comparações de strings chamam essa função.""",

            """Medição de tempo correta:
            Verificar que o tempo medido corresponde apenas ao processo de ordenação,
            com o timer iniciado APÓS o preenchimento do vetor e finalizado ANTES da escrita do arquivo.""",

            """Parte B — testes de 2 segundos e variantes de MergeSort:
            Verificar que o aluno executou testes para determinar o maior n que roda em até 2 segundos
            para BubbleSort, QuickSort e MergeSort (com T local e T global).""",

            """Limite de string:
            Verificar que o código reserva espaço suficiente para strings, seguindo a recomendação da aula:
            1. A string deve ter espaço para até 50 caracteres visíveis.
            2. Deve haver 1 posição extra para o caractere de nova linha '\\n' e 1 posição extra para o terminador nulo '\\0'.
            3. Ou seja, o array deve ter tamanho mínimo 52.
            4. Considerar erro se o tamanho do array for menor que 50 ou maior que 55, para evitar alocação insuficiente ou desperdício excessivo de memória.""",

            """Uso correto de vetor auxiliar em MergeSort:
            Verificar se implementa duas versões do MergeSort, uma com vetor auxiliar local e outra com vetor global.""",

            """MergeSort — vetor global como versão principal:
            Verificar que, para o MergeSort, as variantes foram utilizadas da seguinte forma:
            1. MergeSort com vetor T local — usado apenas para testes de desempenho (2 segundos).
            2. MergeSort com vetor T global — considerado a versão “melhor” e deve ser usado em todo o restante do programa, inclusive na Parte A.""",

            """Segurança de memória:
            Confirmar que todas as alocações são liberadas corretamente (free).""",

            """Tamanho do vetor:
            Verificar que os vetores são alocados com tamanho variável (dinâmico), 
            não utilizando constantes fixas. 
            O código deve usar malloc/calloc ou equivalentes para criar vetores do tamanho necessário 
            em tempo de execução, garantindo que o programa funcione para diferentes valores de n.""",

            """Cabeçalho:
            O aluno deve colocar no início do código um cabeçalho com seu nome, o compilador utilizado e sua versão e outros informações."""
        ]

