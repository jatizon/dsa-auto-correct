#!/usr/bin/env python3
import os

# Diretório alvo (default: atual)
dir_path = os.path.abspath(os.getcwd())

# Ou passar como argumento
# import sys
# dir_path = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()

for filename in os.listdir(dir_path):
    file_path = os.path.join(dir_path, filename)
    
    if not os.path.isfile(file_path):
        continue  # Ignora diretórios

    name, ext = os.path.splitext(filename)
    
    if not ext:
        continue  # Ignora arquivos sem extensão

    lower_ext = ext.lower()
    
    if ext != lower_ext:
        new_file_path = os.path.join(dir_path, name + lower_ext)
        if os.path.exists(new_file_path):
            print(f"Arquivo já existe, pulando: {new_file_path}")
        else:
            os.rename(file_path, new_file_path)
            print(f"Renomeado: {filename} -> {name + lower_ext}")
