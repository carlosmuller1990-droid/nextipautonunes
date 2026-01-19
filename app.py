import pandas as pd
import re
import streamlit as st

st.set_page_config(
    page_title="Higienizador de Base - Auto Nunes",
    layout="centered"
)

st.title("📊 Higienização de Base – Auto Nunes")

st.write(
    "O sistema limpa e padroniza telefones dentro dos parâmetros de importação do NextIP"
)

# ================= FUNÇÕES =================

def limpar_telefone(valor):
    if pd.isna(valor):
        return None
    if isinstance(valor, float):
        valor = str(int(valor))
    else:
        valor = str(valor)
    valor = re.sub(r"\D", "", valor)
    return valor if valor else None

def extrair_ddd_numero(tel, ddd_externo=None):
    if not tel:
        return None, None

    if ddd_externo and pd.notna(ddd_externo):
        ddd = re.sub(r"\D", "", str(ddd_externo))[:2]
        numero = tel
    else:
        if len(tel) >= 10:
            ddd = tel[:2]
            numero = tel[2:]
        else:
            return None, None

    if len(numero) == 8:
        numero = "9" + numero

    if len(numero) != 9 or len(ddd) != 2:
        return None, None

    return ddd, numero

# ================= UPLOAD =================

arquivo = st.file_uploader(
    "📂 Envie a planilha (.csv ou .xlsx)",
    type=["csv", "xlsx"]
)

if arquivo:
    try:
        # -------- LEITURA --------
        if arquivo.name.lower().endswith(".csv"):
            df = pd.read_csv(
                arquivo,
                sep=";",
                encoding="utf-8-sig",  # ← já trata BOM
                engine="python",
                on_bad_lines="skip"
            )
        else:
            df = pd.read_excel(arquivo)

        # 🔥 CORREÇÃO DEFINITIVA DO BOM
        df.columns = (
            df.columns
            .astype(str)
            .str.replace("\ufeff", "", regex=False)
            .str.upper()
            .str.strip()
        )

        # -------- DETECÇÃO DE COLUNAS --------
        col_tel = next(
            (c for c in df.columns if any(p in c for p in ["TELEFONE", "TEL", "FONE", "CELULAR"])),
            None
        )

        if not col_tel:
            st.error("❌ Nenhuma coluna de telefone encontrada.")
            st.stop()

        col_ddd = next(
            (c for c in df.columns if any(p in c for p in ["DDD", "CODIGO AREA", "ÁREA", "CODAREA"])),
            None
        )

        col_nome = next(
            (c for c in df.columns if c.startswith("NOME")),
            None
        )

        # -------- PRIMEIRO NOME (CAPTURA REAL) --------
        if col_nome:
            primeiro_nome = (
                df[col_nome]
                .astype(str)
                .str.strip()
                .str.split()
                .str[0]
            )
        else:
            primeiro_nome = ""

        # -------- TELEFONE --------
        df["TEL_LIMPO"] = df[col_tel].apply(limpar_telefone)

        if col_ddd:
            resultados = df.apply(
                lambda r: extrair_ddd_numero(r["TEL_LIMPO"], r[col_ddd]),
                axis=1
            )
        else:
            resultados = df["TEL_LIMPO"].apply(extrair_ddd_numero)

        ddds, numeros = zip(*resultados)
        df["FONE1_DD"] = ddds
        df["FONE1_NR"] = numeros

        df = df.dropna(subset=["FONE1_NR"]).reset_index(drop=True)

        # -------- IDS --------
        df["ID1"] = range(10, 10 + len(df))
        df["ID2"] = df["ID1"]

        # ✅ CAMPO01 FINAL E CORRETO
        df["CAMPO01"] = primeiro_nome.iloc[df.index] if col_nome else ""

        # -------- CAMPOS FIXOS --------
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

        for c in colunas_finais:
            if c not in df:
                df[c] = ""

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
