import streamlit as st
import pandas as pd
import os

st.title("📋 Cadastro de Alunos")

# 📂 Caminho para o banco de dados (CSV)
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "../banco_de_dados/alunos.csv")

# 📂 Garante que a pasta do banco de dados exista
os.makedirs(os.path.dirname(csv_path), exist_ok=True)

# 📌 Se o arquivo não existir, cria um novo
if not os.path.exists(csv_path):
    df = pd.DataFrame(columns=["Nome Completo", "E-mail", "CPF", "Disciplinas"])
    df.to_csv(csv_path, index=False)

# 🔹 Formulário para adicionar aluno
with st.form("form_cadastro"):
    nome = st.text_input("Nome Completo:")
    email = st.text_input("E-mail:")
    cpf = st.text_input("CPF (apenas números, sem pontos ou traços):")
    
    # 🔹 Seleção múltipla de disciplinas
    disciplinas_opcoes = ["Introdução ao Laboratório de Química", "Química Geral Experimental ", "Química Inorgânica I", "Química Inorgânica Exp.", "Mineralogia"]
    disciplinas = st.multiselect("Disciplinas", disciplinas_opcoes)

    cadastrar = st.form_submit_button("Cadastrar Aluno")

if cadastrar:
    if nome and email and cpf and disciplinas:
        # 🔹 Carrega o banco de dados
        df = pd.read_csv(csv_path, dtype={"CPF": str})  # Garante que CPF seja tratado como string

        # 🔹 Verifica se o aluno já está cadastrado
        aluno_existente = df[df["E-mail"] == email]

        if not aluno_existente.empty:
            # 🔹 Se o aluno já estiver cadastrado, adiciona novas disciplinas
            disciplinas_existentes = set(aluno_existente.iloc[0]["Disciplinas"].split(", "))
            novas_disciplinas = set(disciplinas)
            todas_disciplinas = list(disciplinas_existentes.union(novas_disciplinas))

            df.loc[df["E-mail"] == email, "Disciplinas"] = ", ".join(todas_disciplinas)
            st.success(f"✅ {nome} atualizado! Agora está nas disciplinas: {', '.join(todas_disciplinas)}")
        else:
            # 🔹 Adiciona novo aluno
            novo_aluno = pd.DataFrame([[nome, email, cpf, ", ".join(disciplinas)]], 
                                      columns=["Nome Completo", "E-mail", "CPF", "Disciplinas"])
            df = pd.concat([df, novo_aluno], ignore_index=True)

            st.success(f"✅ {nome} foi cadastrado com sucesso!")

        # 📂 Salva os dados
        df.to_csv(csv_path, index=False)

# 📜 **Exibir alunos cadastrados**
st.subheader("📜 Lista de Alunos Cadastrados")
df = pd.read_csv(csv_path, dtype={"CPF": str})  # Garante que CPF seja tratado como string

if not df.empty:
    # 🔹 Permitir edição da tabela
    df_editado = st.data_editor(df, num_rows="dynamic", key="alunos_editor")

    # 🔹 Salvar a edição quando houver mudanças
    if st.button("Salvar Alterações"):
        df_editado.to_csv(csv_path, index=False)
        st.success("✅ Alterações salvas com sucesso!")
else:
    st.info("Nenhum aluno cadastrado ainda.")