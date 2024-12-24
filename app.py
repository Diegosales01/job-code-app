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
NIVEIS_CARREIRA = { ... }  # Mesma definição anterior

@st.cache_data
def carregar_bases():
    try:
        base_job_codes = pd.read_excel(BASE_JOB_CODES)
        base_substituicao = pd.read_excel(BASE_SUBSTITUICAO)
        base_substituicao['Gestor'] = base_substituicao['Gestor'].fillna("Gestor Não Informado")
        base_substituicao['Cargo'] = base_substituicao['Cargo'].fillna("Cargo Não Informado")
        return base_job_codes, base_substituicao
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None, None

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

def registrar_feedback(descricao_usuario, codigo_escolhido):
    st.info(f"Feedback registrado para: {descricao_usuario} com código {codigo_escolhido}")

st.title("Sistema de Sugestão de Job Codes")
base_job_codes, base_substituicao = carregar_bases()

# Inicialização de estado
if "descricao_usuario" not in st.session_state:
    st.session_state.descricao_usuario = ""
if "opcoes_disponiveis" not in st.session_state:
    st.session_state.opcoes_disponiveis = []
if "codigo_selecionado" not in st.session_state:
    st.session_state.codigo_selecionado = None

modo_busca = st.radio("Como deseja buscar o Job Code?", ("Descrição da Atividade", "Substituido", "Cargo e Gestor"))

if modo_busca == "Descrição da Atividade":
    st.session_state.descricao_usuario = st.text_area("Digite a descrição do cargo:", st.session_state.descricao_usuario)
    if st.button("Buscar Código"):
        if st.session_state.descricao_usuario.strip():
            tfidf = TfidfVectorizer(stop_words=stop_words, min_df=1, ngram_range=(1, 2))
            matriz_tfidf = tfidf.fit_transform(base_job_codes['Descricao em 2024'])
            st.session_state.opcoes_disponiveis = buscar_por_descricao(st.session_state.descricao_usuario, tfidf, matriz_tfidf, base_job_codes)
        else:
            st.warning("Por favor, insira uma descrição válida.")

    if st.session_state.opcoes_disponiveis:
        for i, (codigo, descricao, titulo) in enumerate(st.session_state.opcoes_disponiveis, 1):
            st.markdown(f"### Opção {i}")
            st.write(f"**Título:** {titulo}")
            st.write(f"**Código:** {codigo}")
            st.write(f"**Descrição:** {descricao}")
        
        opcao_selecionada = st.selectbox("Selecione a opção:", [f"Opção {i}" for i in range(1, 4)])
        nivel_carreira = st.selectbox("Selecione o nível de carreira:", list(NIVEIS_CARREIRA.keys()))
        
        if st.button("Confirmar Seleção"):
            indice = int(opcao_selecionada.split()[1]) - 1
            codigo, _, _ = st.session_state.opcoes_disponiveis[indice]
            complemento = NIVEIS_CARREIRA[nivel_carreira]
            st.session_state.codigo_selecionado = f"{codigo}-{complemento}"
            registrar_feedback(st.session_state.descricao_usuario, st.session_state.codigo_selecionado)
            st.success(f"Código Completo Selecionado: {st.session_state.codigo_selecionado}")

elif modo_busca == "Substituido":
    substituido = st.selectbox("Selecione o nome do substituído:", sorted(base_substituicao['Substituido'].dropna().unique()))
    if substituido:
        ultimo_registro = base_substituicao[base_substituicao['Substituido'] == substituido].sort_values(by='Data Referencia', ascending=False).iloc[0]
        st.markdown("### Último Registro Encontrado")
        st.write(f"**Job Code:** {ultimo_registro['Job Code']}")
        st.write(f"**Título:** {ultimo_registro['Titulo Job Code']}")
        st.write(f"**Cargo:** {ultimo_registro['Cargo']}")
        st.write(f"**Gestor:** {ultimo_registro['Gestor']}")
        st.write(f"**Data de Referência:** {ultimo_registro['Data Referencia']}")

elif modo_busca == "Cargo e Gestor":
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
