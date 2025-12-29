# Sistema de Correção Automática de Laboratórios

Sistema automatizado para correção de laboratórios de programação em C++. Este sistema compila, executa e avalia o código dos alunos, gerando logs detalhados de correção e detectando problemas comuns.

## Funcionalidades

- **Compilação automática**: Compila código C++ dos alunos com timeout configurável
- **Execução de testcases**: Executa casos de teste e compara saídas
- **Validação de arquivos**: Verifica nomes corretos de arquivos de entrada e saída
- **Detecção de problemas**: Identifica erros de compilação, formatação, e casos de teste falhos
- **Correção com IA**: Usa Gemini AI para análise detalhada de código (bronco detection)
- **Geração de logs**: Cria logs automáticos e manuais para cada aluno
- **Suporte a relatórios PDF**: Extrai e analisa texto de relatórios em PDF

## Estrutura do Projeto

```
monitoria-ces11/
├── main.py                 # Ponto de entrada principal
├── src/
│   ├── dados_lab.py       # Configuração específica de cada laboratório
│   ├── lab_corrector.py   # Lógica principal de correção
│   ├── bronco_finder_agent.py  # Agente de IA para correção detalhada
│   └── utils.py           # Funções utilitárias
├── scripts_utils/         # Scripts auxiliares
├── previous_labs/         # Laboratórios anteriores corrigidos
└── lab{N}/                # Pasta do laboratório atual
    ├── testcases/         # Casos de teste
    ├── alunos/            # Código dos alunos
    └── erros-alunos/      # Arquivos de erro gerados
```

## Requisitos

- Python 3.x
- g++ (compilador C++)
- Biblioteca Google Generative AI (para correção com IA)
- Bibliotecas Python:
  - `python-dotenv`
  - `google-generativeai`
  - `pdfplumber`

## Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd monitoria-ces11
```

2. Instale as dependências:
```bash
pip install python-dotenv google-generativeai pdfplumber
```

3. Configure a variável de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione sua chave da API do Gemini:
   ```
   GEMINI_API_KEY=sua_chave_aqui
   ```

## Configuração do Laboratório

Para configurar um novo laboratório, edite o arquivo `src/dados_lab.py`:

1. **Configurações básicas**:
   - `compile_timeout`: Timeout para compilação (padrão: 20 segundos)
   - `run_timeout`: Timeout para execução (padrão: 10 segundos)
   - `has_report`: Se o laboratório inclui relatório PDF (padrão: False)

2. **Função de correção**: Implemente `correction_function` para comparar a saída do aluno com o gabarito

3. **Regexes de arrays**: Configure `array_regexes` para extrair valores da saída do aluno

4. **Critérios de correção com IA**: Adicione critérios em `ai_correction_criteria` para a análise com IA

5. **Tipos de saída**: Configure `output_types` se houver múltiplos arquivos de saída

## Uso

### Execução Básica

Execute o script principal (o número do lab é inferido do nome do script):

```bash
python3 lab{N}.py <pasta_alunos> [error_type]
```

Exemplo:
```bash
python3 lab7.py alunos
```

### Opções de Linha de Comando

- `students_path`: Pasta com os alunos a serem corrigidos (obrigatório)
- `-s, --student`: Corrigir apenas um aluno específico
- `-b, --bronco`: Ativa detecção de bronco (correção com IA)
- `-j, --jump_to_student`: Pular para um aluno específico e continuar a partir dele
- `-t, --testcases_folder`: Pasta com os testcases (padrão: "testcases")
- `error_type`: Tipo de erro a corrigir (padrão: "ALL")

### Exemplos de Uso

```bash
# Corrigir todos os alunos
python3 lab7.py alunos

# Corrigir apenas um aluno específico
python3 lab7.py alunos -s "João_Silva"

# Ativar correção com IA (bronco detection)
python3 lab7.py alunos -b

# Corrigir apenas erros de compilação
python3 lab7.py alunos ERRO-COMPILACAO

# Pular para um aluno e continuar a partir dele
python3 lab7.py alunos -j "Maria_Santos"
```

## Tipos de Erros Detectados

O sistema identifica os seguintes tipos de erros:

- **ARQUIVO-NOME-ERRADO**: Arquivo de entrada ou saída com nome incorreto
- **ERRO-COMPILACAO**: Erro na compilação do código
- **FORMATACAO-OUTPUT-ERRADA**: Formatação incorreta da saída
- **ERRO-CASOS-TESTE**: Falha em um ou mais casos de teste
- **NO-ERRORS**: Nenhum erro encontrado

## Estrutura de Pastas Esperada

### Pasta do Laboratório (lab{N}/)

```
lab{N}/
├── testcases/
│   └── <testcase_name>/
│       ├── entrada{N}.txt ou Entrada{N}.txt
│       └── saida{N}.json
├── alunos/
│   └── <student_name>/
│       ├── Lab{N}_<student_name>.cpp
│       ├── Lab{N}_<student_name>.txt (arquivo de saída)
│       └── (opcional) Lab{N}_<student_name>.pdf (relatório)
└── erros-alunos/
    └── <error_type>.txt (gerado automaticamente)
```

### Arquivos dos Alunos

- **Código**: `Lab{N}_<Nome_Aluno>.cpp`
- **Saída**: `Lab{N}_<Nome_Aluno>.txt`
- **Relatório**: `Lab{N}_<Nome_Aluno>.pdf` (opcional)

Os arquivos de saída são processados e movidos para a pasta `outputs/` dentro da pasta de cada aluno.

## Logs Gerados

Para cada aluno, são gerados os seguintes arquivos:

- `logs_correcao_auto.txt`: Logs da correção automática (erros encontrados)
- `logs_correcao_bronco.txt`: Análise detalhada com IA (quando `-b` é usado)
- `outputs/`: Pasta com os arquivos de saída processados

## Scripts Utilitários

A pasta `scripts_utils/` contém scripts auxiliares para:

- Capitalização de nomes de arquivos
- Criação de pastas de alunos
- Correção de extensões
- Substituição de substrings em nomes de arquivos
- Execução isolada de código de alunos
- Debug com Valgrind

## Notas Importantes

1. O sistema assume que o código C++ usa `fopen` com os nomes corretos dos arquivos
2. Os arquivos de entrada devem ter os nomes `entrada{N}.txt` ou `Entrada{N}.txt`
3. O sistema limpa arquivos desnecessários da pasta do aluno após a correção
4. A correção com IA requer uma chave válida da API do Gemini
5. O timeout de execução pode ser ajustado conforme a complexidade dos testcases

## Desenvolvimento

Este sistema foi desenvolvido para uso em monitoria de programação, facilitando a correção automática de laboratórios e fornecendo feedback detalhado aos alunos.

