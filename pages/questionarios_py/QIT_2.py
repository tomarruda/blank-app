
import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime

# 🔹 Configuração do quiz
P_C_given_A = {0: 0.308, 1: 0.632, 2: 0.857, 3: 0.973}
alpha_values = {0: 0.25, 1: 0.5, 2: 0.75, 3: 1.0}

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
csv_path = os.path.join("pages/resultados_csv", f"resultado_{quiz_nome}.csv")

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
json_path = os.path.join(JSON_DIR, f"{quiz_nome}.json")

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
    st.session_state.respostas_aluno = {}
if "niveis_conf" not in st.session_state:
    st.session_state.niveis_conf = {}
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
    st.subheader(f"Questão {questao_atual + 1} de {total_questoes}")
    st.markdown(f"<p style='font-size:20px'>{questao['question']}</p>", unsafe_allow_html=True)
    resposta = st.radio("Selecione a resposta:", questao["options"], key=f"questao_{questao_atual}")
    nivel_conf = st.slider("Nível de confiança na resposta (0: Baixa confiança → 3: Alta confiança)", 0, 3, 1, key=f"conf_{questao_atual}")

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
    CSV_FILE = f"resultados_{quiz_nome}.csv"
    questoes = st.session_state.questoes

    pontuacao_final = 0
    acertos = 0
    erros = 0
    nome_aluno = st.session_state.get("nome_aluno", "Aluno")
    email_aluno = st.session_state.get("aluno_logado", "email_não_definido")
    resultados_aluno = {
        "Nome": nome_aluno,
        "E-mail": email_aluno
    }

    for i, questao in enumerate(questoes):
        resposta_correta = questao['answer']
        resposta_escolhida = st.session_state.respostas_aluno[i]
        nivel_conf = st.session_state.niveis_conf[i]

        tags = questao.get("tags", {})
        contents = tags.get("content", "NÃO ENCONTRADO")
        topics = tags.get("topic", "NÃO ENCONTRADO")
        subtopics = tags.get("subtopic", "NÃO ENCONTRADO")

        # Inclui o ID da questão no CSV
        questao_id = questao.get("id", f"Q{i+1}")

        P_C_E = 1 - P_C_given_A[nivel_conf]
        acertou = resposta_escolhida == resposta_correta
        if acertou:
            pontuacao_final += P_C_given_A[nivel_conf]
            acertos += 1
        else:
            pontuacao_final += -alpha_values[nivel_conf] * (1 - P_C_E)
            erros += 1

        resultados_aluno[f"Q{i+1}_ID"] = questao_id
        resultados_aluno[f"Q{i+1}_Acertou"] = "Sim" if acertou else "Não"
        resultados_aluno[f"Q{i+1}_Confiança"] = nivel_conf
        resultados_aluno[f"Q{i+1}_Contents"] = contents
        resultados_aluno[f"Q{i+1}_Topics"] = topics
        resultados_aluno[f"Q{i+1}_Subtopics"] = subtopics

    horario_finalizacao = datetime.now()
    tempo_total = horario_finalizacao - st.session_state.tempo_inicio
    tempo_total_formatado = f"{tempo_total.seconds // 60}:{tempo_total.seconds % 60:02d}"

    resultados_aluno["Acertos Totais"] = acertos
    resultados_aluno["Pontuação Ajustada"] = pontuacao_final
    resultados_aluno["Horário Finalização"] = horario_finalizacao.strftime("%Y-%m-%d %H:%M:%S")
    resultados_aluno["Tempo Total"] = tempo_total_formatado
    resultados_aluno["Status"] = "concluído"

    RESULTADOS_DIR = "/workspaces/blank-app/pages/resultados_csv"   
    os.makedirs(RESULTADOS_DIR, exist_ok=True)

    CSV_FILE = os.path.join(RESULTADOS_DIR, f"resultados_{quiz_nome}.csv")

    df_resultado = pd.DataFrame([resultados_aluno])
    if os.path.exists(CSV_FILE):
        df_resultado.to_csv(CSV_FILE, mode='a', header=False, index=False)
    else:
        df_resultado.to_csv(CSV_FILE, mode='w', header=True, index=False)

    st.success(f"{st.session_state.nome_aluno}, você finalizou o quiz!")
    st.write(f"**Número de acertos:** {acertos}")
    st.write(f"**Pontuação final ajustada:** {pontuacao_final:.2f}")
    st.write(f"**Tempo total:** {tempo_total_formatado}")