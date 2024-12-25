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

def buscar_por_descricao(descricao_usuario, tfidf, matriz_tfidf, base_job_codes):
    try:
        descricao_usuario_tfidf = tfidf.transform([descricao_usuario])
        similaridades = cosine_similarity(descricao_usuario_tfidf, matriz_tfidf)
        indices_similares = similaridades.argsort()[0, -3:][::-1]
        opcoes = []
        for indice in indices_similares:
            if indice < len(base_job_codes):
                descricao_similar = base_job_codes.iloc[indice]['Descricao em 2024']
                codigo_similar = base_job_codes.iloc[indice]['Job Code']
                titulo_similar = base_job_codes.iloc[indice]['Titulo em 2024']
                opcoes.append((codigo_similar, descricao_similar, titulo_similar))
        return opcoes
    except Exception as e:
        st.error(f"Erro ao buscar descrição: {e}")
        return []

def buscar_por_substituido(substituido, base_substituicao):
    resultados = base_substituicao[base_substituicao['Substituido'].str.contains(substituido, case=False, na=False)]
    return resultados

def buscar_por_cargo_e_gestor(cargo, gestor, base_substituicao):
    resultados = base_substituicao[
        (base_substituicao['Cargo'].str.contains(cargo, case=False, na=False)) &
        (base_substituicao['Gestor'].str.contains(gestor, case=False, na=False))
    ]
    return resultados

def registrar_feedback(descricao_usuario, codigo_escolhido):
    st.info(f"Feedback registrado para: {descricao_usuario} com código {codigo_escolhido}")

# Interface do usuário
st.title("Sistema de Sugestão de Job Codes")
base_job_codes, base_substituicao = carregar_bases()

# Inicialização de variáveis na sessão
if "descricao_usuario" not in st.session_state:
    st.session_state.descricao_usuario = ""
if "opcoes_disponiveis" not in st.session_state:
    st.session_state.opcoes_disponiveis = []
if "codigo_selecionado" not in st.session_state:
    st.session_state.codigo_selecionado = None

# Seleção inicial
modo_busca = st.radio("Como deseja buscar o Job Code?", ("Descrição da Atividade", "Substituido", "Cargo e Gestor"))

if modo_busca == "Descrição da Atividade":
    st.session_state.descricao_usuario = st.text_area("Digite a descrição do cargo:", st.session_state.descricao_usuario)
    if st.button("Buscar Código"):
        if st.session_state.descricao_usuario.strip():
            if base_job_codes is not None:
                tfidf = TfidfVectorizer(stop_words=stop_words, min_df=1, ngram_range=(1, 2))
                matriz_tfidf = tfidf.fit_transform(base_job_codes['Descricao em 2024'])
                opcoes = buscar_por_descricao(st.session_state.descricao_usuario, tfidf, matriz_tfidf, base_job_codes)
                if opcoes:
                    st.session_state.opcoes_disponiveis = opcoes
                else:
                    st.warning("Nenhuma opção encontrada.")
            else:
                st.error("Erro ao carregar os dados.")
        else:
            st.warning("Por favor, insira uma descrição válida.")
    
    if st.session_state.opcoes_disponiveis:
        opcoes_disponiveis = st.session_state.opcoes_disponiveis
        for i, (codigo, descricao, titulo) in enumerate(opcoes_disponiveis, 1):
            st.markdown(f"### Opção {i}")
            st.write(f"**Título:** {titulo}")
            st.write(f"**Código:** {codigo}")
            st.write(f"**Descrição:** {descricao}")
        
        opcao_selecionada = st.selectbox("Selecione a opção:", [f"Opção {i+1}" for i in range(len(opcoes_disponiveis))])
        nivel_carreira = st.selectbox("Selecione o nível de carreira:", list(NIVEIS_CARREIRA.keys()))

        if st.button("Confirmar Seleção"):
            i = int(opcao_selecionada.split()[1]) - 1
            codigo, descricao, _ = opcoes_disponiveis[i]
            complemento = NIVEIS_CARREIRA[nivel_carreira]
            st.session_state.codigo_selecionado = f"{codigo}-{complemento}"
            registrar_feedback(st.session_state.descricao_usuario, st.session_state.codigo_selecionado)
            st.success(f"Código Completo Selecionado: {st.session_state.codigo_selecionado}")

elif modo_busca == "Substituido":
    substituido = st.text_input("Digite o nome do substituído:")
    if st.button("Buscar por Substituído"):
        if base_substituicao is not None:
            resultados = buscar_por_substituido(substituido, base_substituicao)
            st.write(resultados)
        else:
            st.error("Erro ao carregar os dados.")

elif modo_busca == "Cargo e Gestor":
    cargo = st.text_input("Digite o cargo:")
    gestor = st.text_input("Digite o nome do gestor:")
    if st.button("Buscar por Cargo e Gestor"):
        if base_substituicao is not None:
            resultados = buscar_por_cargo_e_gestor(cargo, gestor, base_substituicao)
            st.write(resultados)
        else:
            st.error("Erro ao carregar os dados.")
