import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Stopwords estáticas em português
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

# URLs das bases no GitHub
BASE_JOB_CODES = "https://raw.githubusercontent.com/Diegosales01/job-code-app/refs/heads/main/Base_Job_Code_2024.xlsx"
BASE_SUBSTITUICAO = "https://raw.githubusercontent.com/Diegosales01/job-code-app/refs/heads/main/BASE_SUBSTITUICAO.xlsx"

# Função para carregar bases
@st.cache_data
def carregar_bases():
    try:
        base_job_codes = pd.read_excel(BASE_JOB_CODES)
        base_substituicao = pd.read_excel(BASE_SUBSTITUICAO)
        
        # Verificar colunas necessárias
        colunas_necessarias = ['Substituido', 'Cargo', 'Gestor', 'Data Referência']
        for coluna in colunas_necessarias:
            if coluna not in base_substituicao.columns:
                raise ValueError(f"A coluna '{coluna}' não foi encontrada na base de substituição.")
        
        # Tratar valores nulos
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
modo_busca = st.radio("Como deseja buscar o Job Code?", ("Descrição da Atividade", "Nome do Substituído", "Cargo e Gestor"))

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
                        if st.button(f"Selecionar Opção {i}", key=f"botao_{i}"):
                            registrar_feedback(descricao_usuario, codigo)
                else:
                    st.warning("Nenhuma opção encontrada.")
            else:
                st.error("Erro ao carregar os dados.")
        else:
            st.warning("Por favor, insira uma descrição válida.")

elif modo_busca == "Nome do Substituído":
    if base_substituicao is not None:
        substituido = st.selectbox("Selecione o nome do substituído:", sorted(base_substituicao['Nome Substituído'].unique()))
        if substituido:
            resultado = base_substituicao[base_substituicao['Nome Substituído'] == substituido].sort_values(by='Data Referência', ascending=False)
            st.markdown("### Resultados Encontrados")
            for _, linha in resultado.iterrows():
                st.write(f"**Job Code:** {linha['Job Code']}")
                st.write(f"**Título:** {linha['Titulo']}")
    else:
        st.error("Base de substituição não carregada.")

elif modo_busca == "Cargo e Gestor":
    if base_substituicao is not None:
        cargo = st.selectbox("Selecione o cargo:", sorted(base_substituicao['Cargo'].unique()))
        gestor = st.selectbox("Selecione o gestor:", sorted(base_substituicao['Gestor'].unique()))
        if cargo and gestor:
            resultado = base_substituicao[(base_substituicao['Cargo'] == cargo) & (base_substituicao['Gestor'] == gestor)].sort_values(by='Data Referência', ascending=False)
            if not resultado.empty:
                st.markdown("### Resultados Encontrados")
                for _, linha in resultado.iterrows():
                    st.write(f"**Job Code:** {linha['Job Code']}")
                    st.write(f"**Título:** {linha['Titulo']}")
            else:
                st.warning("Nenhum resultado encontrado para a combinação selecionada.")
    else:
        st.error("Base de substituição não carregada.")
