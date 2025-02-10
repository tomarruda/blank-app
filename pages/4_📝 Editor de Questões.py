import streamlit as st
import json
import uuid
import os

def load_questions():
    """Carrega as questões do arquivo JSON armazenado localmente."""
    if os.path.exists("all_questions.json"):
        with open("all_questions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_questions(questions):
    """Salva todas as questões em um único arquivo JSON."""
    with open("all_questions.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)

def reset_question_form():
    """Reseta os campos do formulário sem causar erro de redefinição de sessão."""
    st.session_state["show_add_question"] = False
    st.session_state["answer_selected"] = False
    st.session_state["preview_visible"] = False

def main():
    st.set_page_config(layout="wide")  # Define a página como wide
    st.title("Gerenciador de Questões de Química")
    
    tab1, tab2 = st.tabs(["Adicionar Questões", "Gerenciar Questões"])
    
    with tab1:
        st.header("Adicionar Nova Questão")
        uploaded_file = st.file_uploader("Faça o upload do arquivo JSON", type=["json"])
        
        if uploaded_file is not None:
            questions = load_questions()
            new_questions = json.load(uploaded_file)
            
            existing_questions = {q["question"]: q for q in questions}
            for q in new_questions:
                if q["question"] not in existing_questions:
                    q["id"] = str(uuid.uuid4())
                    questions.append(q)
            
            save_questions(questions)
            st.success("Questões do arquivo adicionadas com sucesso!")
        
        if st.button("Adicionar Nova Questão Manualmente"):
            st.session_state["show_add_question"] = True
        
        if st.session_state.get("show_add_question", False):
            with st.expander("Nova Questão", expanded=True):
                new_question = st.text_area("Enunciado da questão", key="new_question")
                new_options = [st.text_input(f"Opção {i+1}", key=f"opt_{i}") for i in range(4)]
                new_content = st.text_input("Conteúdo", key="new_content")
                new_topic = st.text_input("Tópico", key="new_topic")
                new_subtopic = st.text_input("Subtópico", key="new_subtopic")
                
                if st.button("Escolher Resposta Correta") and all(new_options):
                    st.session_state["answer_selected"] = True
                
                if st.session_state.get("answer_selected", False):
                    new_answer = st.selectbox("Escolha a resposta correta", new_options, key="new_answer")
                else:
                    new_answer = ""
                
                if st.button("Visualizar Questão"):
                    st.session_state["preview_visible"] = True
                
                if st.session_state.get("preview_visible", False) and all([
                    new_question, 
                    all(new_options), 
                    new_answer, 
                    new_content, 
                    new_topic, 
                    new_subtopic
                ]):
                    st.subheader("Prévia da Questão")
                    st.write(f"<h4>{new_question}</h4>", unsafe_allow_html=True)
                    for opt in new_options:
                        st.write(f"- {opt}")
                    st.write(f"**Resposta Correta:** {new_answer}")
                    st.write(f"**Tags:** {new_content} → {new_topic} → {new_subtopic}")
                
                if st.button("Salvar Questão") and st.session_state.get("preview_visible", False):
                    questions = load_questions()
                    new_q = {
                        "id": str(uuid.uuid4()),
                        "question": new_question,
                        "options": new_options,
                        "answer": new_answer,
                        "tags": {"content": new_content, "topic": new_topic, "subtopic": new_subtopic}
                    }
                    questions.append(new_q)
                    save_questions(questions)
                    st.success("Nova questão adicionada com sucesso!")
                    reset_question_form()
    
    with tab2:
        st.header("Gerenciar Questões")
        questions = load_questions()
        
        content_options = list(set(q["tags"]["content"] for q in questions))
        selected_contents = st.multiselect("Filtrar por Conteúdo", content_options)
        
        topic_options = list(set(q["tags"]["topic"] for q in questions if q["tags"]["content"] in selected_contents))
        selected_topics = st.multiselect("Filtrar por Tópico", topic_options)
        
        subtopic_options = list(set(q["tags"].get("subtopic", "") for q in questions if q["tags"]["topic"] in selected_topics))
        selected_subtopics = st.multiselect("Filtrar por Subtópico", subtopic_options)
        
        filtered_questions = [
            q for q in questions
            if (not selected_contents or q["tags"]["content"] in selected_contents) and
               (not selected_topics or q["tags"]["topic"] in selected_topics) and
               (not selected_subtopics or q["tags"].get("subtopic", "") in selected_subtopics)
        ]
        
        st.write(f"Total de questões: {len(filtered_questions)}")
        
        selected_questions = []
        
        for q in filtered_questions:
            with st.expander(f"{q['question']}", expanded=False):
                st.markdown(f"## {q['question']}")
                st.markdown(
                    f"<span style='background-color:#FFD700;padding:4px;border-radius:5px;'>📌 {q['tags']['content']}</span> "
                    f"<span style='background-color:#ADD8E6;padding:4px;border-radius:5px;'>📌 {q['tags']['topic']}</span> "
                    f"<span style='background-color:#90EE90;padding:4px;border-radius:5px;'>📌 {q['tags'].get('subtopic', '')}</span>",
                    unsafe_allow_html=True
                )
                selected = st.checkbox("Selecionar", key=f"select_{q['id']}")
                if selected:
                    selected_questions.append(q)
                st.write("**Opções:**")
                for opt in q["options"]:
                    st.write(f"- {opt}")
                st.write(f"**Resposta Correta:** {q['answer']}")
                if st.button(f"Editar {q['id']}", key=f"edit_{q['id']}"):
                    st.text_area("Editar Pergunta", value=q['question'], key=f"edit_q_{q['id']}")
                if st.button(f"Remover {q['id']}", key=f"remove_{q['id']}"):
                    questions = [question for question in questions if question["id"] != q["id"]]
                    save_questions(questions)
                    st.rerun()
    
if __name__ == "__main__":
    main()

