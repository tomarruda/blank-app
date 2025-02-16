import streamlit as st
import pandas as pd
import os

# 🔹 Configuração da Página
st.set_page_config(page_title="Login do Aluno", page_icon="🔑", initial_sidebar_state="collapsed")

st.title("🔑 Login do Aluno")

# 🔹 Caminho do banco de dados
BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "..", "banco_de_dados", "alunos.csv")  # Caminho correto do CSV

# 🔍 **Verifica se o banco de dados existe**
if not os.path.exists(CSV_PATH):
    st.error("❌ Erro: O banco de dados de alunos não foi encontrado.")
    st.stop()

# 🔹 Carrega a base de alunos
df_alunos = pd.read_csv(CSV_PATH, dtype=str)

# 🔹 **Se o aluno já estiver logado, redireciona para a Página do Aluno**
if "aluno_logado" in st.session_state and st.session_state.aluno_logado:
    st.success(f"✅ Você já está logado como **{st.session_state.nome_aluno}**!")
    if st.button("Ir para o Painel do Aluno"):
        st.switch_page("pages/7_👨🏻‍🎓Página_do_Aluno.py")
    st.stop()

# 🔹 **Formulário de Login**
with st.form("login_form"):
    email = st.text_input("📧 E-mail do aluno:")
    cpf = st.text_input("🔑 CPF (somente números):")
    submit = st.form_submit_button("Entrar")

if submit:
    aluno = df_alunos[(df_alunos["E-mail"].str.strip() == email.strip()) & (df_alunos["CPF"].str.strip() == cpf.strip())]

    if not aluno.empty:
        st.session_state.aluno_logado = aluno["E-mail"].values[0].strip()  # 🔹 Salva o e-mail correto
        st.session_state.nome_aluno = aluno["Nome"].values[0].strip()  # 🔹 Nome sem espaços extras
        st.session_state.disciplinas = aluno["Disciplinas"].values[0].strip()  # 🔹 Disciplinas corretas

        st.success(f"✅ Bem-vindo, {st.session_state.nome_aluno}!")
        st.switch_page("pages/7_👨🏻‍🎓Página_do_Aluno.py")  # 🔄 Redireciona para a página do aluno
    else:
        st.error("❌ E-mail ou CPF inválido. Verifique suas credenciais e tente novamente.")