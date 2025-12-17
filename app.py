import pandas as pd
import re
import streamlit as st

st.set_page_config(
    page_title="Higienizador de Base - Nextip Auto Nunes",
    layout="centered"
)

st.title("📊 Higienização de Base – Auto Nunes")
st.write("Faça upload da planilha (.xlsx). O sistema irá apenas limpar e padronizar os telefones.")

# -----------------------------
# Funções
# -----------------------------
def limpar_telefone(valor):
    if pd.isna(valor):
        return None

    # Trata float vindo do Excel
    if isinstance(valor, float):
        valor = str(int(valor))
    else:
        valor = str(valor)

    # Remove tudo que não é número
    valor = re.sub(r"\D", "", valor)

    # Remove zero extra no início (ex: 0819...)
    if valor.startswith("0") and len(valor) >= 11:
        valor = valor[1:]

    return valor


def extrair_ddd_numero(tel):
    if not tel:
        return None, None

    # Caso venha com DDD
    if len(tel) >= 10:
        ddd = tel[:2]
        numero = tel[2:]
    else:
        # Sem DDD não descarta — apenas invalida
        return None, None

    # Remove fixos comerciais
    if numero.startswith("3"):
        return None, None

    # Ajusta celular antigo
    if len(numero) == 8:
        numero = "9" + numero

    # Validação final mínima
    if len(numero) != 9:
        return None, None

    return ddd, numero


# -----------------------------
# Upload
# -----------------------------
arquivo = st.file_uploader("📂 Envie a planilha (.xlsx)", type=["xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo)
        df.columns = df.columns.str.upper().str.strip()

        # Identificar coluna telefone
        possiveis = ["TELEFONE", "TEL", "FONE", "CELULAR"]
        col_tel = next((c for c in df.columns if any(p in c for p in possiveis)), None)

        if not col_tel:
            st.error("❌ Nenhuma coluna de telefone encontrada.")
            st.stop()

        # Identificar coluna nome (opcional)
        col_nome = next((c for c in df.columns if "NOME" in c), None)

        # Limpeza
        df["TEL_LIMPO"] = df[col_tel].apply(limpar_telefone)
        df["FONE1_DD"], df["FONE1_NR"] = zip(*df["TEL_LIMPO"].apply(extrair_ddd_numero))

        # Remove apenas inválidos reais
        df = df.dropna(subset=["FONE1_DD", "FONE1_NR"])

        # IDs
        df["ID1"] = range(10, 10 + len(df))
        df["ID2"] = df["ID1"]

        # Primeiro nome (se existir)
        if col_nome:
            df["CAMPO01"] = df[col_nome].astype(str).str.split().str[0]
        else:
            df["CAMPO01"] = ""

        # Campos fixos
        df["FONE1_DISCAR EM"] = ""
        df["FONE1_DISCAR AGORA"] = "S"

        colunas_finais = [
            "ID1","ID2",
            "FONE1_DD","FONE1_NR","FONE1_DISCAR EM","FONE1_DISCAR AGORA",
            "FONE2_DD","FONE2_NR","FONE2_DISCAR EM","FONE2_DISCAR AGORA",
            "FONE3_DD","FONE3_NR","FONE3_DISCAR EM","FONE3_DISCAR AGORA",
            "FONE4_DD","FONE4_NR","FONE4_DISCAR EM","FONE4_DISCAR AGORA",
            "FONE5_DD","FONE5_NR","FONE5_DISCAR EM","FONE5_DISCAR AGORA",
            "AGENTE","CAMPO01","CAMPO02","CAMPO03","CAMPO04","CAMPO05",
            "CAMPO06","CAMPO07","CAMPO08","CAMPO09","CAMPO10"
        ]

        for col in colunas_finais:
            if col not in df:
                df[col] = ""

        df = df[colunas_finais]

        csv = df.to_csv(sep=";", index=False, encoding="utf-8-sig")

        st.success("✅ Planilha higienizada com sucesso!")

        st.download_button(
            "⬇ Baixar CSV Higienizado",
            csv,
            "planilha_higienizada.csv",
            "text/csv"
        )

        st.dataframe(df.head(10))

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
