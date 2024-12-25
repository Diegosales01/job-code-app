import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Stopwords estáticas em português
stop_words = [...]

# URLs das bases no GitHub
BASE_JOB_CODES = "https://raw.githubusercontent.com/Diegosales01/job-code-app/refs/heads/main/Base_Job_Code_2024.xlsx"
BASE_SUBSTITUICAO = "https://raw.githubusercontent.com/Diegosales01/job-code-app/refs/heads/main/BASE_SUBSTITUICAO.xlsx"

# Mapeamento dos níveis de carreira
NIVEIS_CARREIRA = {
    "PRESIDENTE": "EX-19",
    "VICE PRESIDENTE": "EX-18",
    "DIRETOR II": "EX-17",
    "DIRETOR I": "EX-16",
    "GERENTE EXECUTIVO": "M3-14",
    "GERENTE II": "M2-13",
    "GERENTE I": "M2-12",
    "LÍDER TÉCNICO I": "M2-12",
    "LÍDER TÉCNICO II": "M2-13",
    "COORDENADOR I": "M1-10",
    "COORDENADOR II": "M1-11",
    "ESPECIALISTA I": "M1-10",
    "ESPECIALISTA II": "M1-11",
    "ANALISTA III": "P3-11",
    "ANALISTA III (COMERCIAL)": "S3-11",
    "ANALISTA II": "P2-10",
    "ANALISTA II (COMERCIAL)": "S2-10",
    "ANALISTA I": "P1-08",
    "ANALISTA I (COMERCIAL)": "S1-08",
    "ASSISTENTE (ATENDIMENTO)": "T2-06",
    "ASSISTENTE": "U2-06",
    "AUXILIAR": "U2-05",
    "AUXILIAR (ATENDIMENTO)": "T2-05",
    "SUPERVISOR III (ATENDIMENTO)": "S3-11",
    "SUPERVISOR II (ATENDIMENTO)": "P2-10",
    "SUPERVISOR I (ATENDIMENTO)": "T4-09",
    "ASSISTENTE (ATENDIMENTO)": "U1-04"
}

@st.cache_data
def carregar_bases():
    try:
        base_job_codes = pd.read_excel(BASE_JOB_CODES)
        base_substituicao = pd.read_excel(BASE_SUBSTITUICAO)
        return base_job_codes, base_substituicao
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None, None

def buscar_por_substituido(substituido, base_substituicao):
    resultados = base_substituicao[base_substituicao['Substituido'].str.contains(substituido, case=False, na=False)]
    return resultados[['Substituido', 'Job Code', 'Descricao']].values.tolist()

def buscar_por_cargo_e_gestor(cargo, gestor, base_substituicao):
    resultados = base_substituicao[
        (base_substituicao['Cargo'].str.contains(cargo, case=False, na=False)) &
        (base_substituicao['Gestor'].str.contains(gestor, case=False, na=False))
    ]
    return resultados[['Cargo', 'Gestor', 'Job Code', 'Descricao']].values.tolist()

def registrar_feedback(entrada, codigo_escolhido):
    st.info(f"Feedback registrado para: {entrada} com código {codigo_escolhido}")

# Interface do usuário
st.title("Sistema de Sugestão de Job Codes")
base_job_codes, base_substituicao = carregar_bases()

# Seleção inicial
modo_busca = st.radio("Como deseja buscar o Job Code?", ("Descrição da Atividade", "Substituido", "Cargo e Gestor"))

if modo_busca == "Descrição da Atividade":
    descricao_usuario = st.text_area("Digite a descrição do cargo:")
    if st.button("Buscar Código"):
        if descricao_usuario.strip():
            if base_job_codes is not None:
                tfidf = TfidfVectorizer(stop_words=stop_words, min_df=1, ngram_range=(1, 2))
                matriz_tfidf = tfidf.fit_transform(base_job_codes['Descricao em 2024'])
                similaridades = cosine_similarity(tfidf.transform([descricao_usuario]), matriz_tfidf)
                indices_similares = similaridades.argsort()[0, -3:][::-1]
                opcoes = [(base_job_codes.iloc[i]['Job Code'], base_job_codes.iloc[i]['Descricao em 2024'], base_job_codes.iloc[i]['Titulo em 2024']) for i in indices_similares if i < len(base_job_codes)]
                if opcoes:
                    for i, (codigo, descricao, titulo) in enumerate(opcoes, 1):
                        st.markdown(f"### Opção {i}")
                        st.write(f"**Título:** {titulo}")
                        st.write(f"**Código:** {codigo}")
                        st.write(f"**Descrição:** {descricao}")
                    opcao_selecionada = st.selectbox("Selecione a opção:", [f"Opção {i+1}" for i in range(len(opcoes))])
                    nivel_carreira = st.selectbox("Selecione o nível de carreira:", list(NIVEIS_CARREIRA.keys()))
                    if st.button("Confirmar Seleção"):
                        codigo, _, _ = opcoes[int(opcao_selecionada.split()[1]) - 1]
                        complemento = NIVEIS_CARREIRA[nivel_carreira]
                        codigo_completo = f"{codigo}-{complemento}"
                        registrar_feedback(descricao_usuario, codigo_completo)
                        st.success(f"Código Completo Selecionado: {codigo_completo}")
                else:
                    st.warning("Nenhuma opção encontrada.")
            else:
                st.error("Erro ao carregar os dados.")
        else:
            st.warning("Por favor, insira uma descrição válida.")

elif modo_busca == "Substituido":
    if base_substituicao is not None:
        substituido = st.selectbox("Selecione o nome do substituído:", sorted(base_substituicao['Substituido'].dropna().unique()))
        if substituido:
            # Selecionar apenas o último registro baseado na data mais recente
            ultimo_registro = base_substituicao[base_substituicao['Substituido'] == substituido].sort_values(by='Data Referencia', ascending=False).iloc[0]
            st.markdown("### Último Registro Encontrado")
            st.write(f"**Job Code:** {ultimo_registro['Job Code']}")
            st.write(f"**Título:** {ultimo_registro['Titulo Job Code']}")
            st.write(f"**Cargo:** {ultimo_registro['Cargo']}")
            st.write(f"**Gestor:** {ultimo_registro['Gestor']}")
            st.write(f"**Data de Referência:** {ultimo_registro['Data Referencia']}")
    else:
        st.error("Base de substituição não carregada.")

elif modo_busca == "Cargo e Gestor":
    if base_substituicao is not None:
        cargo = st.selectbox("Selecione o cargo:", sorted(base_substituicao['Cargo'].unique()))
        gestor = st.selectbox("Selecione o gestor:", sorted(base_substituicao['Gestor'].unique()))
        if cargo and gestor:
            resultado = base_substituicao[(base_substituicao['Cargo'] == cargo) & (base_substituicao['Gestor'] == gestor)].sort_values(by='Data Referencia', ascending=False)
            if not resultado.empty:
                st.markdown("### Resultados Encontrados")
                for _, linha in resultado.iterrows():
                    st.write(f"**Job Code:** {linha['Job Code']}")
                    st.write(f"**Título:** {linha['Titulo']}")
            else:
                st.warning("Nenhum resultado encontrado para a combinação selecionada.")
    else:
        st.error("Base de substituição não carregada.")
