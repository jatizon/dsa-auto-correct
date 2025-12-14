#!/usr/bin/env python3
import os
import sys
import glob
import shutil
import subprocess

# ------------------------------------------------------------
# Função auxiliar para rodar comandos e salvar logs
# ------------------------------------------------------------
def run_cmd(cmd, cwd=None, log_prefix="log"):
    print(f"\n[CMD] {' '.join(cmd)}")
    
    stdout_file = os.path.join(cwd, f"{log_prefix}_stdout.txt")
    stderr_file = os.path.join(cwd, f"{log_prefix}_stderr.txt")
    
    with open(stdout_file, "w") as out, open(stderr_file, "w") as err:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            stdout=out,
            stderr=err
        )
    
    print(f"[INFO] stdout salvo em: {stdout_file}")
    print(f"[INFO] stderr salvo em: {stderr_file}")
    return result

# ------------------------------------------------------------
# Script principal
# ------------------------------------------------------------
def main():
    if len(sys.argv) != 6:
        print("Uso: python3 run_normal.py <lab_root> <folder_alunos> <nome_aluno> <testcase_folder> <testcase>")
        sys.exit(1)

    lab_root, folder_alunos, nome_aluno, testcase_folder, testcase = sys.argv[1:]

    # ------------------------------------------------------------
    # Localizar pasta do aluno
    # ------------------------------------------------------------
    alunos_path = os.path.join(lab_root, folder_alunos)
    if not os.path.isdir(alunos_path):
        print(f"ERRO: pasta de alunos não encontrada: {alunos_path}")
        sys.exit(1)

    matching = sorted([p for p in os.listdir(alunos_path) if p.startswith(nome_aluno)])
    if not matching:
        print(f"ERRO: nenhum aluno encontrado começando com '{nome_aluno}'")
        sys.exit(1)

    aluno_folder = os.path.join(alunos_path, matching[0])
    print(f"Usando pasta do aluno: {aluno_folder}")

    # ------------------------------------------------------------
    # Localizar testcase e copiar entradas
    # ------------------------------------------------------------
    testcase_dir = os.path.join(lab_root, testcase_folder, testcase)
    if not os.path.isdir(testcase_dir):
        print(f"ERRO: testcase não encontrado: {testcase_dir}")
        sys.exit(1)

    print(f"\n=== Copiando arquivos de entrada do testcase '{testcase}' ===")
    for pat in ["entrada*.txt", "Entrada*.txt"]:
        for src in glob.glob(os.path.join(testcase_dir, pat)):
            dst = os.path.join(aluno_folder, os.path.basename(src))
            print(f"Copiando {src} → {dst}")
            shutil.copyfile(src, dst)

    # ------------------------------------------------------------
    # Encontrar .cpp
    # ------------------------------------------------------------
    print("\n=== Procurando arquivo .cpp do aluno ===")
    cpp_files = glob.glob(os.path.join(aluno_folder, "*.cpp"))
    if not cpp_files:
        print("ERRO: nenhum arquivo .cpp encontrado.")
        sys.exit(1)
    if len(cpp_files) > 1:
        print("[AVISO] Mais de um .cpp encontrado, usando o primeiro.")

    cpp_name = os.path.basename(cpp_files[0])
    exe_name = "prog.out"
    print(f"Arquivo usado: {cpp_name}")

    # ------------------------------------------------------------
    # Compilar
    # ------------------------------------------------------------
    print("\n=== Compilando ===")
    compile_cmd = ["g++", "-std=c++17", "-Wall", "-Wextra", "-g", "-O0", cpp_name, "-o", exe_name]
    res = run_cmd(compile_cmd, cwd=aluno_folder, log_prefix="compile")
    if res.returncode != 0:
        print("ERRO: compilação falhou. Cheque compile_stdout.txt e compile_stderr.txt")
        sys.exit(1)

    # ------------------------------------------------------------
    # Rodar programa
    # ------------------------------------------------------------
    print("\n=== Rodando programa ===")
    res = run_cmd(["./prog.out"], cwd=aluno_folder, log_prefix="run")
    if res.returncode != 0:
        print(f"[AVISO] Programa terminou com código {res.returncode}. Cheque run_stdout.txt e run_stderr.txt")

    # ------------------------------------------------------------
    # Limpeza opcional
    # ------------------------------------------------------------
    print("\n=== Limpando arquivos temporários ===")
    for pat in ["entrada*.txt", "Entrada*.txt"]:
        for arq in glob.glob(os.path.join(aluno_folder, pat)):
            try:
                os.remove(arq)
                print(f"Removido: {arq}")
            except Exception as e:
                print(f"Erro ao remover {arq}: {e}")

    exe_path = os.path.join(aluno_folder, exe_name)
    if os.path.exists(exe_path):
        try:
            os.remove(exe_path)
            print(f"Removido: {exe_path}")
        except Exception as e:
            print(f"Erro ao remover executável: {e}")

# ------------------------------------------------------------
# Start
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
