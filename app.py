import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

# URLs dos arquivos Excel no GitHub
BASE_JOB_CODES = "https://raw.githubusercontent.com/Diegosales01/job-code-app/main/Base_Job_Code_2024.xlsx"
BASE_SUBSTITUICAO = "https://raw.githubusercontent.com/Diegosales01/job-code-app/main/BASE_SUBSTITUICAO.xlsx"

# Função para carregar bases de dados
@st.cache_data
def carregar_bases():
    try:
        base_job_codes = pd.read_excel(BASE_JOB_CODES)
        base_substituicao = pd.read_excel(BASE_SUBSTITUICAO)

        # Validar colunas necessárias
        colunas_job_codes = ['Descricao em 2024', 'Job Code', 'Titulo em 2024']
        colunas_substituicao = ['Substituido', 'Gestor', 'Cargo', 'Job Code', 'Titulo Job Code', 'Data Referencia']

        for coluna in colunas_job_codes:
            if coluna not in base_job_codes.columns:
                raise ValueError(f"A coluna '{coluna}' não foi encontrada na base de job codes.")
        
        for coluna in colunas_substituicao:
            if coluna not in base_substituicao.columns:
                raise ValueError(f"A coluna '{coluna}' não foi encontrada na base de substituição.")
        
        # Ordenar a base de substituição pela data mais recente
        base_substituicao = base_substituicao.sort_values(by='Data Referencia', ascending=False)

        # Configurar TF-IDF para a base de descrições
        tfidf = TfidfVectorizer(stop_words=stop_words, min_df=1, ngram_range=(1, 2))
        matriz_tfidf = tfidf.fit_transform(base_job_codes['Descricao em 2024'])

        return base_job_codes, base_substituicao, matriz_tfidf, tfidf
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None, None, None, None

# Função para buscar códigos com base na descrição
def buscar_por_descricao(descricao_usuario, tfidf, matriz_tfidf, base_job_codes):
    descricao_usuario_tfidf = tfidf.transform([descricao_usuario])
    similaridades = cosine_similarity(descricao_usuario_tfidf, matriz_tfidf)
    indices_similares = similaridades.argsort()[0, -3:][::-1]
    opcoes = []
    for indice in indices_similares:
        codigo_similar = base_job_codes.iloc[indice]['Job Code']
        descricao_similar = base_job_codes.iloc[indice]['Descricao em 2024']
        titulo_similar = base_job_codes.iloc[indice]['Titulo em 2024']
        opcoes.append((codigo_similar, descricao_similar, titulo_similar))
    return opcoes

# Função para registrar feedback
def registrar_feedback(descricao_usuario, codigo_escolhido, tipo_busca):
    feedback = {'Descricao Usuario': descricao_usuario, 'Job Code Escolhido': codigo_escolhido, 'Tipo Busca': tipo_busca}
    feedback_df = pd.DataFrame([feedback])
    feedback_csv = 'feedback_usuario.csv'
    feedback_df.to_csv(feedback_csv, mode='a', index=False, header=not st.session_state.get('feedback_existe', False))
    st.session_state['feedback_existe'] = True
    st.success("Feedback registrado com sucesso!")

# Interface do usuário
st.title("Sistema de Sugestão de Job Codes")

# Seleção de tipo de busca
tipo_busca = st.radio("Selecione o tipo de busca:", ["Descrição da Atividade", "Por Substituído", "Por Cargo e Gestor"])

# Carregar dados
base_job_codes, base_substituicao, matriz_tfidf, tfidf = carregar_bases()

if tipo_busca == "Descrição da Atividade":
    descricao_usuario = st.text_area("Digite a descrição da atividade:")
    if st.button("Buscar Código"):
        if descricao_usuario.strip():
            opcoes = buscar_por_descricao(descricao_usuario, tfidf, matriz_tfidf, base_job_codes)
            if opcoes:
                for i, (codigo, descricao, titulo) in enumerate(opcoes, 1):
                    st.markdown(f"### Opção {i}")
                    st.write(f"**Código:** {codigo}")
                    st.write(f"**Título:** {titulo}")
                    st.write(f"**Descrição:** {descricao}")
                    if st.button(f"Selecionar Opção {i}", key=f"desc_botao_{i}"):
                        registrar_feedback(descricao_usuario, codigo, "Descrição da Atividade")
            else:
                st.warning("Nenhuma opção encontrada.")
        else:
            st.warning("Por favor, insira uma descrição válida.")

elif tipo_busca == "Por Substituído":
    substituido = st.selectbox("Selecione o nome do substituído:", sorted(base_substituicao['Substituido'].unique()))
    if st.button("Buscar por Substituído"):
        resultados = base_substituicao[base_substituicao['Substituido'] == substituido]
        for i, row in resultados.iterrows():
            st.markdown(f"### Job Code")
            st.write(f"**Código:** {row['Job Code']}")
            st.write(f"**Título:** {row['Titulo Job Code']}")
            if st.button(f"Selecionar Substituído {i}", key=f"sub_botao_{i}"):
                registrar_feedback(substituido, row['Job Code'], "Por Substituído")

elif tipo_busca == "Por Cargo e Gestor":
    cargo = st.selectbox("Selecione o cargo:", sorted(base_substituicao['Cargo'].unique()))
    gestor = st.selectbox("Selecione o gestor:", sorted(base_substituicao['Gestor'].unique()))
    if st.button("Buscar por Cargo e Gestor"):
        resultados = base_substituicao[(base_substituicao['Cargo'] == cargo) & (base_substituicao['Gestor'] == gestor)]
        for i, row in resultados.iterrows():
            st.markdown(f"### Job Code")
            st.write(f"**Código:** {row['Job Code']}")
            st.write(f"**Título:** {row['Titulo Job Code']}")
            if st.button(f"Selecionar Cargo/Gestor {i}", key=f"cg_botao_{i}"):
                registrar_feedback(f"{cargo}/{gestor}", row['Job Code'], "Por Cargo e Gestor")
