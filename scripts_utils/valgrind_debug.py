#!/usr/bin/env python3
import os
import sys
import glob
import shutil
import subprocess

# ------------------------------------------------------------
# Função auxiliar para rodar comandos e imprimir saída
# ------------------------------------------------------------
def run_cmd(cmd, cwd=None):
    print(f"\n[CMD] {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    print("\n[STDOUT]\n", result.stdout)
    print("\n[STDERR]\n", result.stderr)
    return result

# ------------------------------------------------------------
# Script principal
# ------------------------------------------------------------
def main():
    if len(sys.argv) != 6:
        print("Uso: python3 valgrind_debug.py <lab_root> <folder_alunos> <nome_aluno> <testcase_folder> <testcase>")
        sys.exit(1)

    lab_root = sys.argv[1]             # ex: lab5
    folder_alunos = sys.argv[2]        # ex: labs-alunos-t2
    nome_aluno = sys.argv[3]           # ex: Joao_Da_Silva
    testcase_folder = sys.argv[4]      # ex: testcases
    testcase = sys.argv[5]             # ex: casos_erro

    # Procurar o primeiro folder cujo nome comece com o nome fornecido
    alunos_path = os.path.join(lab_root, folder_alunos)
    if not os.path.isdir(alunos_path):
        print(f"ERRO: pasta de alunos não encontrada: {alunos_path}")
        sys.exit(1)

    matching_alunos = sorted(
        [p for p in os.listdir(alunos_path) if p.startswith(nome_aluno)]
    )
    if not matching_alunos:
        print(f"ERRO: nenhum aluno encontrado que comece com '{nome_aluno}' na pasta {alunos_path}")
        sys.exit(1)

    aluno_folder_name = matching_alunos[0]
    folder_aluno = os.path.join(alunos_path, aluno_folder_name)

    print(f"Usando pasta do aluno: {folder_aluno}")

    if not os.path.isdir(folder_aluno):
        print(f"ERRO: pasta do aluno não encontrada: {folder_aluno}")
        sys.exit(1)

    # pasta do testcase
    testcase_dir = os.path.join(lab_root, testcase_folder, testcase)
    if not os.path.isdir(testcase_dir):
        print(f"ERRO: testcase não existe: {testcase_dir}")
        sys.exit(1)

    print(f"\n=== Copiando arquivos de entrada do testcase '{testcase}' ===")

    # padrões de arquivo
    patterns = ["entrada*.txt", "Entrada*.txt"]

    for pat in patterns:
        for src in glob.glob(os.path.join(testcase_dir, pat)):
            dst = os.path.join(folder_aluno, os.path.basename(src))
            print(f"Copiando {src} → {dst}")
            shutil.copyfile(src, dst)

    # ------------------------------------------------------------
    # Encontrar o arquivo .cpp
    # ------------------------------------------------------------
    print("\n=== Procurando arquivo .cpp do aluno ===")
    cpp_files = glob.glob(os.path.join(folder_aluno, "*.cpp"))

    if not cpp_files:
        print("ERRO: Nenhum .cpp encontrado no folder do aluno.")
        sys.exit(1)

    if len(cpp_files) > 1:
        print("[AVISO] Mais de um .cpp encontrado, usando o primeiro.")

    cpp_path = cpp_files[0]
    exe_path = os.path.join(folder_aluno, "prog.out")

    print(f"CPP encontrado: {cpp_path}")

    # ------------------------------------------------------------
    # Compilar com flags úteis para debugging
    # ------------------------------------------------------------
    print("\n=== Compilando com g++ ===")

    compile_cmd = [
        "g++",
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-Wshadow",
        "-Wconversion",
        "-Wuninitialized",
        "-g",
        "-O0",
        cpp_path,
        "-o", exe_path
    ]

    res = run_cmd(compile_cmd)
    if res.returncode != 0:
        print("ERRO: compilação falhou. Abortando.")
        sys.exit(1)

    # ------------------------------------------------------------
    # Rodar com Valgrind
    # ------------------------------------------------------------
    print("\n=== Rodando com Valgrind ===")

    valgrind_cmd = [
        "valgrind",
        "--leak-check=full",
        "--show-leak-kinds=all",
        "--track-origins=yes",
        "--undef-value-errors=yes",
        "--read-var-info=yes",
        "--error-limit=no",
        "--track-fds=yes",
        "--verbose",
        "./prog.out"
    ]

    run_cmd(valgrind_cmd, cwd=folder_aluno)

    # ------------------------------------------------------------
    # Remover arquivos entrada*.txt do aluno
    # ------------------------------------------------------------
    print("\n=== Removendo arquivos temporarios ===")

    for arq in glob.glob(os.path.join(folder_aluno, "entrada*.txt")):
        try:
            os.remove(arq)
            print(f"Removido: {arq}")
        except Exception as e:
            print(f"Erro ao apagar {arq}: {e}")

    for arq in glob.glob(os.path.join(folder_aluno, "Entrada*.txt")):
        try:
            os.remove(arq)
            print(f"Removido: {arq}")
        except Exception as e:
            print(f"Erro ao apagar {arq}: {e}")

    for arq in glob.glob(os.path.join(folder_aluno, "prog.out")):
        try:
            os.remove(arq)
            print(f"Removido: {arq}")
        except Exception as e:
            print(f"Erro ao apagar {arq}: {e}")


# ------------------------------------------------------------
# Start
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
