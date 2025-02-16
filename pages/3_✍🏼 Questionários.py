import streamlit as st
import os

# Diretório onde os questionários são salvos
questionarios_dir = "pages/questionarios_py"

# Obtém a lista de arquivos .py na pasta
arquivos = [f for f in os.listdir(questionarios_dir) if f.endswith(".py")]

st.sidebar.title("Selecione um Questionário")
selected_file = st.sidebar.selectbox("Escolha um questionário:", arquivos)

if selected_file:
    st.write(f"### Executando: {selected_file}")
    caminho_completo = os.path.join(questionarios_dir, selected_file)
    exec(open(caminho_completo).read())