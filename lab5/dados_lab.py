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
        self.ai_correction_criteria = [

            """Encapsulamento - Parte 1:
            Verificar se o aluno respeitou completamente as regras de encapsulamento:
            - Não usar variáveis globais.
            - A função main NÃO pode acessar diretamente os campos internos do TAD (vet, quant, MAX).
            - A função main só pode interagir com o TAD por meio das funções públicas.
            - Campos internos da struct TipoAgenda não podem ser manipulados fora das funções do TAD.""",

            """Uso obrigatório da estrutura-base fornecida:
            Verificar se o aluno manteve exatamente:
            - as declarações de tipos (struct TipoTarefa e TipoAgenda),
            - os cabeçalhos das funções,
            - a função main sem modificações estruturais.
            Alterações na main, renomear funções públicas, ou mudar assinaturas resulta em penalidade.""",

            """Funções públicas obrigatórias:
            Conferir se o aluno implementou TODAS as funções solicitadas, com assinaturas idênticas:
            - Inicializar
            - Finalizar
            - Inserir
            - ConsultarMax
            - RemoverMax (deve ser void)
            - FilaVazia (retorna bool)
            - FilaCheia (retorna bool)
            A main não pode chamar funções privadas, apenas estas.""",

            """Heap máximo indexado em 1:
            Verificar se o heap está implementado corretamente:
            - a posição 0 do vetor NÃO é usada;
            - a raiz está na posição 1;
            - o vetor é alocado com tamanho MAX+1;
            - o TAD utiliza um heap de máximo (max-heap).""",

            """Operações de heap:
            Validar as regras de funcionamento:
            - Inserir deve aplicar sift-up (subir enquanto prioridade maior que o pai).
            - RemoverMax deve aplicar sift-down (descer comparando filhos).
            - ConsultarMax deve simplesmente retornar vet[1].
            - A propriedade do heap deve ser mantida após cada operação.""",

            """Inicializar:
            Deve:
            - alocar o vetor do heap (malloc),
            - definir quant = 0,
            - armazenar o valor MAX lido da entrada.
            Não pode ler arquivos ou imprimir nada.""",

            """Finalizar:
            Deve apenas:
            - liberar o vetor com free,
            - não deve imprimir nada,
            - não deve encerrar arquivos (isso é da main).""",

            """FilaVazia e FilaCheia:
            Conferir:
            - FilaVazia retorna quant == 0,
            - FilaCheia retorna quant == MAX.
            Não deve imprimir nada e não pode acessar arquivo.""",

            """Inserir:
            Regras obrigatórias:
            - não pode inserir se a fila estiver cheia (main já testa isso),
            - inserir no final do heap (quant+1),
            - aplicar sift-up,
            - atualizar quant.
            Não pode imprimir nada.""",

            """RemoverMax:
            Regras obrigatórias:
            - só executa se quant > 0 (main testa antes),
            - troca raiz com o último elemento,
            - decrementa quant,
            - aplica sift-down.
            Deve ser void e não imprimir nada.""",

            """ConsultarMax:
            Regras obrigatórias:
            - retornar o elemento da raiz (vet[1]).
            - não pode remover o elemento,
            - não pode imprimir nada.""",

            """Entrada e formato:
            Verificar:
            - pular as 5 linhas iniciais,
            - ler tamanho máximo,
            - pular mais 3 linhas,
            - seguir exatamente o fluxo da main fornecida,
            - não alterar lógica de leitura.
            Descrição da tarefa deve ter até 40 caracteres.""",

            """Saída e alinhamento:
            Conferir:
            - cabeçalho de saída deve seguir exatamente o modelo fornecido,
            - linhas de cabeçalho com máximo de 70 caracteres,
            - mensagens de erro e aviso devem ser alinhadas como o exemplo,
            - ao consultar tarefa, imprimir prioridade e descrição no formato esperado.""",

            """Mensagens obrigatórias:
            Verificar se o programa imprime:
            - AVISO quando consultar tarefa com agenda vazia,
            - ERRO quando tentar inserir agenda cheia,
            - AVISO final caso a agenda termine vazia após o comando FIM.
            As mensagens podem ter frases diferentes, mas o alinhamento deve seguir o exemplo.""",

            """Processamento após FIM:
            O programa deve:
            - imprimir cabeçalho de 'Fica para o dia seguinte',
            - desfazer o heap removendo um por um,
            - imprimir tarefas em ordem decrescente de prioridade,
            - usar ConsultarMax e RemoverMax para isso.
            A main não pode acessar o vetor do heap diretamente.""",

            """Proibição de acessar campos internos do TAD na main:
            A main NÃO pode acessar:
            - A.quant
            - A.MAX
            - A.vet
            - qualquer posição do vetor
            Isso gera penalização imediata.""",

            """Erros críticos:
            Casos que devem gerar penalização grande:
            - código não compila,
            - main alterada,
            - heap não usado,
            - TAD ignorado (tudo feito na main),
            - funções com assinaturas diferentes das fornecidas.""",

            """Implementações corretas, mas significativamente subótimas (heap):
            Este critério identifica soluções que *funcionam* e passam nos casos básicos,
            mas apresentam problemas estruturais ou lógicos que tornam a implementação
            muito inferior ao esperado, mesmo sem ser completamente errada.
            Penalizações moderadas devem ser aplicadas quando ocorrerem situações como:

            1. Sift-up ou sift-down corretos, mas implementados com complexidade desnecessária:
            - loops que percorrem o heap inteiro para encontrar pai ou filho;
            - comparação redundante com todos os filhos em vez de apenas o maior;
            - dupla verificação de condições sem necessidade.

            2. Uso de funções auxiliares extremamente ineficientes:
            - recalcular o maior filho escaneando toda a árvore;
            - recomputar índices de pai/filho em loops externos sem necessidade.

            3. Implementação de RemoverMax trocando elementos muitos mais vezes que o necessário:
            - realizar várias trocas de posições antes de iniciar o sift-down;
            - usar swaps repetidos em vez de mover o buraco (hole method).

            4. Inserção ou remoção funcionando, mas com ordem subótima:
            - copiar elementos sucessivamente para cima/baixo ao invés de trocar posições;
            - deslocamentos lineares quando o heap permite operações logarítmicas.

            5. Uso incorreto de condições lógicas:
            - sift-down que primeiro tenta descer pela esquerda, e só depois compara com direita,
                podendo resultar em árvores quase certas com trabalho extra desnecessário.

            6. Acessos desnecessários à memória:
            - múltiplas leituras do mesmo elemento do vetor dentro do mesmo laço;
            - cálculo repetido (2*i, 2*i+1, i/2) dentro de loops sem salvar em variáveis locais.

            Observação importante:
            Não se penaliza itens menores ou pedagógicos, como:
            - comentar pouco,
            - implementar sift-down com while ou com if + loop,
            - trocar pai/filho com uma função auxiliar,
            - usar variáveis auxiliares simples.
            Somente penalizar quando o código fica visivelmente mais lento ou trabalhoso
            sem necessidade, mesmo mantendo a corretude funcional do heap.""",

        ]


        # Put false if no report expected (the first .pdf file will be considered for each student)
        self.has_report = False

