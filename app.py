import pandas as pd
import re
import streamlit as st

st.set_page_config(
    page_title="Higienizador de Base - Auto Nunes",
    layout="centered"
)

st.title("📊 Higienização de Base – Auto Nunes")

# -----------------------------
# Funções
# -----------------------------
def limpar_telefone(valor):
    if pd.isna(valor):
        return ""

    valor = str(valor)

    if re.match(r"^\d+\.0$", valor):
        valor = valor.replace(".0", "")
    elif re.match(r"^\d+\.\d+$", valor):
        valor = str(int(float(valor)))

    return re.sub(r"\D", "", valor)


def validar_telefone(ddd, num):
    if not ddd or not num:
        return None, None

    if not ddd.isdigit() or len(ddd) != 2:
        return None, None

    if num.startswith("3"):
        return None, None

    if len(num) == 8:
        num = "9" + num

    if len(num) != 9:
        return None, None

    return ddd, num


def extrair_do_telefone(tel):
    if not tel or len(tel) < 10:
        return None, None

    return tel[:2], tel[2:]

# -----------------------------
# Upload
# -----------------------------
arquivo = st.file_uploader("📂 Envie a planilha (.xlsx)", type=["xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo)
        df.columns = df.columns.str.upper().str.strip()

        col_nome = next((c for c in df.columns if "NOME" in c), None)

        col_ddd = next((c for c in df.columns if c == "ddd"), None)

        possiveis_tel = ["TELEFONE", "TEL", "FONE", "CELULAR"]
        col_tel = next((c for c in df.columns if any(p in c for p in possiveis_tel)), None)

        if not col_tel:
            st.error("❌ Nenhuma coluna de telefone encontrada.")
            st.stop()

        df["TEL_LIMPO"] = df[col_tel].apply(limpar_telefone)

        novos_ddds = []
        novos_nums = []

        for _, row in df.iterrows():
            tel = row["TEL_LIMPO"]

            ddd_raw = ""
            num_raw = ""

            # 👉 PRIORIDADE: coluna DDD
            if col_ddd:
                ddd_raw = limpar_telefone(row[col_ddd])
                num_raw = tel
            else:
                ddd_raw, num_raw = extrair_do_telefone(tel)

            ddd, num = validar_telefone(ddd_raw, num_raw)

            novos_ddds.append(ddd)
            novos_nums.append(num)

        df["FONE1_DD"] = novos_ddds
        df["FONE1_NR"] = novos_nums

        # ❗ REGRA CRÍTICA
        df = df.dropna(subset=["FONE1_DD", "FONE1_NR"])

        # -----------------------------
        # IDs
        # -----------------------------
        df["ID1"] = range(10, 10 + len(df))
        df["ID2"] = df["ID1"]

        if col_nome:
            df["CAMPO01"] = df[col_nome].astype(str).str.split().str[0]
        else:
            df["CAMPO01"] = ""

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

        st.success(f"✅ Higienização concluída — {len(df)} números válidos")

        st.download_button(
            "⬇ Baixar CSV Higienizado",
            csv,
            "planilha_higienizada.csv",
            "text/csv"
        )

        st.dataframe(df.head(10))

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
