import streamlit as st
import os
import pandas as pd

# 🔹 Configuração da página
st.set_page_config(page_title="Painel do Aluno", page_icon="🎓", initial_sidebar_state="collapsed")

st.title("🎓 Painel do Aluno")

# 🔹 Verifica login ativo
if "aluno_logado" not in st.session_state:
    st.error("⚠️ Você precisa fazer login primeiro!")
    st.stop()

# 📌 Exibe informações do aluno
st.success(f"Bem-vindo, {st.session_state.nome_aluno}!")
st.info(f"Disciplinas: {st.session_state.disciplinas}")


# 🔹 Caminhos organizados
BASE_DIR = os.path.dirname(__file__)  # Diretório base
QUIZ_DIR = os.path.join(BASE_DIR, "questionarios_py")  # Caminho correto para os quizzes
RESULTADOS_DIR = os.path.join(BASE_DIR, "resultados_csv")  # Caminho correto para os resultados
os.makedirs(RESULTADOS_DIR, exist_ok=True)  # Garante que a pasta de resultados existe

# 🔍 Mapeamento das disciplinas para seus códigos de 3 letras
codigos_disciplinas = {
    "Introdução ao Laboratório de Química": "ILQ",
    "Química Geral Experimental": "QEX",
    "Química Inorgânica I": "QIT",
    "Química Inorgânica Exp.": "QIE",
    "Mineralogia": "MIN",
}

# 📌 Obtém os códigos das disciplinas do aluno
disciplinas_aluno = st.session_state.disciplinas.split(", ")
codigos_aluno = [codigos_disciplinas[disciplina] for disciplina in disciplinas_aluno if disciplina in codigos_disciplinas]

# 🔎 Lista todos os arquivos de quiz na pasta `pages/questionarios_py/` e filtra por prefixo
quizzes_disponiveis = []
if os.path.exists(QUIZ_DIR):
    for arquivo in os.listdir(QUIZ_DIR):
        if arquivo.endswith(".py"):  # Apenas arquivos .py
            quiz_prefixo = arquivo.split("_")[0]  # Obtém o prefixo (ex: "ILQ", "QEX")
            if quiz_prefixo in codigos_aluno:  # Verifica se pertence às disciplinas do aluno
                quizzes_disponiveis.append(arquivo.replace(".py", ""))  # Remove extensão


# 🔍 Verifica quais quizzes já foram concluídos pelo aluno
quizzes_concluidos = []
quizzes_pendentes = []

for quiz in quizzes_disponiveis:
    csv_filename = f"resultados_{quiz}.csv"
    csv_path = os.path.join(RESULTADOS_DIR, csv_filename)

    if os.path.exists(csv_path):
        df_resultados = pd.read_csv(csv_path, dtype=str)
        

        # 🔍 Filtrar SOMENTE as respostas do aluno logado
        aluno_respostas = df_resultados[df_resultados["E-mail"].str.strip() == st.session_state.aluno_logado]

        if not aluno_respostas.empty:
            # 🔹 Pegamos o último status do quiz, removendo espaços extras
            status_quiz = aluno_respostas["Status"].dropna().values[-1].strip().lower()

            if status_quiz in ["concluído", "concluido", "finalizado"]:
                quizzes_concluidos.append(quiz)  # ✅ Move para concluídos
            else:
                quizzes_pendentes.append(quiz)
        else:
            st.warning(f"⚠️ Nenhuma resposta encontrada para {st.session_state.aluno_logado} no {quiz}.")
            quizzes_pendentes.append(quiz)
    else:
        st.warning(f"⚠️ Arquivo CSV não encontrado para {quiz}!")
        quizzes_pendentes.append(quiz)


# 📜 **Exibir quizzes pendentes (Verde)**
st.subheader("✅ Quizzes Disponíveis (A serem respondidos)")

if quizzes_pendentes:
    for quiz in quizzes_pendentes:
        quiz_name = quiz.replace("_", " ")

        # ✅ Botão que salva o nome do quiz e recarrega a página
        if st.button(f"🟩 {quiz_name}", key=f"pendente_{quiz}"):
            st.session_state.quiz_atual = quiz  # 🔹 Armazena o nome do quiz
            st.rerun()  # 🔹 Recarrega a página para iniciar o quiz
else:
    st.info("Nenhum quiz pendente no momento.")


# 🚀 **Executa o Quiz Selecionado**
if "quiz_atual" in st.session_state:
    quiz_nome = st.session_state.quiz_atual  # Nome correto do quiz
    quiz_path = os.path.join(QUIZ_DIR, f"{quiz_nome}.py")

    if os.path.exists(quiz_path):
        with open(quiz_path, "r", encoding="utf-8") as file:
            exec(file.read())  # 🔹 Executa o código do quiz diretamente
    else:
        st.error(f"❌ Erro: O arquivo do quiz `{quiz_path}` não foi encontrado.")


# 📜 **Exibir quizzes concluídos (Vermelho)**
st.subheader("❌ Quizzes Concluídos")

if quizzes_concluidos:
    for quiz in quizzes_concluidos:
        quiz_name = quiz.replace("_", " ")
        st.button(f"🟥 {quiz_name}", key=f"concluido_{quiz}", disabled=True)  # 🔹 Botão desativado
else:
    st.info("Nenhum quiz concluído ainda.")
