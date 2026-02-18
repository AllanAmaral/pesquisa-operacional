import pandas as pd
import gurobipy as gp
from gurobipy import GRB, Model

model = Model("1||Σyj")

model.setParam("TimeLimit", 600) # limite de execução (segundos)

# Dados
df = pd.read_csv("arquivo.csv", sep=";")

jobs = df["job"].to_numpy()
p = df.set_index("job")["pj"].to_dict()
d = df.set_index("job")["dj"].to_dict()

M = 600 # parâmetro Big-M

# Variáveis
C = model.addVars(jobs, vtype=GRB.CONTINUOUS, name="Cj")
X = model.addVars(jobs, jobs, vtype=GRB.BINARY, name="Xjk")
T = model.addVars(jobs, vtype=GRB.CONTINUOUS, name="Tj")
y = model.addVars(jobs, vtype=GRB.BINARY, name="yj")

# Função objetivo
model.setObjective(gp.quicksum(y[j] for j in jobs if j!=0), GRB.MINIMIZE)

# Restrições
# s(1) e s(2): cada job tem exatamente um predecessor e um sucessor
for k in jobs:    
    model.addConstr(gp.quicksum(X[j, k] for j in jobs if j != k) == 1)

for j in jobs:
    model.addConstr(gp.quicksum(X[j, k] for k in jobs if k != j) == 1)

# s(3): restrição de precedência
for j in jobs:
    for k in jobs:
            if j != k and k != 0: # job fictício não pode ser sucessor
                model.addConstr(C[k] >= C[j] - M + (p[k] + M) * X[j, k])

# s(4): não negatividade e fixação do job fictício 0
for j in jobs:
    model.addConstr(C[j] >= 0)

model.addConstr(C[0] == 0) # início da sequência (com job fictício 0)

# s(5): definição do atraso e ativação da variável binária de atraso
for j in jobs:
    if j != 0:
        model.addConstr(T[j] >= C[j] - d[j])

for j in jobs:
    if j!= 0:
        model.addConstr(T[j] <= M * y[j])

# Otimização
model.optimize()

# Impressão dos resultados
if model.Status == GRB.OPTIMAL:
    print("\nJobs que atrasaram e seus atrasos:")
    for j in jobs:
        if j != 0:
            if T[j].X > 0:
                print(f"J{j}, T={T[j].X:.2f}")
    print(f"\nNúmero de jobs atrasados = {model.ObjVal}")

elif model.SolCount > 0:
    print("\nJobs que atrasaram e seus atrasos:")
    for j in jobs:
        if j != 0:
            if T[j].X > 0:
                print(f"J{j}, T={T[j].X:.2f}")
    print("\nO modelo encontrou uma solução viável, mas não foi possível comprovar a otimalidade.")
    print(f"Número de jobs atrasados = {model.ObjVal}")

else:
    print("Nenhuma solução viável encontrada.")

# Referências
# ARENALES, Marcos Nereu et al. *Pesquisa Operacional*. Rio de Janeiro: Elsevier, 2007.
