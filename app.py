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
    "O sistema apenas limpa, padroniza e remove telefones duplicados dentro dos parâmetros de importação do NextIP"
)

# -----------------------------
# Funções
# -----------------------------
def limpar_telefone(valor):
    if pd.isna(valor):
        return None

    valor = str(valor)
    valor = re.sub(r"\D", "", valor)

    # Remove apenas lixo real
    if len(valor) < 8:
        return None

    return valor


def extrair_ddd_numero(tel):
    if not tel:
        return None, None

    # Com DDD
    if len(tel) >= 10:
        ddd = tel[:2]
        numero = tel[2:]
    else:
        # Sem DDD
        ddd = ""
        numero = tel

    # Ajuste celular antigo
    if len(numero) == 8:
        numero = "9" + numero

    # Trava final segura
    if len(numero) < 9:
        return None, None

    numero = numero[-9:]

    return ddd, numero


# -----------------------------
# Upload
# -----------------------------
arquivo = st.file_uploader("📂 Envie a planilha (.xlsx)", type=["xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo)
        df.columns = df.columns.str.upper().str.strip()

        # Detecta coluna telefone
        possiveis = ["TELEFONE", "TEL", "FONE", "CELULAR"]
        col_tel = next((c for c in df.columns if any(p in c for p in possiveis)), None)

        if not col_tel:
            st.error("❌ Nenhuma coluna de telefone encontrada.")
            st.stop()

        # Detecta coluna nome (opcional)
        col_nome = next((c for c in df.columns if "NOME" in c), None)

        # Higienização
        df["TEL_LIMPO"] = df[col_tel].apply(limpar_telefone)
        df[["FONE1_DD", "FONE1_NR"]] = df["TEL_LIMPO"].apply(
            lambda x: pd.Series(extrair_ddd_numero(x))
        )

        # Remove apenas lixo real
        df = df.dropna(subset=["FONE1_NR"])

        # 🔒 Remove números duplicados (considera o número apenas uma vez)
        df = df.drop_duplicates(subset=["FONE1_NR"])

        # IDs
        df["ID1"] = range(10, 10 + len(df))
        df["ID2"] = df["ID1"]

        # Primeiro nome
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

        st.success(f"✅ Higienização concluída — {len(df)} números únicos e válidos")

        st.download_button(
            "⬇ Baixar CSV Higienizado",
            csv,
            "planilha_higienizada.csv",
            "text/csv"
        )

        st.dataframe(df.head(10))

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
