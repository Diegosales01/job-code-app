import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Stopwords estáticas em português
stop_words = [
    'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'e',
    'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as',
    'dos', 'como', 'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à',
    'seu', 'sua', 'ou', 'ser', 'quando', 'muito', 'há', 'nos',
    'já', 'está', 'eu', 'também', 'só', 'pelo', 'pela', 'até',
    'isso', 'ela', 'entre', 'depois', 'sem', 'mesmo', 'aos',
    'seus', 'quem', 'nas', 'me', 'esse', 'eles', 'estão',
    'você', 'tinha', 'foram', 'essa', 'num', 'nem', 'suas',
    'meu', 'às', 'minha', 'têm', 'numa', 'pelos', 'elas',
    'havia', 'seja', 'qual', 'será', 'nós', 'tenho', 'lhe',
    'deles', 'essas', 'esses', 'pelas', 'este', 'fosse',
    'dele', 'tu', 'te', 'vocês', 'vos', 'lhes', 'meus',
    'minhas', 'teu', 'tua', 'teus', 'tuas', 'nosso',
    'nossa', 'nossos', 'nossas', 'dela', 'delas', 'esta',
    'estes', 'estas', 'aquele', 'aquela', 'aqueles',
    'aquelas', 'isto', 'aquilo'
]

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

# Função para carregar bases
@st.cache_data
def carregar_bases():
    try:
        base_job_codes = pd.read_excel(BASE_JOB_CODES)
        base_substituicao = pd.read_excel(BASE_SUBSTITUICAO)

        colunas_necessarias = ['Substituido', 'Cargo', 'Gestor', 'Data Referencia']
        for coluna in colunas_necessarias:
            if coluna not in base_substituicao.columns:
                raise ValueError(f"A coluna '{coluna}' não foi encontrada na base de substituição.")

        base_substituicao['Gestor'] = base_substituicao['Gestor'].fillna("Gestor Não Informado")
        base_substituicao['Cargo'] = base_substituicao['Cargo'].fillna("Cargo Não Informado")

        return base_job_codes, base_substituicao
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None, None

# Função para buscar por descrição
def buscar_por_descricao(descricao_usuario, tfidf, matriz_tfidf, base_job_codes):
    descricao_usuario_tfidf = tfidf.transform([descricao_usuario])
    similaridades = cosine_similarity(descricao_usuario_tfidf, matriz_tfidf)
    indices_similares = similaridades.argsort()[0, -3:][::-1]
    opcoes = []
    for indice in indices_similares:
        descricao_similar = base_job_codes.iloc[indice]['Descricao em 2024']
        codigo_similar = base_job_codes.iloc[indice]['Job Code']
        titulo_similar = base_job_codes.iloc[indice]['Titulo em 2024']
        opcoes.append((codigo_similar, descricao_similar, titulo_similar))
    return opcoes

# Função para registrar feedback
def registrar_feedback(descricao_usuario, codigo_escolhido):
    feedback = {'Descricao do Usuario': descricao_usuario, 'Job Code Escolhido': codigo_escolhido}
    feedback_df = pd.DataFrame([feedback])
    feedback_csv = 'feedback_usuario.csv'
    feedback_df.to_csv(feedback_csv, mode='a', index=False, header=not st.session_state.feedback_existe)
    st.session_state.feedback_existe = True
    st.success("Feedback registrado com sucesso!")

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
                opcoes = buscar_por_descricao(descricao_usuario, tfidf, matriz_tfidf, base_job_codes)
                if opcoes:
                    for i, (codigo, descricao, titulo) in enumerate(opcoes, 1):
                        st.markdown(f"### Opção {i}")
                        st.write(f"**Título:** {titulo}")
                        st.write(f"**Código:** {codigo}")
                        st.write(f"**Descrição:** {descricao}")
                        nivel_carreira = st.selectbox("Selecione o nível de carreira:", list(NIVEIS_CARREIRA.keys()), key=f"nivel_{i}")
                        if st.button(f"Selecionar Opção {i}", key=f"botao_{i}"):
                            complemento = NIVEIS_CARREIRA[nivel_carreira]
                            codigo_completo = f"{codigo}-{complemento}"
                            registrar_feedback(descricao_usuario, codigo_completo)
                            st.success(f"JOB CODE SELECIONADO: {codigo_completo}")
                else:
                    st.warning("Nenhuma opção encontrada.")
            else:
                st.error("Erro ao carregar os dados.")
        else:
            st.warning("Por favor, insira uma descrição válida.")
