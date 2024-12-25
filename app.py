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
                        
                        # Seleção do nível de carreira
                        nivel_carreira = st.selectbox(
                            "Selecione o nível de carreira:",
                            list(NIVEIS_CARREIRA.keys()),
                            key=f"nivel_{i}"
                        )
                        
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
