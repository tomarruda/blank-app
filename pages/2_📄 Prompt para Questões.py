import streamlit as st
import json
import os

st.title("🧪 Gerador de Prompt para Questões de Química")

# Upload do arquivo JSON
uploaded_file = st.file_uploader("📂 Faça o upload de um arquivo JSON contendo os conceitos de química", type=["json"])

if uploaded_file is not None:
    conceitos_quimica = json.load(uploaded_file)
else:
    conceitos_quimica = {}
    st.warning("⚠️ Aguarde o upload de um arquivo JSON para continuar.")

# Título do Questionário
titulo_questionario = st.text_input("📜 Digite o título do questionário:")

# Escolha do número de questões
total_questoes = st.slider("🔢 Número de questões:", min_value=1, max_value=20, value=5)

# Escolha do número de conceitos por questão
num_conceitos = st.slider("📚 Número de conceitos por questão:", min_value=1, max_value=3, value=2)

# Escolha do número máximo de questões por conteúdo
max_questoes_por_conteudo = st.slider("📊 Número máximo de questões por conteúdo:", min_value=1, max_value=10, value=4)

st.write("### 🏗️ Escolha os conteúdos e conceitos desejados")

# Estado da seleção armazenado na sessão do usuário
if "conceitos_selecionados" not in st.session_state:
    st.session_state.conceitos_selecionados = set()

# Criar expanders apenas para os conteúdos carregados do JSON
for conteudo, topicos in conceitos_quimica.items():
    with st.expander(f"📂 {conteudo}"):
        selecionar_conteudo = st.checkbox(f"✅ {conteudo}", key=f"{conteudo}_todos", value=False)
        if selecionar_conteudo:
            for topico, subtitulos in topicos.items():
                for subtopico in subtitulos:
                    st.session_state.conceitos_selecionados.add(f"{conteudo} - {topico} - {subtopico}")
        
        for topico, subtitulos in topicos.items():
            selecionar_topico = st.checkbox(f"📖 {topico}", key=f"{conteudo}_{topico}_todos", value=False)
            if selecionar_topico:
                for subtopico in subtitulos:
                    st.session_state.conceitos_selecionados.add(f"{conteudo} - {topico} - {subtopico}")
            
            for subtopico in subtitulos:
                selecionar_subtopico = st.checkbox(f"🔬 {subtopico}", key=f"{conteudo}_{topico}_{subtopico}", value=False)
                if selecionar_subtopico:
                    st.session_state.conceitos_selecionados.add(f"{conteudo} - {topico} - {subtopico}")

# Exibir conceitos selecionados
st.write("### 📌 Conceitos Selecionados:")
if st.session_state.conceitos_selecionados:
    st.write("✔️ " + "\n✔️ ".join(st.session_state.conceitos_selecionados))
else:
    st.write("⚠️ Nenhum conceito selecionado ainda.")

# Determinar como expressar o número de conceitos no prompt
txt_num_conceitos = "um único conceito" if num_conceitos == 1 else f"entre 1 e {num_conceitos} conceitos simultaneamente"

# Criar Prompt
if st.button("📝 Gerar Prompt e Exibir Texto"):
    if not st.session_state.conceitos_selecionados:
        st.error("⚠️ Por favor, selecione pelo menos um conceito antes de gerar o prompt.")
    else:
        prompt_text = (
            f"Gere {total_questoes} questões de múltipla escolha baseadas nos seguintes conteúdos de química: "
            f"{', '.join(st.session_state.conceitos_selecionados)}. "
            f"Cada questão deve abordar {txt_num_conceitos} e ter quatro alternativas (A, B, C e D), "
            "com apenas uma alternativa correta. A complexidade das questões deve ser apropriada para estudantes universitários. "
            f"No máximo {max_questoes_por_conteudo} questões podem ser geradas para cada conteúdo. "
            "As questões devem ser variadas, cobrindo aspectos conceituais, teóricos e aplicações práticas dos conceitos selecionados. "
            "Certifique-se de que cada questão tenha apenas uma resposta correta e que as alternativas erradas sejam plausíveis. "
            "Use a formatação adequada para química, incluindo subscrito para fórmulas moleculares (exemplo: H₂O) e sobrescrito para cargas iônicas (exemplo: Ca²⁺). "
            "O resultado deve ser salvo em um arquivo JSON contendo uma lista de questões no seguinte formato:\n\n"
            "[\n"
            "    {\n"
            "        \"question\": \"Qual é a equação correta para a entalpia padrão de formação da água líquida?\",\n"
            "        \"options\": [\"A) H₂(g) + 1/2 O₂(g) → H₂O(l)\", \"B) H₂O(g) → H₂(g) + 1/2 O₂(g)\", \"C) 2H₂(g) + O₂(g) → 2H₂O(l)\", \"D) H₂O(l) → H₂(g) + 1/2 O₂(g)\"],\n"
            "        \"answer\": \"A) H₂(g) + 1/2 O₂(g) → H₂O(l)\",\n"
            "        \"tags\": {\"conteúdo\": \"Termoquímica\", \"tópico\": \"Reações de Formação\", \"subtópico\": \"Energia\"}\n"
            "    }\n"
            "]"
        )
        
        st.write("### ✨ Prompt Gerado:")
        st.text_area("Copie este prompt para rodar em uma LLM:", prompt_text, height=400)
        
        # Salvar prompt como JSON
        prompt_data = {
            "titulo": titulo_questionario,
            "numero_questoes": total_questoes,
            "conceitos_por_questao": num_conceitos,
            "max_questoes_por_conteudo": max_questoes_por_conteudo,
            "conceitos_selecionados": list(st.session_state.conceitos_selecionados),
            "prompt_text": prompt_text
        }
        
        prompt_file_path = "prompt_questoes.json"
        with open(prompt_file_path, "w", encoding="utf-8") as file:
            json.dump(prompt_data, file, ensure_ascii=False, indent=4)
        
        st.download_button(label="⬇️ Baixar JSON do Prompt", data=json.dumps(prompt_data, indent=4, ensure_ascii=False), file_name=prompt_file_path, mime="application/json")
