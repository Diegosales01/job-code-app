
import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
import nltk

# Stopwords estáticas em português (sem necessidade de download)
stop_words = [
    'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 
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

# URL do arquivo Excel no GitHub
ARQUIVO_EXCEL = "https://raw.githubusercontent.com/Diegosales01/job-code-app/refs/heads/main/Base_Job_Code_2024.xlsx"

# Função para carregar dados do Excel
@st.cache_data
def carregar_dados():
    try:
        dados = pd.read_excel(ARQUIVO_EXCEL)
        colunas_necessarias = ['Descricao em 2024', 'Job Code', 'Titulo em 2024']
        for coluna in colunas_necessarias:
            if coluna not in dados.columns:
                raise ValueError(f"A coluna '{coluna}' não foi encontrada no arquivo.")
        tfidf = TfidfVectorizer(stop_words=stop_words, min_df=1, ngram_range=(1, 2))
        matriz_tfidf = tfidf.fit_transform(dados['Descricao em 2024'])
        return dados, matriz_tfidf, tfidf
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None, None, None

# Função para buscar sugestões de códigos
def buscar_codigo(descricao_usuario, tfidf, matriz_tfidf, dados):
    descricao_usuario_tfidf = tfidf.transform([descricao_usuario])
    similaridades = cosine_similarity(descricao_usuario_tfidf, matriz_tfidf)
    indices_similares = similaridades.argsort()[0, -3:][::-1]
    opcoes = []
    for indice in indices_similares:
        descricao_similar = dados.iloc[indice]['Descricao em 2024']
        codigo_similar = dados.iloc[indice]['Job Code']
        titulo_similar = dados.iloc[indice]['Titulo em 2024']
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
descricao_usuario = st.text_area("Digite a descrição do cargo:")
if st.button("Buscar Código"):
    if descricao_usuario.strip():
        dados, matriz_tfidf, tfidf = carregar_dados()
        if dados is not None and matriz_tfidf is not None and tfidf is not None:
            opcoes = buscar_codigo(descricao_usuario, tfidf, matriz_tfidf, dados)
            if opcoes:
                for i, (codigo, descricao, titulo) in enumerate(opcoes, 1):
                    st.markdown(f"### Opção {i}")
                    st.write(f"**Título:** {titulo}")
                    st.write(f"**Código:** {codigo}")
                    st.write(f"**Descrição:** {descricao}")
                    if st.button(f"Selecionar Opção {i}", key=f"botao_{i}"):
                        registrar_feedback(descricao_usuario, codigo)
            else:
                st.warning("Nenhuma opção encontrada.")
        else:
            st.error("Erro ao carregar os dados.")
    else:
        st.warning("Por favor, insira uma descrição válida.")
