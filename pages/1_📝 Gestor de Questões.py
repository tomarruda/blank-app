import streamlit as st
import json
import uuid
import os
from datetime import datetime
import textwrap

# Configuração da página em modo wide
st.set_page_config(layout="wide")

# ─── Constantes de Pastas ───────────────────────────────────────────────
JSON_OUTPUT_DIR = "/workspaces/blank-app/pages/questionarios_json"
PY_OUTPUT_DIR = "/workspaces/blank-app/pages/questionarios_py"

# Cria as pastas se não existirem
os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
os.makedirs(PY_OUTPUT_DIR, exist_ok=True)

# ─── Funções de Carregamento e Salvamento de Questões ─────────────────────

def load_questions():
    """Carrega todas as questões do arquivo central 'all_questions.json'."""
    if os.path.exists("all_questions.json"):
        with open("all_questions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_questions(questions):
    temp_filename = "all_questions_temp.json"

    # Salva as questões em um arquivo temporário primeiro
    with open(temp_filename, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)
    
    # Garante que os dados são gravados antes de substituir o arquivo original
    os.replace(temp_filename, "all_questions.json")

    print("✅ QUESTÕES SALVAS COM SUCESSO!")

# ─── Função para Gerar o Script do Quiz ────────────────────────────────────
def generate_quiz_script(quiz_name, json_filename, py_filename):
    script_content = f"""
import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime

# 🔹 Configuração do quiz
P_C_given_A = {{0: 0.308, 1: 0.632, 2: 0.857, 3: 0.973}}
alpha_values = {{0: 0.25, 1: 0.5, 2: 0.75, 3: 1.0}}

# 🔹 Verifica login ativo
if "aluno_logado" not in st.session_state:
    st.error("⚠️ Você precisa fazer login primeiro!")
    st.stop()

# ✅ **Corrige o Nome do Quiz**
if "quiz_atual" in st.session_state:
    quiz_nome = st.session_state.quiz_atual  # Nome correto do quiz
else:
    st.error("❌ Erro: Nenhum quiz foi selecionado corretamente.")
    st.stop()

# 📌 Caminho do arquivo CSV de resultados
csv_path = os.path.join("pages/resultados_csv", f"resultado_{{quiz_nome}}.csv")

# 🔍 Bloqueia o acesso se o quiz já foi respondido
if os.path.exists(csv_path):
    df_resultados = pd.read_csv(csv_path, dtype=str)
    if (df_resultados["E-mail"] == st.session_state.aluno_logado).any():
        status_quiz = df_resultados[df_resultados["E-mail"] == st.session_state.aluno_logado]["Status"].values[-1]
        if status_quiz.lower().strip() == "concluído":
            st.warning("⚠️ Você já respondeu este quiz antes! Seus resultados já foram registrados.")
            st.stop()  # 🔹 Bloqueia o quiz e impede recomeço

# 🔹 Caminho correto para os arquivos JSON
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Sobe um nível para a pasta principal
JSON_DIR = os.path.join(BASE_DIR, "pages", "questionarios_json")  # 🔹 Nome da pasta sem acentos
json_path = os.path.join(JSON_DIR, f"{{quiz_nome}}.json")

# 🔹 Carrega as questões do quiz
with open(json_path, "r", encoding="utf-8") as file:
    st.session_state.questoes = json.load(file)

# 🔹 Inicializa variáveis de sessão
if "quiz_iniciado" not in st.session_state:
    st.session_state.quiz_iniciado = False
if "tempo_inicio" not in st.session_state:
    st.session_state.tempo_inicio = None
if "questao_atual" not in st.session_state:
    st.session_state.questao_atual = 0
if "respostas_aluno" not in st.session_state:
    st.session_state.respostas_aluno = {{}}
if "niveis_conf" not in st.session_state:
    st.session_state.niveis_conf = {{}}
if "finalizou_quiz" not in st.session_state:
    st.session_state.finalizou_quiz = False

# 🔹 Inicia o quiz automaticamente
if not st.session_state.quiz_iniciado:
    st.session_state.quiz_iniciado = True
    st.session_state.tempo_inicio = datetime.now()

# 🔹 Processamento das questões
if st.session_state.quiz_iniciado and not st.session_state.finalizou_quiz:
    questoes = st.session_state.questoes
    total_questoes = len(questoes)
    questao_atual = st.session_state.questao_atual

    questao = questoes[questao_atual]
    st.subheader(f"Questão {{questao_atual + 1}} de {{total_questoes}}")
    st.markdown(f"<p style='font-size:20px'>{{questao['question']}}</p>", unsafe_allow_html=True)
    resposta = st.radio("Selecione a resposta:", questao["options"], key=f"questao_{{questao_atual}}")
    nivel_conf = st.slider("Nível de confiança na resposta (0: Baixa confiança → 3: Alta confiança)", 0, 3, 1, key=f"conf_{{questao_atual}}")

    if st.button("Avançar"):
        st.session_state.respostas_aluno[questao_atual] = resposta
        st.session_state.niveis_conf[questao_atual] = nivel_conf
        if questao_atual + 1 < total_questoes:
            st.session_state.questao_atual += 1
            st.rerun()
        else:
            st.session_state.finalizou_quiz = True
            st.rerun()

# 🔹 Salvar os resultados ao final do quiz com pontuação ajustada
if st.session_state.finalizou_quiz and st.session_state.questoes is not None:
    CSV_FILE = f"resultados_{{quiz_nome}}.csv"
    questoes = st.session_state.questoes

    pontuacao_final = 0
    acertos = 0
    erros = 0
    nome_aluno = st.session_state.get("nome_aluno", "Aluno")
    email_aluno = st.session_state.get("aluno_logado", "email_não_definido")
    resultados_aluno = {{
        "Nome": nome_aluno,
        "E-mail": email_aluno
    }}

    for i, questao in enumerate(questoes):
        resposta_correta = questao['answer']
        resposta_escolhida = st.session_state.respostas_aluno[i]
        nivel_conf = st.session_state.niveis_conf[i]

        tags = questao.get("tags", {{}})
        contents = tags.get("content", "NÃO ENCONTRADO")
        topics = tags.get("topic", "NÃO ENCONTRADO")
        subtopics = tags.get("subtopic", "NÃO ENCONTRADO")

        # Inclui o ID da questão no CSV
        questao_id = questao.get("id", f"Q{{i+1}}")

        P_C_E = 1 - P_C_given_A[nivel_conf]
        acertou = resposta_escolhida == resposta_correta
        if acertou:
            pontuacao_final += P_C_given_A[nivel_conf]
            acertos += 1
        else:
            pontuacao_final += -alpha_values[nivel_conf] * (1 - P_C_E)
            erros += 1

        resultados_aluno[f"Q{{i+1}}_ID"] = questao_id
        resultados_aluno[f"Q{{i+1}}_Acertou"] = "Sim" if acertou else "Não"
        resultados_aluno[f"Q{{i+1}}_Confiança"] = nivel_conf
        resultados_aluno[f"Q{{i+1}}_Contents"] = contents
        resultados_aluno[f"Q{{i+1}}_Topics"] = topics
        resultados_aluno[f"Q{{i+1}}_Subtopics"] = subtopics

    horario_finalizacao = datetime.now()
    tempo_total = horario_finalizacao - st.session_state.tempo_inicio
    tempo_total_formatado = f"{{tempo_total.seconds // 60}}:{{tempo_total.seconds % 60:02d}}"

    resultados_aluno["Acertos Totais"] = acertos
    resultados_aluno["Pontuação Ajustada"] = pontuacao_final
    resultados_aluno["Horário Finalização"] = horario_finalizacao.strftime("%Y-%m-%d %H:%M:%S")
    resultados_aluno["Tempo Total"] = tempo_total_formatado
    resultados_aluno["Status"] = "concluído"

    RESULTADOS_DIR = "/workspaces/blank-app/pages/resultados_csv"   
    os.makedirs(RESULTADOS_DIR, exist_ok=True)

    CSV_FILE = os.path.join(RESULTADOS_DIR, f"resultados_{{quiz_nome}}.csv")

    df_resultado = pd.DataFrame([resultados_aluno])
    if os.path.exists(CSV_FILE):
        df_resultado.to_csv(CSV_FILE, mode='a', header=False, index=False)
    else:
        df_resultado.to_csv(CSV_FILE, mode='w', header=True, index=False)

    st.success(f"{{st.session_state.nome_aluno}}, você finalizou o quiz!")
    st.write(f"**Número de acertos:** {{acertos}}")
    st.write(f"**Pontuação final ajustada:** {{pontuacao_final:.2f}}")
    st.write(f"**Tempo total:** {{tempo_total_formatado}}")
"""
    
    # 🔹 Escrevendo o script para um arquivo Python
    with open(py_filename, "w", encoding="utf-8") as f:
        f.write(script_content)

    st.success(f"✅ Script do Quiz gerado em: {py_filename}")

# ─── Inicializa variável para questões selecionadas para o Quiz ───────────
if "selected_for_quiz" not in st.session_state:
    st.session_state.selected_for_quiz = {}

# ─── Interface com 3 abas ─────────────────────────────────────────────────

st.title("Gerenciador e Gerador de Questionário")
tabs = st.tabs(["Adicionar Questões", "Gerenciar Questões", "Gerador de Questionário"])

# ─── Aba 1: Adicionar Questões ─────────────────────────────────────────────

with tabs[0]:
    st.header("Adicionar Questões")
    
    st.subheader("Importar Arquivo JSON")
    uploaded_file = st.file_uploader("Selecione um arquivo JSON com questões", type=["json"], key="upload_questions")
    if uploaded_file is not None:
        try:
            imported_questions = json.load(uploaded_file)
            print(f"✅ QUESTÕES IMPORTADAS DO JSON ({len(imported_questions)}):", imported_questions)  # Debug
        except Exception as e:
            st.error(f"❌ Erro ao ler o JSON: {e}")
            imported_questions = []

        if imported_questions:
            all_q = load_questions()  # Carrega as questões já salvas no sistema
            print(f"📂 QUESTÕES JÁ EXISTENTES NO BANCO ({len(all_q)}):", all_q)  # Debug

            existentes = {q["question"].strip().lower() for q in all_q}  # Normaliza os enunciados para evitar duplicação
            novas = 0

            for q in imported_questions:
                enunciado = q.get("question", "").strip().lower()  # Remove espaços e normaliza para comparar
                if enunciado and enunciado not in existentes:  # Verifica se a questão já existe
                    if "id" not in q or not q["id"]:
                        q["id"] = str(uuid.uuid4())  # Gera um ID único para a questão
                    print(f"🆕 NOVA QUESTÃO RECEBENDO ID: {q}")  # Debug
                    all_q.append(q)
                    novas += 1
                else:
                    print(f"⚠️ QUESTÃO JÁ EXISTE NO BANCO: q['question']")  # Debug

            print(f"🔄 QUESTÕES FINALIZADAS PARA SALVAR ({len(all_q)}):", all_q)  # Confirmação antes de salvar

            save_questions(all_q)  # Salva as questões atualizadas no all_questions.json

            print(f"📌 TOTAL DE QUESTÕES APÓS IMPORTAÇÃO: {len(all_q)}")  # Debug

        # 🔥 Verifica se realmente foi salvo
        all_q_test = load_questions()
        print(f"📂 VERIFICAÇÃO PÓS-SALVAMENTO ({len(all_q_test)} questões no arquivo JSON):", all_q_test)

        if novas > 0:
            st.success(f"✅ {novas} questão(ões) importada(s) e adicionada(s) com sucesso!")
        else:
            st.warning("⚠️ Nenhuma nova questão foi adicionada. Todas já existem no sistema.")
    else:
        st.error("❌ Nenhuma questão foi carregada do JSON. Verifique o arquivo enviado.")
    
    if st.button("Selecionar todas as questões para o Quiz", key="select_all"):
        all_q = load_questions()
        for q in all_q:
            st.session_state.selected_for_quiz[q["id"]] = q
        st.success("Todas as questões foram selecionadas para o Quiz.")
    
    st.markdown("---")
    st.subheader("Adicionar Questão Manualmente")
    with st.form("form_add_question"):
        new_question = st.text_area("Enunciado da Questão")
        col1, col2 = st.columns(2)
        with col1:
            opt1 = st.text_input("Opção 1", key="opt1")
            opt2 = st.text_input("Opção 2", key="opt2")
        with col2:
            opt3 = st.text_input("Opção 3", key="opt3")
            opt4 = st.text_input("Opção 4", key="opt4")
        new_options = [opt1, opt2, opt3, opt4]
        new_answer = st.selectbox("Selecione a resposta correta", new_options if all(new_options) else [""])
        new_content = st.text_input("Conteúdo")
        new_topic = st.text_input("Tópico")
        new_subtopic = st.text_input("Subtópico")
        submit_manual = st.form_submit_button("Salvar Questão")
        
        if submit_manual:
            if new_question and all(new_options) and new_answer and new_content and new_topic and new_subtopic:
                question_obj = {{
                    "id": str(uuid.uuid4()),
                    "question": new_question,
                    "options": new_options,
                    "answer": new_answer,
                    "tags": {{
                        "content": new_content,
                        "topic": new_topic,
                        "subtopic": new_subtopic
                    }}
                }}
                all_q = load_questions()
                all_q.append(question_obj)
                save_questions(all_q)
                st.success("Questão adicionada com sucesso!")
            else:
                st.error("Por favor, preencha todos os campos.")

# ─── Aba 2: Gerenciar Questões ──────────────────────────────────────────────

with tabs[1]:
    st.header("Gerenciar Questões")
    all_q = load_questions()
    
    total_selecionadas = len(st.session_state.selected_for_quiz)
    st.info(f"Total de questões selecionadas para o Quiz: {total_selecionadas}")
    
    contents = sorted({q["tags"]["content"] for q in all_q})
    selected_contents = st.multiselect("Filtrar por Conteúdo", contents)
    
    topics = sorted({q["tags"]["topic"] for q in all_q if (not selected_contents or q["tags"]["content"] in selected_contents)})
    selected_topics = st.multiselect("Filtrar por Tópico", topics)
    
    subtopics = sorted({q["tags"]["subtopic"] for q in all_q if (not selected_topics or q["tags"]["topic"] in selected_topics)})
    selected_subtopics = st.multiselect("Filtrar por Subtópico", subtopics)
    
    filtered = []
    for q in all_q:
        if selected_contents and q["tags"]["content"] not in selected_contents:
            continue
        if selected_topics and q["tags"]["topic"] not in selected_topics:
            continue
        if selected_subtopics and q["tags"]["subtopic"] not in selected_subtopics:
            continue
        filtered.append(q)
    
    st.write(f"Total de questões filtradas: {len(filtered)}")
    
    for q in filtered:
        selecionada = q["id"] in st.session_state.selected_for_quiz
        if selecionada:
            titulo = f"<p style='font-size:20px; color: green; margin-bottom: 0;'>{q['question']} (Selecionada)</p>"
        else:
            titulo = f"<p style='font-size:20px; margin-bottom: 0;'>{q['question']}</p>"
        st.markdown(titulo, unsafe_allow_html=True)
        
        tags_html = (
            f"<span style='background-color:#FFD700; color:black; padding:2px 4px; border-radius:4px;'>{q['tags']['content']}</span> " +
            f"<span style='background-color:#ADD8E6; color:black; padding:2px 4px; border-radius:4px;'>{q['tags']['topic']}</span> " +
            f"<span style='background-color:#90EE90; color:black; padding:2px 4px; border-radius:4px;'>{q['tags']['subtopic']}</span>"
        )
        st.markdown(tags_html, unsafe_allow_html=True)
        
        selecionado_checkbox = st.checkbox("Selecionar para Quiz", value=selecionada, key=f"select_{q['id']}")
        if selecionado_checkbox:
            st.session_state.selected_for_quiz[q["id"]] = q
        else:
            st.session_state.selected_for_quiz.pop(q["id"], None)
        
        with st.expander("Ver detalhes"):
            st.markdown("**Opções:**")
            for opt in q["options"]:
                st.write(f"- {opt}")
            st.markdown(f"**Resposta Correta:** {q['answer']}")
            
            if st.button("Editar", key=f"edit_{q['id']}"):
                st.session_state.edit_question_id = q["id"]
            
            if st.session_state.get("edit_question_id") == q["id"]:
                st.info("Editando questão:")
                new_q_text = st.text_area("Editar enunciado", value=q["question"], key=f"edit_text_{{q['id']}}")
                new_opts = []
                for i, opt in enumerate(q["options"]):
                    novo_opt = st.text_input(f"Editar opção {{i+1}}", value=opt, key=f"edit_opt_{{q['id']}}_{{i}}")
                    new_opts.append(novo_opt)
                new_ans = st.selectbox("Editar resposta correta", new_opts, key=f"edit_ans_{{q['id']}}")
                new_content = st.text_input("Editar Conteúdo", value=q["tags"]["content"], key=f"edit_content_{{q['id']}}")
                new_topic = st.text_input("Editar Tópico", value=q["tags"]["topic"], key=f"edit_topic_{{q['id']}}")
                new_subtopic = st.text_input("Editar Subtópico", value=q["tags"]["subtopic"], key=f"edit_subtopic_{{q['id']}}")
                if st.button("Salvar Alterações", key=f"save_edit_{{q['id']}}"):
                    for idx, quest in enumerate(all_q):
                        if quest["id"] == q["id"]:
                            all_q[idx]["question"] = new_q_text
                            all_q[idx]["options"] = new_opts
                            all_q[idx]["answer"] = new_ans
                            all_q[idx]["tags"]["content"] = new_content
                            all_q[idx]["tags"]["topic"] = new_topic
                            all_q[idx]["tags"]["subtopic"] = new_subtopic
                            break
                    save_questions(all_q)
                    st.success("Questão atualizada!")
                    st.session_state.pop("edit_question_id", None)
                    st.experimental_rerun()

# ─── Aba 3: Gerador de Questionário ─────────────────────────────────────────

with tabs[2]:
    st.header("Gerador de Questionário")
    
    if st.session_state.selected_for_quiz:
        selecionadas = list(st.session_state.selected_for_quiz.values())
        for quest in selecionadas:
            if "id" not in quest:
                quest["id"] = str(uuid.uuid4())
        quiz_json_path = os.path.join(JSON_OUTPUT_DIR, "quiz_selected.json")
        with open(quiz_json_path, "w", encoding="utf-8") as f:
            json.dump(selecionadas, f, indent=4, ensure_ascii=False)
        st.success(f"Arquivo JSON para Quiz gerado em: {{quiz_json_path}}")
        st.write("As questões selecionadas estão prontas para gerar o quiz.")
    else:
        st.info("Nenhuma questão selecionada para o Quiz. Selecione questões na aba 'Gerenciar Questões'.")
    
    st.markdown("---")
    st.subheader("Gerar Script do Quiz")
    quiz_name = st.text_input("Nome do Questionário para o Quiz", "questionario")
    if st.button("Gerar Script do Quiz"):
        json_filename = os.path.join(JSON_OUTPUT_DIR, f"{quiz_name}.json")
        if st.session_state.selected_for_quiz:
            os.replace(quiz_json_path, json_filename)
            py_filename = os.path.join(PY_OUTPUT_DIR, f"{quiz_name}.py")
            generate_quiz_script(quiz_name, json_filename, py_filename)
        else:
            st.error("Nenhuma questão selecionada para gerar o quiz.")