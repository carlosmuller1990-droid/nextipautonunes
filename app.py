import pandas as pd
import re
import streamlit as st

st.set_page_config(
    page_title="Higienizador de Base - Auto Nunes",
    layout="centered"
)

st.title("📊 Higienização de Base – Auto Nunes")

def limpar_telefone(valor):
    """Limpa número de telefone, mantendo apenas dígitos"""
    if pd.isna(valor):
        return None
    
    valor = str(valor)
    # Remover .0 do Excel
    if valor.endswith('.0'):
        valor = valor[:-2]
    
    # Manter apenas números
    valor = re.sub(r'\D', '', valor)
    
    return valor if valor else None

arquivo = st.file_uploader("📂 Envie a planilha (.xlsx)", type=["xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo)
        
        st.info(f"📋 **Colunas encontradas na planilha:**")
        st.write(df.columns.tolist())
        
        # Converter nomes para minúsculo para facilitar busca
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        # IDENTIFICAR COLUNAS
        # 1. Encontrar coluna de nome
        nome_cols = [col for col in df.columns if 'NOME' in col]
        col_nome = nome_cols[0] if nome_cols else None
        
        # 2. Encontrar coluna de telefone
        tel_keys = ['TELEFONE', 'TEL', 'FONE', 'CEL', 'CELULAR', 'CONTATO', 'NUMERO', 'NÚMERO']
        tel_cols = []
        for col in df.columns:
            for key in tel_keys:
                if key in col:
                    tel_cols.append(col)
                    break
        col_tel = tel_cols[0] if tel_cols else None
        
        # 3. Encontrar coluna de DDD (IMPORTANTE!)
        ddd_keys = ['DDD', 'CODIGO', 'AREA', 'ÁREA', 'COD']
        ddd_cols = []
        for col in df.columns:
            for key in ddd_keys:
                if key in col:
                    ddd_cols.append(col)
                    break
        col_ddd = ddd_cols[0] if ddd_cols else None
        
        st.success(f"✅ **Colunas identificadas:**")
        st.write(f"- Nome: `{col_nome}`")
        st.write(f"- Telefone: `{col_tel}`")
        st.write(f"- DDD: `{col_ddd}`")
        
        if not col_tel:
            st.error("❌ Coluna de telefone não encontrada!")
            st.stop()
        
        # PROCESSAR DDD E TELEFONE (FONE1_DD e FONE1_NR)
        if col_ddd:
            st.info("🔍 **Processando com DDD separado...**")
            # CASO 1: DDD está em coluna separada
            novos_ddds = []
            novos_numeros = []
            
            for idx, row in df.iterrows():
                # Obter DDD da coluna ddd
                ddd_valor = str(row[col_ddd]) if pd.notna(row[col_ddd]) else ""
                # Limpar DDD
                ddd_limpo = re.sub(r'\D', '', ddd_valor)
                
                # Obter e limpar telefone
                tel_valor = limpar_telefone(row[col_tel])
                
                # Se telefone tiver DDD incluso (mais de 9 dígitos), remover
                if tel_valor and len(tel_valor) >= 10:
                    # Se já temos DDD da coluna separada, remover do telefone
                    if ddd_limpo and len(ddd_limpo) >= 2:
                        # Verificar se os primeiros dígitos do telefone coincidem com o DDD
                        if tel_valor.startswith(ddd_limpo):
                            tel_valor = tel_valor[len(ddd_limpo):]
                    else:
                        # Se não tem DDD separado, extrair do telefone
                        ddd_limpo = tel_valor[:2]
                        tel_valor = tel_valor[2:]
                
                # Garantir que DDD tenha 2 dígitos
                if ddd_limpo and len(ddd_limpo) >= 2:
                    ddd_limpo = ddd_limpo[:2]
                else:
                    ddd_limpo = None
                
                # Ajustar telefone para 9 dígitos
                if tel_valor:
                    if len(tel_valor) == 8:
                        tel_valor = "9" + tel_valor
                    elif len(tel_valor) != 9:
                        tel_valor = None
                
                novos_ddds.append(ddd_limpo)
                novos_numeros.append(tel_valor)
            
            df["FONE1_DD"] = novos_ddds
            df["FONE1_NR"] = novos_numeros
            
        else:
            st.info("🔍 **Processando sem coluna DDD separada...**")
            # CASO 2: DDD está junto com o telefone
            df["TEL_LIMPO"] = df[col_tel].apply(limpar_telefone)
            
            novos_ddds = []
            novos_numeros = []
            
            for tel in df["TEL_LIMPO"]:
                if tel and len(tel) >= 10:
                    ddd = tel[:2]
                    numero = tel[2:]
                    
                    if len(numero) == 8:
                        numero = "9" + numero
                    elif len(numero) != 9:
                        ddd = None
                        numero = None
                else:
                    ddd = None
                    numero = None
                
                novos_ddds.append(ddd)
                novos_numeros.append(numero)
            
            df["FONE1_DD"] = novos_ddds
            df["FONE1_NR"] = novos_numeros
            df = df.drop(columns=["TEL_LIMPO"])
        
        # REMOVER LINHAS SEM NÚMERO VÁLIDO
        df_antes = len(df)
        df = df.dropna(subset=["FONE1_NR"])
        df_depois = len(df)
        
        st.warning(f"⚠️ Removidas {df_antes - df_depois} linhas sem número válido")
        
        # VERIFICAR SE FONE1_DD FOI PREENCHIDA
        st.info("📊 **Verificação da coluna FONE1_DD:**")
        dd_preenchidos = df["FONE1_DD"].notna().sum()
        dd_total = len(df)
        st.write(f"- Linhas com DDD: {dd_preenchidos} de {dd_total}")
        
        if dd_preenchidos == 0:
            st.error("🚨 ATENÇÃO: FONE1_DD está vazia!")
            st.write("**Solução:** Verifique se a coluna DDD na planilha original tem valores válidos (ex: 11, 21, 31)")
        
        # MOSTRAR AMOSTRA
        st.subheader("👁️ **Amostra dos dados processados:**")
        amostra_cols = []
        if col_nome:
            amostra_cols.append(col_nome)
        amostra_cols.extend(["FONE1_DD", "FONE1_NR"])
        
        # Formatar números para exibição
        df_amostra = df[amostra_cols].head(10).copy()
        if "FONE1_NR" in df_amostra.columns:
            df_amostra["FONE1_NR"] = df_amostra["FONE1_NR"].apply(
                lambda x: f"{x[:5]}-{x[5:]}" if pd.notna(x) and len(str(x)) == 9 else x
            )
        
        st.dataframe(df_amostra)
        
        # CRIAR COLUNAS ADICIONAIS
        df["ID1"] = range(10, 10 + len(df))
        df["ID2"] = df["ID1"]
        
        if col_nome:
            df["CAMPO01"] = df[col_nome].astype(str).str.split().str[0]
        else:
            df["CAMPO01"] = ""
        
        df["FONE1_DISCAR EM"] = ""
        df["FONE1_DISCAR AGORA"] = "S"
        
        # COLUNAS FINAIS
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
        
        # GERAR CSV
        csv = df.to_csv(sep=";", index=False, encoding="utf-8-sig")
        
        st.success(f"✅ Processamento concluído: {len(df)} registros válidos")
        
        # BOTÃO PARA DOWNLOAD
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                "⬇️ BAIXAR PLANILHA HIGIENIZADA",
                csv,
                "planilha_higienizada.csv",
                "text/csv",
                use_container_width=True
            )
        
    except Exception as e:
        st.error(f"❌ Erro: {str(e)}")
