import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from nltk.corpus import stopwords

# Carregar stopwords em português
stop_words = set(stopwords.words('portuguese'))

# Função para limpar o texto
def clean_text(text):
    text = re.sub(r'[^\w\s]', '', text)  # Remove pontuação
    text = text.lower()  # Converte para minúsculas
    words = text.split()
    words = [word for word in words if word not in stop_words]  # Remove stopwords
    return ' '.join(words)

# Função para sugerir códigos com base em similaridade
def suggest_codes(input_text, base, column):
    base[column] = base[column].astype(str).apply(clean_text)
    input_text_cleaned = clean_text(input_text)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(base[column])
    input_vector = vectorizer.transform([input_text_cleaned])

    similarities = cosine_similarity(input_vector, tfidf_matrix).flatten()
    top_indices = similarities.argsort()[-3:][::-1]
    suggestions = base.iloc[top_indices]

    return suggestions, similarities[top_indices]

# Carregar base de dados
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        return pd.read_excel(uploaded_file)
    return None

# Interface do Usuário
st.title("Sistema de Sugestão de Job Codes")
st.sidebar.header("Configuração de Busca")

uploaded_file = st.sidebar.file_uploader("Carregue sua base de dados em Excel", type="xlsx")
base = load_data(uploaded_file)

if base is not None:
    st.sidebar.success("Base de dados carregada com sucesso!")

    option = st.sidebar.selectbox("Escolha o tipo de busca:", [
        "Descrição da Atividade",
        "Substituído",
        "Cargo e Gestor"
    ])

    if option == "Descrição da Atividade":
        input_text = st.text_area("Digite a descrição da atividade:")
        column = "descricao"

    elif option == "Substituído":
        input_text = st.text_input("Digite o código substituído:")
        column = "substituido"

    elif option == "Cargo e Gestor":
        input_cargo = st.text_input("Digite o cargo:")
        input_gestor = st.text_input("Digite o gestor:")
        input_text = f"{input_cargo} {input_gestor}"
        column = "cargo_gestor"

    if st.button("Buscar"):
        if input_text.strip() != "":
            if column not in base.columns:
                st.error(f"A coluna '{column}' não foi encontrada na base de dados.")
            else:
                suggestions, scores = suggest_codes(input_text, base, column)
                st.write("### Sugestões de Job Code:")

                for i, (index, row) in enumerate(suggestions.iterrows()):
                    st.write(f"{i + 1}. **Código:** {row['codigo']}  
**Pontuação:** {scores[i]:.2f}  
**Descrição:** {row[column]}")

                feedback = st.radio("Escolha a sugestão mais adequada:", ["Nenhuma"] + [f"Sugestão {i + 1}" for i in range(len(suggestions))])

                if st.button("Enviar Feedback"):
                    if feedback == "Nenhuma":
                        st.info("Feedback registrado: Nenhuma sugestão foi adequada.")
                    else:
                        selected_index = int(feedback.split()[1]) - 1
                        st.success(f"Feedback registrado: Sugestão {selected_index + 1} escolhida.")

        else:
            st.warning("Por favor, insira um texto para busca.")

else:
    st.warning("Por favor, carregue uma base de dados para iniciar a busca.")
