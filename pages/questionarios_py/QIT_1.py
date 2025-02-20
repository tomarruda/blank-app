
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

# ✅ **Nome do quiz**
quiz_nome = "QIT_1"  # Agora corretamente formatado

st.write(f"📌 Nome do quiz detectado corretamente: `QIT_1`")  # Debugging

# 🔹 Caminho correto para os arquivos JSON
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Sobe um nível para a pasta principal
JSON_DIR = os.path.join(BASE_DIR, "pages", "questionarios_json")  
json_path = os.path.join(JSON_DIR, f"QIT_1.json")

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

# 🔹 Salvar os resultados ao final do quiz com pontuação ajustada
if st.session_state.finalizou_quiz and st.session_state.questoes is not None:
    CSV_FILE = f"resultados_QIT_1.csv"
    questoes = st.session_state.questoes

    pontuacao_final = 0
    acertos = 0
    erros = 0
    name_aluno = st.session_state.get("name_aluno", "Aluno")
    email_aluno = st.session_state.get("aluno_logado", "aluno@example.com")
    
    # 🔹 Certifique-se de que este dicionário não está causando erro de formatação
    resultados_aluno = {
        "Nome": name_aluno,
        "E-mail": email_aluno
    }

    horario_finalizacao = datetime.now()
    tempo_total = horario_finalizacao - st.session_state.tempo_inicio
    tempo_total_formatado = f"{tempo_total.seconds // 60}:{tempo_total.seconds % 60:02d}"

    resultados_aluno["Acertos Totais"] = acertos
    resultados_aluno["Pontuação Ajustada"] = pontuacao_final
    resultados_aluno["Horário Finalização"] = horario_finalizacao.strftime("%Y-%m-%d %H:%M:%S")
    resultados_aluno["Tempo Total"] = tempo_total_formatado
    resultados_aluno["Status"] = "concluído"

    df_resultado = pd.DataFrame([resultados_aluno])
    if os.path.exists(CSV_FILE):
        df_resultado.to_csv(CSV_FILE, mode='a', header=False, index=False)
    else:
        df_resultado.to_csv(CSV_FILE, mode='w', header=True, index=False)

    st.success(f"✅ {st.session_state.name_aluno}, você finalizou o quiz!")
    st.write(f"**Número de acertos:** {acertos}")
    st.write(f"**Pontuação final ajustada:** {pontuacao_final:.2f}")
    st.write(f"**Tempo total:** {tempo_total_formatado}")
