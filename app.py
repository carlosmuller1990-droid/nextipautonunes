import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog

# Inicializa Tkinter sem janela principal
root = tk.Tk()
root.withdraw()

print("=" * 50)
print("HIGIENIZAÇÃO DE DUPLICATAS EM ARQUIVOS")
print("=" * 50)

# Selecionar arquivo
arquivo = filedialog.askopenfilename(
    title="Selecione o arquivo CSV ou Excel",
    filetypes=[
        ("CSV", "*.csv"),
        ("Excel", "*.xlsx *.xlsm *.xls"),
        ("Todos os arquivos", "*.*")
    ]
)

if not arquivo:
    print("\n❌ Nenhum arquivo selecionado.")
    input("Pressione ENTER para sair...")
    exit()

ext = os.path.splitext(arquivo)[1].lower()

# Leitura do arquivo
try:
    if ext == ".csv":
        # CSV brasileiro problemático
        df = pd.read_csv(
            arquivo,
            sep=None,                 # detecta separador automaticamente
            engine="python",
            encoding="latin1",
            on_bad_lines="skip"
        )
    else:
        # Excel moderno
        df = pd.read_excel(arquivo)

except Exception as e:
    print(f"\n❌ Erro ao ler o arquivo: {e}")
    input("Pressione ENTER para sair...")
    exit()

# Mostrar colunas
print("\nColunas encontradas:")
for c in df.columns:
    print(f"- {c}")

coluna = input("\nDigite o NOME EXATO da coluna de referência: ").strip()

if coluna not in df.columns:
    print("\n❌ Coluna não encontrada.")
    input("Pressione ENTER para sair...")
    exit()

# Higienização
total_antes = len(df)

df_limpo = df.drop_duplicates(subset=[coluna], keep="first")

total_depois = len(df_limpo)
removidos = total_antes - total_depois

# Salvar arquivo
base, _ = os.path.splitext(arquivo)
saida = f"{base}_HIGIENIZADO{ext}"

try:
    if ext == ".csv":
        df_limpo.to_csv(saida, index=False, sep=";", encoding="latin1")
    else:
        df_limpo.to_excel(saida, index=False)
except Exception as e:
    print(f"\n❌ Erro ao salvar o arquivo: {e}")
    input("Pressione ENTER para sair...")
    exit()

print("\n✅ HIGIENIZAÇÃO CONCLUÍDA")
print(f"📊 Registros antes: {total_antes}")
print(f"🗑️ Duplicatas removidas: {removidos}")
print(f"📁 Arquivo salvo em: {saida}")

input("\nPressione ENTER para sair...")
