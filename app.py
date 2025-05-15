import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configurar a API do Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Função para obter sugestões usando Gemini
def obter_sugestoes_gemini(descricao, base_job_codes):
    prompt = f"""
A seguir está uma descrição de atividade enviada por um usuário:
{descricao}

Considere a base de possíveis descrições abaixo com seus respectivos códigos:
{base_job_codes[['Job Code', 'Titulo em 2024', 'Descricao em 2024']].to_dict(orient='records')}

Com base nisso, retorne as 3 descrições mais compatíveis com a descrição enviada, no seguinte formato:
[
    {{
        "Job Code": "XXX",
        "Titulo": "...",
        "Descricao": "..."
    }},
    ...
]
"""
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    try:
        resultado = eval(response.text.strip())
        return resultado
    except:
        st.error("Erro ao interpretar resposta do Gemini.")
        return []

# Função para carregar a base de dados
@st.cache_data
def carregar_base():
    try:
        return pd.read_excel("base_job_codes.xlsx")
    except Exception as e:
        st.error(f"Erro ao carregar base de dados: {e}")
        return None

# Função para registrar feedback
def registrar_feedback(entrada, codigo):
    with open("feedback.csv", "a", encoding="utf-8") as f:
        f.write(f'"{entrada}","{codigo}"\n')

# Níveis de carreira disponíveis
NIVEIS_CARREIRA = {
    "Estágio": "EST",
    "Trainee": "TRN",
    "Júnior": "JR",
    "Pleno": "PL",
    "Sênior": "SR",
    "Coordenador": "COORD",
    "Especialista": "ESP",
    "Gerente": "GR",
    "Diretor": "DIR",
    "Superintendente": "SUP"
}

# Interface do Streamlit
st.title("Sistema de Sugestão de Job Code")

modo_busca = st.radio("Escolha o modo de busca:", [
    "Descrição da Atividade",
    "Colaborador (Cargo atual)",
    "Gestor + Cargo"
])

base_job_codes = carregar_base()

# Descrição da Atividade com Gemini
if modo_busca == "Descrição da Atividade":
    descricao_usuario = st.text_area("Digite a descrição do cargo:")

    if "opcoes_descricao" not in st.session_state:
        st.session_state.opcoes_descricao = []

    if "selecao_descricao" not in st.session_state:
        st.session_state.selecao_descricao = None

    if st.button("Buscar Código"):
        if descricao_usuario.strip():
            if base_job_codes is not None:
                resultados = obter_sugestoes_gemini(descricao_usuario, base_job_codes)
                st.session_state.opcoes_descricao = [
                    (r['Job Code'], r['Descricao'], r['Titulo']) for r in resultados
                ]
                if not st.session_state.opcoes_descricao:
                    st.warning("Nenhuma opção encontrada.")
            else:
                st.error("Erro ao carregar os dados.")
        else:
            st.warning("Por favor, insira uma descrição válida.")

    if st.session_state.opcoes_descricao:
        for i, (codigo, descricao, titulo) in enumerate(st.session_state.opcoes_descricao, 1):
            st.markdown(f"### Opção {i}")
            st.write(f"**Título:** {titulo}")
            st.write(f"**Código:** {codigo}")
            st.write(f"**Descrição:** {descricao}")

        opcao_selecionada = st.selectbox(
            "Selecione a opção:",
            [f"Opção {i}" for i in range(1, len(st.session_state.opcoes_descricao) + 1)],
            key="selecao_descricao"
        )
        nivel_carreira = st.selectbox("Selecione o nível de carreira:", list(NIVEIS_CARREIRA.keys()))

        if st.button("Confirmar Seleção"):
            index_selecionado = int(opcao_selecionada.split()[1]) - 1
            codigo, _, _ = st.session_state.opcoes_descricao[index_selecionado]
            complemento = NIVEIS_CARREIRA[nivel_carreira]
            codigo_completo = f"{codigo}-{complemento}"
            registrar_feedback(descricao_usuario, codigo_completo)
            st.success(f"Código Completo Selecionado: {codigo_completo}")

# As demais funcionalidades (busca por colaborador e por gestor + cargo)
# permanecem iguais — se desejar, posso integrá-las aqui também.
