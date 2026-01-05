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
        # Para números como 999888777.0
        if valor.is_integer():
            valor = str(int(valor))
        else:
            valor = str(valor)
    else:
        valor = str(valor)

    valor = re.sub(r"\D", "", valor)

    if valor == "":
        return None

    return valor

def validar_telefone(ddd, numero):
    """Valida DDD e número conforme regras do primeiro código"""
    if not numero:
        return None, None
    
    # Se não tem DDD mas tem número válido, tentar extrair do número
    if not ddd and numero:
        if len(numero) >= 10:
            ddd = numero[:2]
            numero = numero[2:]

    # Se ainda não tem DDD, retornar None
    if not ddd:
        return None, None

    # excluir números que começam com 3
    if numero and numero.startswith("3"):
        return None, None

    # adicionar 9 se tiver 8 dígitos
    if numero and len(numero) == 8:
        numero = "9" + numero

    # Verificar se o número tem 9 dígitos
    if numero and len(numero) != 9:
        return None, None

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
        possiveis_tel = ["TELEFONE", "TEL", "FONE", "CELULAR", "CEL", "CONTATO", "NUMERO", "NÚMERO", "WHATSAPP"]
        col_tel = next((c for c in df.columns if any(p in c for p in possiveis_tel)), None)
        
        # Buscar coluna DDD (verificar nomes comuns)
        possiveis_ddd = ["DDD", "CODIGO AREA", "ÁREA", "CODAREA", "COD AREA", "COD. AREA", "COD", "AREA"]
        col_ddd = None
        
        # Verificar cada possível nome de DDD
        for col in df.columns:
            col_upper = col.upper()
            for possivel in possiveis_ddd:
                if possivel in col_upper:
                    col_ddd = col
                    break
            if col_ddd:
                break
        
        # Se não encontrou, verificar se tem exatamente "DDD"
        if not col_ddd and "DDD" in df.columns:
            col_ddd = "DDD"
        # -----------------------------------------------------------

        col_nome = next((c for c in df.columns if "NOME" in c), None)
   
        if not col_tel:
            st.error("❌ Nenhuma coluna de telefone encontrada.")
            st.error(f"Colunas disponíveis: {', '.join(colunas_originais)}")
            st.stop()

        # Mostrar quais colunas foram identificadas
        st.info(f"🔍 **Colunas identificadas:**")
        st.info(f"- Telefone: `{col_tel}`")
        st.info(f"- DDD: `{col_ddd if col_ddd else 'Não encontrada'}`")
        st.info(f"- Nome: `{col_nome if col_nome else 'Não encontrada'}`")

        # Limpar telefone
        df["TEL_LIMPO"] = df[col_tel].apply(limpar_telefone)
        
        # Lógica para tratar DDD separado vs. junto
        # -----------------------------------------------------------
        novos_ddds = []
        novos_numeros = []
        
        linhas_processadas = []
        
        for idx, row in df.iterrows():
            ddd_raw = ""
            numero = row["TEL_LIMPO"]
            
            # Se tiver coluna DDD separada, usar ela
            if col_ddd and col_ddd in df.columns:
                ddd_val = row[col_ddd]
                if pd.notna(ddd_val):
                    ddd_raw = str(ddd_val)
                    # Limpar o DDD
                    ddd_raw = re.sub(r"\D", "", ddd_raw)
                    
                    # Se DDD estiver vazio mas temos telefone com DDD incluso
                    if not ddd_raw and numero and len(numero) >= 10:
                        ddd_raw = numero[:2]
                        numero = numero[2:]
            else:
                # Se não tiver coluna DDD, extrair do telefone
                if numero and len(numero) >= 10:
                    ddd_raw = numero[:2]
                    numero = numero[2:]
            
            # Validar
            ddd_final, numero_final = validar_telefone(ddd_raw, numero)
            
            novos_ddds.append(ddd_final)
            novos_numeros.append(numero_final)
            
            # Guardar para debug (opcional)
            linhas_processadas.append({
                "original_ddd": row[col_ddd] if col_ddd and col_ddd in df.columns else "",
                "ddd_limpo": ddd_raw,
                "ddd_final": ddd_final,
                "numero_final": numero_final
            })
        
        # Atribuir os resultados às colunas
        df["FONE1_DD"] = novos_ddds
        df["FONE1_NR"] = novos_numeros
        
        # Remover coluna temporária
        df = df.drop(columns=["TEL_LIMPO"], errors="ignore")
        # -----------------------------------------------------------

        # Mostrar estatísticas antes de filtrar
        total_linhas = len(df)
        linhas_validas = df["FONE1_NR"].notna().sum()
        linhas_com_ddd = df["FONE1_DD"].notna().sum()
        
        st.info(f"📊 **Estatísticas de processamento:**")
        st.info(f"- Total de linhas: {total_linhas}")
        st.info(f"- Linhas com número válido: {linhas_validas}")
        st.info(f"- Linhas com DDD válido: {linhas_com_ddd}")

        # Remover linhas onde não há número válido
        df_original_len = len(df)
        df = df.dropna(subset=["FONE1_NR"])
        df_filtrado_len = len(df)
        
        st.warning(f"⚠️ Foram removidas {df_original_len - df_filtrado_len} linhas sem número válido")

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
            if col not in df.columns:
                df[col] = ""

        df = df[colunas_finais]

        # Mostrar amostra dos dados
        st.subheader("🔍 **Amostra dos dados processados (primeiras 10 linhas):**")
        
        # Criar visualização compacta
        colunas_vis = []
        if "CAMPO01" in df.columns:
            colunas_vis.append("CAMPO01")
        colunas_vis.extend(["FONE1_DD", "FONE1_NR"])
        
        # Formatar para melhor visualização
        df_display = df[colunas_vis].head(10).copy()
        df_display["FONE1_NR"] = df_display["FONE1_NR"].apply(lambda x: f"{x[:5]}-{x[5:]}" if pd.notna(x) and len(str(x)) == 9 else x)
        
        st.dataframe(df_display)

        # Verificar se a coluna FONE1_DD está vazia
        if df["FONE1_DD"].isna().all() or df["FONE1_DD"].eq("").all():
            st.error("🚨 ATENÇÃO: A coluna FONE1_DD está vazia para todas as linhas!")
            st.error("Possíveis causas:")
            st.error("1. A coluna DDD não foi encontrada na planilha original")
            st.error("2. Os números de telefone não incluem DDD")
            st.error("3. O DDD não está no formato correto (apenas 2 dígitos)")
            
            # Mostrar debug das primeiras linhas
            st.subheader("🔧 Debug das primeiras 5 linhas:")
            debug_df = pd.DataFrame(linhas_processadas[:5])
            st.dataframe(debug_df)

        csv = df.to_csv(sep=";", index=False, encoding="utf-8-sig")

        st.success(f"✅ Higienização concluída — {len(df)} números válidos")

        st.download_button(
            "⬇ Baixar CSV Higienizado",
            csv,
            "planilha_higienizada.csv",
            "text/csv"
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        import traceback
        st.error(f"Detalhes do erro: {traceback.format_exc()}")
