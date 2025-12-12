#!/usr/bin/env python3
import os
import sys
import re

# Verifica argumentos
if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} <folder> <old_substring> <new_substring>")
    sys.exit(1)

dir_path = sys.argv[1]
old_substr = sys.argv[2]
new_substr = sys.argv[3]

# Verifica se é diretório
if not os.path.isdir(dir_path):
    print(f"Error: '{dir_path}' is not a directory")
    sys.exit(1)

# Itera sobre todos os arquivos
for filename in os.listdir(dir_path):
    file_path = os.path.join(dir_path, filename)

    # Substitui substring no filename inteiro
    new_file = filename.replace(old_substr, new_substr)

    # Capitaliza letras após '_' na parte do nome (antes do último '.')
    parts = new_file.rsplit('.', 1)
    name = re.sub(r'_([a-z])', lambda m: '_' + m.group(1).upper(), parts[0])
    ext = parts[1].lower() if len(parts) == 2 else ''
    new_file = name + ('.' + ext if ext else '')

    # Renomeia se diferente
    if new_file != filename:
        new_file_path = os.path.join(dir_path, new_file)
        if os.path.exists(new_file_path):
            print(f"Arquivo já existe, pulando: {new_file}")
        else:
            os.rename(file_path, new_file_path)
            print(f"Renamed: '{filename}' → '{new_file}'")
