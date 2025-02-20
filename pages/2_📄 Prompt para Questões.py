import streamlit as st
import json

st.title("🧪 Gerador de Prompt para Questões de Química")

# Upload do arquivo JSON
uploaded_file = st.file_uploader("📂 Faça o upload de um arquivo JSON contendo os conceitos de química", type=["json"])

# Carregar o JSON corretamente
if uploaded_file is not None:
    try:
        conceitos_quimica = json.load(uploaded_file)
    except json.JSONDecodeError:
        st.error("❌ Erro ao carregar o JSON. Certifique-se de que o arquivo está formatado corretamente.")
        conceitos_quimica = []
else:
    conceitos_quimica = []
    st.warning("⚠️ Aguarde o upload de um arquivo JSON para continuar.")

# Inicializar session_state corretamente como um dicionário
if "conceitos_selecionados" not in st.session_state:
    st.session_state.conceitos_selecionados = {}

# Título do Questionário
titulo_questionario = st.text_input("📜 Digite o título do questionário:")

# Escolha do número de questões
total_questoes = st.slider("🔢 Número de questões:", min_value=1, max_value=20, value=5)

# Escolha do número de conceitos por questão
num_conceitos = st.slider("📚 Número de conceitos por questão:", min_value=1, max_value=3, value=2)

# Escolha do número máximo de questões por conteúdo
max_questoes_por_conteudo = st.slider("📊 Número máximo de questões por conteúdo:", min_value=1, max_value=10, value=4)

st.write("### 🏗️ Escolha os conteúdos e conceitos desejados")

# Criar expanders para os conteúdos carregados do JSON
if isinstance(conceitos_quimica, list):
    for idx_conteudo, conteudo_data in enumerate(conceitos_quimica):
        conteudo = conteudo_data["content"]
        topicos = conteudo_data["topics"]

        with st.expander(f"📂 {conteudo}"):
            selecionar_conteudo = st.checkbox(f"✅ {conteudo}", key=f"conteudo_{idx_conteudo}", value=False)
            if selecionar_conteudo:
                if conteudo not in st.session_state.conceitos_selecionados:
                    st.session_state.conceitos_selecionados[conteudo] = {}

                for topico_data in topicos:
                    topico = topico_data["topic"]
                    subtitulos = topico_data["subtopics"]
                    st.session_state.conceitos_selecionados[conteudo][topico] = subtitulos

            for idx_topico, topico_data in enumerate(topicos):
                topico = topico_data["topic"]
                subtitulos = topico_data["subtopics"]

                selecionar_topico = st.checkbox(f"📖 {topico}", key=f"topico_{idx_conteudo}_{idx_topico}", value=False)
                if selecionar_topico:
                    if conteudo not in st.session_state.conceitos_selecionados:
                        st.session_state.conceitos_selecionados[conteudo] = {}
                    st.session_state.conceitos_selecionados[conteudo][topico] = subtitulos

                for idx_subtopico, subtopico in enumerate(subtitulos):
                    selecionar_subtopico = st.checkbox(
                        f"🔬 {subtopico}",
                        key=f"subtopico_{idx_conteudo}_{idx_topico}_{idx_subtopico}",
                        value=False
                    )
                    if selecionar_subtopico:
                        if conteudo not in st.session_state.conceitos_selecionados:
                            st.session_state.conceitos_selecionados[conteudo] = {}
                        if topico not in st.session_state.conceitos_selecionados[conteudo]:
                            st.session_state.conceitos_selecionados[conteudo][topico] = []
                        if subtopico not in st.session_state.conceitos_selecionados[conteudo][topico]:
                            st.session_state.conceitos_selecionados[conteudo][topico].append(subtopico)
else:
    st.error("⚠️ Estrutura do JSON inválida. Certifique-se de que ele segue o formato correto.")

# Exibir conceitos selecionados com hierarquia mantida
st.write("### 📌 Conceitos Selecionados:")
if st.session_state.conceitos_selecionados:
    for conteudo, topicos in st.session_state.conceitos_selecionados.items():
        st.write(f"📂 **{conteudo}**")
        for topico, subtitulos in topicos.items():
            st.write(f"   📖 {topico}")
            for subtopico in subtitulos:
                st.write(f"      🔬 {subtopico}")
else:
    st.write("⚠️ Nenhum conceito selecionado ainda.")

# Determinar como expressar o número de conceitos no prompt
txt_num_conceitos = "um único conceito" if num_conceitos == 1 else f"entre 1 e {num_conceitos} conceitos simultaneamente"

# Criar Prompt
if st.button("📝 Gerar Prompt e Exibir Texto"):
    if not st.session_state.conceitos_selecionados:
        st.error("⚠️ Por favor, selecione pelo menos um conceito antes de gerar o prompt.")
    else:
        conceitos_agrupados = list(st.session_state.conceitos_selecionados)  # Usar todos os conceitos selecionados
        prompt_text = (
            f"Gere {total_questoes} questões de múltipla escolha correlacionando os seguintes conceitos de química: "
            f"{', '.join([f'{c} - {t} - {s}' for c, t, s in conceitos_agrupados])}. "
            f"Cada questão deve correlacionar {len(conceitos_agrupados)} conceitos distintos e ter quatro alternativas (A, B, C e D), "
            "com apenas uma alternativa correta. A complexidade das questões deve ser apropriada para estudantes universitários. "
            f"No máximo {max_questoes_por_conteudo} questões podem ser geradas para cada conteúdo. "
            "As questões devem ser variadas, cobrindo aspectos conceituais, teóricos e aplicações práticas dos conceitos selecionados. "
            "Certifique-se de que cada questão tenha apenas uma resposta correta e que as alternativas erradas sejam plausíveis. "
            "Use a formatação adequada para química, incluindo subscrito para fórmulas moleculares (exemplo: H₂O) e sobrescrito para cargas iônicas (exemplo: Ca²⁺). "
            "O JSON gerado deve conter a seguinte estrutura:\n\n"
            "[\n"
            "    {\n"
            "        \"question\": \"Qual é a equação correta para a entalpia padrão de formação da água líquida?\",\n"
            "        \"options\": [\"A) H₂(g) + 1/2 O₂(g) → H₂O(l)\", \"B) H₂O(g) → H₂(g) + 1/2 O₂(g)\", \"C) 2H₂(g) + O₂(g) → 2H₂O(l)\", \"D) H₂O(l) → H₂(g) + 1/2 O₂(g)\"],\n"
            "        \"answer\": \"A) H₂(g) + 1/2 O₂(g) → H₂O(l)\",\n"
            "        \"tags\": {\"content\": \"Termoquímica\", \"topic\": \"Reações de Formação\", \"subtopic\": \"Energia\"}\n"
            "    }\n"
            "]"
            f"Hierarquia de conteúdos carregados:\n{json.dumps(conteudos_quimica, indent=4, ensure_ascii=False)}\n\n"
        )
        
        st.write("### ✨ Prompt Gerado:")
        st.text_area("Copie este prompt para rodar em uma LLM:", prompt_text, height=400)
        
        # Salvar prompt como JSON
        prompt_data = {
            "titulo": titulo_questionario,
            "numero_questoes": total_questoes,
            "conceitos_por_questao": num_conceitos,
            "max_questoes_por_conteudo": max_questoes_por_conteudo,
            "conceitos_selecionados": st.session_state.conceitos_selecionados,
            "prompt_text": prompt_text
        }

        st.download_button(
            label="⬇️ Baixar JSON do Prompt",
            data=json.dumps(prompt_data, indent=4, ensure_ascii=False),
            file_name="prompt_questoes.json",
            mime="application/json"
        )