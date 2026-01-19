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

st.markdown(
    "Para o arquivo ser reconhecido, a planilha deve estar salva no formato **CSV** e seguir um dos padrões abaixo:\n\n"
    "- **3 colunas**: `nome`, `ddd`, `telefone`\n"
    "- **2 colunas** (DDD junto ao número): `nome`, `telefone`\n\n"
    "**Exemplo abaixo:**"
)

st.image(
    "https://github.com/carlosmuller1990-droid/nextipautonunes/blob/main/exemplo_planilha.png?raw=true",
    caption="Exemplo de planilha no formato correto",
    use_column_width=True
)

st.markdown(
    "<div style='text-align:center; font-size:13px; opacity:0.7;'>"
    "Programa desenvolvido pelo supervisor do BDC <strong>Carlos Junior</strong> - Autonunes"
    "</div>",
    unsafe_allow_html=True
)

def limpar_telefone(valor):
    if pd.isna(valor):
        return None

    if isinstance(valor, float):
        valor = str(int(valor))
    else:
        valor = str(valor)

    valor = re.sub(r"\D", "", valor)

    if valor == "":
        return None

    return valor

def extrair_ddd_numero(tel, ddd_externo=None):
    if not tel:
        return None, None
    
    if ddd_externo and pd.notna(ddd_externo):
        ddd = str(ddd_externo)
        ddd = re.sub(r"\D", "", ddd)[:2] if ddd else ""
        numero = tel
    else:
        if len(tel) >= 10:
            ddd = tel[:2]
            numero = tel[2:]
        else:
            ddd = ""
            numero = tel
    
    if len(numero) == 8:
        numero = "9" + numero

    if len(numero) != 9:
        return None, None
    
    if ddd and len(ddd) < 2:
        ddd = None

    return ddd, numero

arquivo = st.file_uploader(
    "📂 Envie a planilha (.csv ou .xlsx)",
    type=["csv", "xlsx"]
)

if arquivo:
    try:
        nome_arquivo = arquivo.name.lower()

        if nome_arquivo.endswith(".csv"):
            df = pd.read_csv(
                arquivo,
                sep=";",
                encoding="latin1",
                engine="python",
                on_bad_lines="skip"
            )
        else:
            df = pd.read_excel(arquivo)

        df.columns = df.columns.str.upper().str.strip()

        possiveis_tel = ["TELEFONE", "TEL", "FONE", "CELULAR"]
        col_tel = next((c for c in df.columns if any(p in c for p in possiveis_tel)), None)

        if not col_tel:
            st.error("❌ Nenhuma coluna de telefone encontrada.")
            st.stop()

        possiveis_ddd = ["DDD", "CODIGO AREA", "ÁREA", "CODAREA"]
        col_ddd = next((c for c in df.columns if any(p in c for p in possiveis_ddd)), None)

        # 🔧 CORREÇÃO APLICADA AQUI
        col_nome = next((c for c in df.columns if c.strip().upper().startswith("NOME")), None)

        st.info(f"🔍 Coluna de telefone encontrada: `{col_tel}`")
        if col_ddd:
            st.info(f"🔍 Coluna de DDD encontrada: `{col_ddd}`")
        if col_nome:
            st.info(f"🔍 Coluna de nome encontrada: `{col_nome}`")

        df["TEL_LIMPO"] = df[col_tel].apply(limpar_telefone)

        if col_ddd:
            resultados = df.apply(
                lambda row: extrair_ddd_numero(row["TEL_LIMPO"], row[col_ddd]),
                axis=1
            )
        else:
            resultados = df["TEL_LIMPO"].apply(extrair_ddd_numero)

        ddds, numeros = zip(*resultados)
        df["FONE1_DD"] = ddds
        df["FONE1_NR"] = numeros

        df = df.dropna(subset=["FONE1_NR"])

        df["ID1"] = range(10, 10 + len(df))
        df["ID2"] = df["ID1"]

        # ✅ CAMPO01 corretamente preenchido com o PRIMEIRO NOME
        if col_nome:
            df["CAMPO01"] = df[col_nome].astype(str).str.strip().str.split().str[0]
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
