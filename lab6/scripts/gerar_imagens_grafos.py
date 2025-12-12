import os
import networkx as nx
import re
import pygraphviz as pgv

# Pastas
input_base = "lab6/testcases_sem_ciclo"
# input_base = "lab6/testcases_ciclo"
# input_base = "lab6/testcases_especiais"

output_base = "lab6/testcases_grafo_imagens/"
os.makedirs(output_base, exist_ok=True)

# Ler tarefas
def ler_tarefas(file_path):
    tasks = {}
    ordem = {}    # <-- NOVO: dict para guardar a ordem de aparição

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    index = 1
    for line in lines:
        if not line.strip() or "----" in line:
            continue
        match = re.match(r"\s*(\w+)\s+.*?\s+(\d+)\s+([A-Za-z,\.]*)", line)
        if match:
            tarefa = match.group(1)
            duracao = int(match.group(2))
            predecessores_raw = match.group(3).replace(".", "").split(",")
            predecessores = [p.strip() for p in predecessores_raw if p.strip()]

            tasks[tarefa] = (duracao, predecessores)
            ordem[tarefa] = index   # <--- salva ordem de aparição
            index += 1

    return tasks, ordem

# Gerar grafo com Graphviz
def gerar_grafo(tasks, ordem, output_file):
    G = nx.DiGraph()
    
    # Adicionar nós com label = ordem + nome + duração
    for task, (duration, _) in tasks.items():
        num = ordem[task]
        G.add_node(task, label=f"{num}: {task}\n({duration})")
    
    # Adicionar arestas
    for task, (_, predecessors) in tasks.items():
        for pred in predecessors:
            if pred in tasks:
                G.add_edge(pred, task)
    
    # Converter para AGraph do pygraphviz
    A = nx.nx_agraph.to_agraph(G)
    
    # Configurar layout hierárquico
    A.graph_attr.update(rankdir='TB', nodesep='0.8', ranksep='1.2')
    A.node_attr.update(shape='box', style='filled', fillcolor='lightblue', fontsize='12')
    A.edge_attr.update(arrowsize='1.2')
    
    # Gerar imagem
    A.draw(output_file, prog='dot')
    print(f"Grafo salvo em: {output_file}")

# Iterar sobre testcases
for folder in os.listdir(input_base):
    folder_path = os.path.join(input_base, folder)
    if os.path.isdir(folder_path):
        input_file = os.path.join(folder_path, "entrada6.txt")
        if os.path.exists(input_file):
            tasks, ordem = ler_tarefas(input_file)
            output_file = os.path.join(output_base, f"{folder}.png")
            gerar_grafo(tasks, ordem, output_file)
