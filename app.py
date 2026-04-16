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
    use_container_width=True
)

st.markdown(
    "<div style='text-align:center; font-size:13px; opacity:0.7;'>"
    "Programa desenvolvido pelo supervisor do BDC <strong>Carlos Junior</strong> - Autonunes"
    "</div>",
    unsafe_allow_html=True
)

# ---------------------------------------
# FUNÇÃO DE LIMPEZA
# ---------------------------------------
def limpar_telefone(tel):
    if pd.isna(tel):
        return None, None

    tel = str(tel).strip()

    if tel == "" or tel.lower() == "nan":
        return None, None

    tel = re.sub(r"\D", "", tel)

    if tel == "":
        return None, None

    if len(tel) > 11 and tel.startswith("0"):
        tel = tel[1:]

    if len(tel) < 10:
        return None, None

    ddd = tel[:2]
    numero = tel[2:]

    if numero.startswith("3"):
        return None, None

    if len(numero) == 8:
        numero = "9" + numero

    if len(numero) != 9:
        return None, None

    return ddd, numero


arquivo = st.file_uploader("📂 Envie a planilha (.xlsx)", type=["xlsx"])

if arquivo:
    try:
        # Lê como texto para evitar float/NaN quebrando o processamento
        df = pd.read_excel(arquivo, dtype=str, engine="openpyxl")
        df = df.fillna("")

        # padroniza cabeçalhos
        df.columns = df.columns.astype(str).str.upper().str.strip()

        # ---------------------------------------
        # DETECTAR COLUNAS
        # ---------------------------------------
        col_nome = next((c for c in df.columns if "NOME" in c), None)
        if not col_nome:
            st.error("❌ Nenhuma coluna de nome encontrada!")
            st.stop()

        possiveis = ["TELEFONE", "TEL", "FONE", "CEL", "CELULAR"]
        col_tel = next((c for c in df.columns if any(p in c for p in possiveis)), None)
        if not col_tel:
            st.error("❌ Nenhuma coluna de telefone encontrada!")
            st.stop()

        col_ddd = next((c for c in df.columns if c == "DDD" or "DDD" in c), None)

        st.info(f"🔍 Coluna de telefone encontrada: `{col_tel}`")
        if col_ddd:
            st.info(f"🔍 Coluna de DDD encontrada: `{col_ddd}`")
        if col_nome:
            st.info(f"🔍 Coluna de nome encontrada: `{col_nome}`")

        # remove linhas realmente vazias no telefone
        df = df[df[col_tel].astype(str).str.strip() != ""].copy()

        # ---------------------------------------
        # PROCESSAR TELEFONES
        # ---------------------------------------
        new_ddds = []
        new_nums = []

        for _, row in df.iterrows():
            valor_tel = row[col_tel] if col_tel in row else ""
            valor_ddd = row[col_ddd] if col_ddd and col_ddd in row else ""

            valor_tel = "" if pd.isna(valor_tel) else str(valor_tel).strip()
            valor_ddd = "" if pd.isna(valor_ddd) else str(valor_ddd).strip()

            # mantém a lógica do código que funciona no VSCode
            tel_completo = (valor_ddd + valor_tel) if col_ddd else valor_tel

            ddd, numero = limpar_telefone(tel_completo)
            new_ddds.append(ddd)
            new_nums.append(numero)

        df["FONE1_DD"] = new_ddds
        df["FONE1_NR"] = new_nums

        df = df.dropna(subset=["FONE1_DD", "FONE1_NR"]).copy()

        df = df[
            (df["FONE1_DD"].astype(str).str.strip() != "")
            & (df["FONE1_NR"].astype(str).str.strip() != "")
        ].copy()

        if df.empty:
            st.warning("⚠️ Nenhum número válido encontrado após a higienização.")
            st.stop()

        # ---------------------------------------
        # CAMPOS EXTRAS
        # ---------------------------------------
        df["ID1"] = range(10, 10 + len(df))
        df["ID2"] = df["ID1"]
        df["CAMPO01"] = df[col_nome].astype(str).str.split().str[0]

        df["FONE1_DISCAR EM"] = ""
        df["FONE1_DISCAR AGORA"] = "S"

        extras = [
            "FONE2_DD","FONE2_NR","FONE2_DISCAR EM","FONE2_DISCAR AGORA",
            "FONE3_DD","FONE3_NR","FONE3_DISCAR EM","FONE3_DISCAR AGORA",
            "FONE4_DD","FONE4_NR","FONE4_DISCAR EM","FONE4_DISCAR AGORA",
            "FONE5_DD","FONE5_NR","FONE5_DISCAR EM","FONE5_DISCAR AGORA",
            "AGENTE","CAMPO02","CAMPO03","CAMPO04","CAMPO05",
            "CAMPO06","CAMPO07","CAMPO08","CAMPO09","CAMPO10"
        ]

        for col in extras:
            df[col] = ""

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

        df = df[colunas_finais]

        csv = df.to_csv(sep=";", index=False, encoding="utf-8-sig")

        st.success(f"✅ Higienização concluída — {len(df)} números válidos")

        st.info(f"📊 Estatísticas: {len(df)} registros válidos processados")

        st.download_button(
            "⬇ Baixar CSV Higienizado",
            csv,
            "planilha_higienizada.csv",
            "text/csv"
        )

        st.dataframe(df.head(10), use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
