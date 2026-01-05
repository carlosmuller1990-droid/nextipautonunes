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

def validar_telefone(ddd, numero):
    """Valida DDD e número conforme regras do primeiro código"""
    if not numero or not ddd:
        return None, None

    # excluir números que começam com 3
    if numero.startswith("3"):
        return None, None

    # adicionar 9 se tiver 8 dígitos
    if len(numero) == 8:
        numero = "9" + numero

    return ddd, numero

arquivo = st.file_uploader("📂 Envie a planilha (.xlsx)", type=["xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo)
        
        # Guardar os nomes originais das colunas para exibição
        colunas_originais = df.columns.tolist()
        
        # Converter nomes das colunas para maiúsculo para padronizar busca
        df.columns = df.columns.str.upper().str.strip()

        # Buscar colunas (agora buscando em maiúsculo)
        # -----------------------------------------------------------
        possiveis_tel = ["TELEFONE", "TEL", "FONE", "CELULAR", "CEL", "CONTATO", "NUMERO", "NÚMERO"]
        col_tel = next((c for c in df.columns if any(p in c for p in possiveis_tel)), None)
        
        # Buscar coluna DDD (verificar nomes comuns)
        # Agora buscando diretamente por DDD em maiúsculo após conversão
        possiveis_ddd = ["DDD", "CODIGO AREA", "ÁREA", "CODAREA", "COD AREA", "COD. AREA"]
        col_ddd = next((c for c in df.columns if any(p in c for p in possiveis_ddd)), None)
        
        # Buscar também se existe exatamente "DDD" (maiúsculo após conversão)
        if "DDD" in df.columns:
            col_ddd = "DDD"
        # -----------------------------------------------------------

        col_nome = next((c for c in df.columns if "NOME" in c), None)
   
        if not col_tel:
            st.error("❌ Nenhuma coluna de telefone encontrada.")
            st.error(f"Colunas disponíveis: {', '.join(colunas_originais)}")
            st.stop()

        # Limpar telefone
        df["TEL_LIMPO"] = df[col_tel].apply(limpar_telefone)
        
        # Lógica para tratar DDD separado vs. junto
        # -----------------------------------------------------------
        novos_ddds = []
        novos_numeros = []
        
        for _, row in df.iterrows():
            # Se tiver coluna DDD separada, usar ela
            if col_ddd:
                # Limpar o DDD: remover .0, espaços, e garantir que seja string
                ddd_raw = str(row[col_ddd])
                
                # Remover .0 do Excel (formato float)
                if re.match(r"^\d+\.0$", ddd_raw):
                    ddd_raw = ddd_raw.replace(".0", "")
                
                # Remover tudo que não é número
                ddd_raw = re.sub(r"\D", "", ddd_raw)
                
                numero = row["TEL_LIMPO"]
            else:
                # Se não tiver coluna DDD, extrair do telefone
                ddd_raw = ""
                numero = row["TEL_LIMPO"]
                if numero and len(numero) >= 10:
                    ddd_raw = numero[:2]
                    numero = numero[2:]
            
            # Validar (igual ao primeiro código)
            ddd, numero_validado = validar_telefone(ddd_raw, numero)
            novos_ddds.append(ddd)
            novos_numeros.append(numero_validado)
        
        df["FONE1_DD"] = novos_ddds
        df["FONE1_NR"] = novos_numeros
        # -----------------------------------------------------------

        # Remover linhas onde não há número válido
        df = df.dropna(subset=["FONE1_NR"])

        # IDs
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
        
        # Mostrar estatísticas detalhadas
        st.info(f"📊 **Estatísticas de importação:**")
        st.info(f"- Colunas encontradas na planilha: {', '.join(colunas_originais)}")
        st.info(f"- Coluna de telefone identificada: `{col_tel}`")
        st.info(f"- Coluna de DDD identificada: `{col_ddd if col_ddd else 'Nenhuma (DDD extraído do telefone)'}`")
        st.info(f"- Coluna de nome identificada: `{col_nome if col_nome else 'Nenhuma'}`")
        
        # Mostrar amostra dos dados processados
        st.subheader("📋 Amostra dos dados processados:")
        
        # Criar um DataFrame de visualização com as colunas relevantes
        if col_nome:
            colunas_vis = ["CAMPO01", "FONE1_DD", "FONE1_NR"]
        else:
            colunas_vis = ["FONE1_DD", "FONE1_NR"]
            
        st.dataframe(df[colunas_vis].head(10))

        st.download_button(
            "⬇ Baixar CSV Higienizado",
            csv,
            "planilha_higienizada.csv",
            "text/csv"
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        st.error("Por favor, verifique se o arquivo está no formato correto.")
