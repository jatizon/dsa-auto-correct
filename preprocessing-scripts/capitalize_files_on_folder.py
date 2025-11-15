#!/usr/bin/env python3
import os
import sys
import re

# Verifica argumento
if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <folder>")
    sys.exit(1)

dir_path = sys.argv[1]

# Verifica se é diretório
if not os.path.isdir(dir_path):
    print(f"Error: '{dir_path}' is not a directory")
    sys.exit(1)

# Itera sobre todos os arquivos
for filename in os.listdir(dir_path):
    file_path = os.path.join(dir_path, filename)

    name, ext = os.path.splitext(filename)

    # Capitaliza letras após '_'
    new_name = re.sub(r'_([a-z])', lambda m: '_' + m.group(1).upper(), name)

    # Reanexa extensão
    new_file = new_name + ext

    # Renomeia se diferente
    if new_file != filename:
        new_file_path = os.path.join(dir_path, new_file)
        os.rename(file_path, new_file_path)
        print(f"Renamed: '{filename}' → '{new_file}'")
