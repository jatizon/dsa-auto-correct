import os
import glob
import shutil
import argparse

# Parse do argumento da linha de comando
parser = argparse.ArgumentParser(description="Organiza arquivos de alunos em pastas individuais")
parser.add_argument("folder", help="Caminho para a pasta onde estão os arquivos dos alunos")
args = parser.parse_args()

students_path = args.folder

# Cria pastas para cada aluno e move os arquivos .cpp
cpp_files = glob.glob(os.path.join(students_path, "Lab*.cpp"))
for file_path in cpp_files:
    filename = os.path.basename(file_path)
    folder_name = filename[5:].replace('.cpp', '')
    new_folder_path = os.path.join(students_path, folder_name)
    os.makedirs(new_folder_path, exist_ok=True)
    shutil.move(file_path, os.path.join(new_folder_path, filename))

for folder_name in os.listdir(students_path):
    folder_path = os.path.join(students_path, folder_name)
    if os.path.isdir(folder_path):
        # Move outros arquivos relacionados (não .cpp)
        for file_name in os.listdir(students_path):
            file_path = os.path.join(students_path, file_name)
            if os.path.isfile(file_path) and not file_name.endswith('.cpp') and folder_name in file_name:
                shutil.move(file_path, os.path.join(folder_path, file_name))

print(f"Arquivos organizados na pasta: {students_path}")
