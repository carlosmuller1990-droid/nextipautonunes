import pandas as pd
import re
import streamlit as st

# -----------------------------
# Configuração da página
# -----------------------------
st.set_page_config(
    page_title="Higienizador de Base - Auto Nunes",
    layout="centered"
)

st.title("📊 Higienização de Base – Auto Nunes")

st.write(
    "O sistema limpa e padroniza telefones seguindo rigorosamente "
    "os parâmetros de importação do NextIP."
)

# -----------------------------
# Funções de higienização
# -----------------------------
def limpar_telefone(num):
    if pd.isna(num):
        return ""

    num_str = str(num).strip()

    # Caso venha como float do Excel
    if re.match(r"^\d+\.0$", num_str):
        num_str = num_str.replace(".0", "")
    elif re.match(r"^\d+\.\d+$", num_str):
        num_str = str(int(float(num_str)))

    # Remove tudo que não é número
    return re.sub(r"\D", "", num_str)


def validar_telefone(ddd, num):
    if not ddd or not num:
        return None, None

    # DDD deve ter exatamente 2 dígitos
    if not ddd.isdigit() or len(ddd) != 2:
        return None, None

    # Excluir números que começam com 3 (fixos/corporativos)
    if num.startswith("3"):
        return None, None

    # Se tiver 8 dígitos, adiciona o 9
    if len(num) == 8:
        num = "9" + num

    # Celular deve ter exatamente 9 dígitos
    if len(num) != 9:
        return None, None

    return ddd, num


def extrair_ddd_numero(tel):
    if not tel or len(tel) < 10:
        return None, None

    ddd = tel[:2]
    numero = tel[2:]

    return validar_telefone(ddd, numero)

# -----------------------------
# Upload do arquivo
# -----------------------------
arquivo = st.file_uploader("📂 Envie a planilha (.xlsx)", type=["xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo)
        df.columns = df.columns.str.upper().str.strip()

        # -----------------------------
        # Detectar colunas
        # -----------------------------
        col_nome = next((c for c in df.columns if "NOME" in c), None)

        possiveis_tel = ["TELEFONE", "TEL", "FONE", "CELULAR"]
        col_tel = next(
            (c for c in df.columns if any(p in c for p in possiveis_tel)),
            None
        )

        if not col_tel:
            st.error("❌ Nenhuma coluna de telefone encontrada.")
            st.stop()

        # -----------------------------
        # Processar telefones
        # -----------------------------
        df["TEL_LIMPO"] = df[col_tel].apply(limpar_telefone)
        df["FONE1_DD"], df["FONE1_NR"] = zip(
            *df["TEL_LIMPO"].apply(extrair_ddd_numero)
        )

        # ❗ REMOVE QUALQUER REGISTRO SEM DDD OU NÚMERO
        df = df.dropna(subset=["FONE1_DD", "FONE1_NR"])

        # -----------------------------
        # IDs sequenciais
        # -----------------------------
        df["ID1"] = range(10, 10 + len(df))
        df["ID2"] = df["ID1"]

        # -----------------------------
        # Primeiro nome
        # -----------------------------
        if col_nome:
            df["CAMPO01"] = df[col_nome].astype(str).str.split().str[0]
        else:
            df["CAMPO01"] = ""

        # -----------------------------
        # Campos fixos
        # -----------------------------
        df["FONE1_DISCAR EM"] = ""
        df["FONE1_DISCAR AGORA"] = "S"

        # -----------------------------
        # Colunas finais
        # -----------------------------
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

        # -----------------------------
        # Exportar CSV
        # -----------------------------
        csv = df.to_csv(
            sep=";",
            index=False,
            encoding="utf-8-sig"
        )

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
