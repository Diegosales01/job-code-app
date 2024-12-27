# Funções de busca atualizadas
def buscar_por_substituido(substituido, base_substituicao):
    resultados = base_substituicao[base_substituicao['Substituido'].str.contains(substituido, case=False, na=False)]
    return resultados[['Substituido', 'Job Code', 'Descricao', 'Descricao em 2024']].values.tolist()

def buscar_por_cargo_e_gestor(cargo, gestor, base_substituicao):
    resultados = base_substituicao[
        (base_substituicao['Cargo'].str.contains(cargo, case=False, na=False)) &
        (base_substituicao['Gestor'].str.contains(gestor, case=False, na=False))
    ]
    return resultados[['Cargo', 'Gestor', 'Job Code', 'Descricao', 'Descricao em 2024']].values.tolist()

# Modos de busca atualizados
if modo_busca == "Descrição da Atividade":
    descricao_usuario = st.text_area("Digite a descrição do cargo:")

    if st.button("Buscar Código"):
        if descricao_usuario.strip():
            if base_job_codes is not None:
                tfidf = TfidfVectorizer(stop_words=stop_words, min_df=1, ngram_range=(1, 2))
                matriz_tfidf = tfidf.fit_transform(base_job_codes['Descricao em 2024'])
                similaridades = cosine_similarity(tfidf.transform([descricao_usuario]), matriz_tfidf)
                indices_similares = similaridades.argsort()[0, -3:][::-1]
                st.session_state.opcoes_descricao = [
                    (base_job_codes.iloc[i]['Job Code'], base_job_codes.iloc[i]['Descricao em 2024'], base_job_codes.iloc[i]['Titulo em 2024'])
                    for i in indices_similares if i < len(base_job_codes)
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

elif modo_busca == "Colaborador (Ativo ou Desligado)":
    if base_substituicao is not None:
        substituido = st.selectbox("Selecione o nome do colaborador:", sorted(base_substituicao['Substituido'].dropna().unique()))
        if substituido:
            ultimo_registro = base_substituicao[base_substituicao['Substituido'] == substituido].sort_values(by='Data Referencia', ascending=False).iloc[0]
            st.markdown("### Último Registro Encontrado")
            st.write(f"**Job Code:** {ultimo_registro['Job Code']}")
            st.write(f"**Título:** {ultimo_registro['Titulo Job Code']}")
            st.write(f"**Cargo:** {ultimo_registro['Cargo']}")
            st.write(f"**Gestor:** {ultimo_registro['Gestor']}")
            st.write(f"**Descrição em 2024:** {ultimo_registro['Descricao em 2024']}")
    else:
        st.error("Base de substituição não carregada.")

elif modo_busca == "Gestor e Cargo":
    if base_substituicao is not None:
        gestor = st.selectbox("Selecione o gestor:", sorted(base_substituicao['Gestor'].dropna().unique()))
        if gestor:
            cargos_filtrados = base_substituicao[base_substituicao['Gestor'] == gestor]['Cargo'].dropna().unique()
            cargo = st.selectbox("Selecione o cargo:", sorted(cargos_filtrados))
        else:
            cargo = None

        if cargo:
            resultado = base_substituicao[
                (base_substituicao['Gestor'] == gestor) & (base_substituicao['Cargo'] == cargo)
            ].sort_values(by='Data Referencia', ascending=False)

            if not resultado.empty:
                st.markdown("### Resultados Encontrados")
                job_codes_exibidos = set()
                for _, linha in resultado.iterrows():
                    job_code = linha['Job Code']
                    if job_code not in job_codes_exibidos:
                        job_codes_exibidos.add(job_code)
                        st.write(f"**Job Code:** {job_code}")
                        st.write(f"**Título:** {linha['Titulo Job Code']}")
                        st.write(f"**Descrição em 2024:** {linha['Descricao em 2024']}")
            else:
                st.warning("Nenhum resultado encontrado para a combinação selecionada.")
        else:
            st.warning("Por favor, selecione um cargo válido.")
    else:
        st.error("Base de substituição não carregada.")
