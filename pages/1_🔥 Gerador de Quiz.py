import json
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Função para carregar JSON
def load_json(file):
    return json.load(file)

# Função para salvar JSON (verifica se há questões antes de salvar)
def save_json(data, filename):
    if not data:  # Se não houver questões, exibe um erro e não salva
        st.error("Erro: Nenhuma questão para salvar. Adicione questões antes de criar o questionário.")
        return
    
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        st.success(f"✅ Arquivo JSON salvo com {len(data)} questões: {filename}")
    except Exception as e:
        st.error(f"Erro ao salvar JSON: {e}")

# Função para gerar o script do quiz (corrigindo o caminho do arquivo)
def generate_quiz_script(quiz_name, json_filename, py_filename):
    script_content = f"""
import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime

P_C_given_A = {{0: 0.308, 1: 0.632, 2: 0.857, 3: 0.973}}
alpha_values = {{0: 0.25, 1: 0.5, 2: 0.75, 3: 1.0}}

if "submetido" not in st.session_state:
    st.session_state.submetido = False
if "questoes" not in st.session_state:
    st.session_state.questoes = None
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

st.title(f"{quiz_name}")
st.subheader("Passo 1: Identificação do aluno")

with st.form("form_identificacao"):
    nome_aluno = st.text_input("Digite seu nome:")
    email_aluno = st.text_input("Digite seu e-mail:")
    iniciar = st.form_submit_button("Iniciar Quiz")
    
if iniciar and nome_aluno and email_aluno:
    st.session_state.quiz_iniciado = True
    st.session_state.tempo_inicio = datetime.now()
    st.session_state.nome_aluno = nome_aluno
    st.session_state.email_aluno = email_aluno

if st.session_state.quiz_iniciado and not st.session_state.finalizou_quiz:
    with open("{json_filename}", "r", encoding="utf-8") as file:
        st.session_state.questoes = json.load(file)
    
    questoes = st.session_state.questoes
    total_questoes = len(questoes)
    questao_atual = st.session_state.questao_atual

    if questao_atual >= total_questoes:
        st.error("Erro: Tentativa de acessar questão fora do índice.")
        st.stop()

    questao = questoes[questao_atual]

    st.subheader(f"Questão {{questao_atual + 1}} de {{total_questoes}}")
    st.write(questao["question"])
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

if st.session_state.finalizou_quiz and st.session_state.questoes is not None:
    CSV_FILE = "resultados_{quiz_name}.csv"
    questoes = st.session_state.questoes

    pontuacao_final = 0
    acertos = 0
    erros = 0
    resultados_aluno = {{
        "Nome": st.session_state.nome_aluno,
        "E-mail": st.session_state.email_aluno
    }}

    for i, questao in enumerate(questoes):
        resposta_correta = questao['answer']
        resposta_escolhida = st.session_state.respostas_aluno[i]
        nivel_conf = st.session_state.niveis_conf[i]

        tags = questao.get("tags", {{}})
        contents = tags.get("content", "NÃO ENCONTRADO")
        topics = tags.get("topic", "NÃO ENCONTRADO")
        subtopics = tags.get("subtopic", "NÃO ENCONTRADO")

        P_C_E = 1 - P_C_given_A[nivel_conf]
        acertou = resposta_escolhida == resposta_correta
        if acertou:
            pontuacao_final += P_C_given_A[nivel_conf]
            acertos += 1
        else:
            pontuacao_final += -alpha_values[nivel_conf] * (1 - P_C_E)
            erros += 1

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

   # 📂 Criando a pasta "resultados csv" fora da pasta do script
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Sobe um nível na estrutura de diretórios
    resultados_dir = os.path.join(base_dir, "resultados csv")

    os.makedirs(resultados_dir, exist_ok=True)  # Garante que a pasta seja criada

    # 📌 Define o caminho do arquivo CSV dentro da pasta "resultados csv"
    CSV_FILE = os.path.join(resultados_dir, f"resultado_{quiz_name}.csv")

    # 📄 Salvar os resultados no CSV
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

    # Salvar o script Python na pasta correta
    with open(py_filename, "w", encoding="utf-8") as file:
        file.write(script_content)
    
    st.success(f"✅ Arquivo Python gerado: {py_filename}")

def main():
    st.title("Gerador de Questionário")
    quiz_name = st.text_input("Nome do Questionário", "questionario")
    
    # Upload de JSON
    uploaded_file = st.file_uploader("Carregar arquivo JSON", type=["json"])
    if uploaded_file is not None:
        try:
            st.session_state.questoes = load_json(uploaded_file)
            json_filename = os.path.join("questionários json", f"{quiz_name}.json")
            save_json(st.session_state.questoes, json_filename)
            st.success(f"Arquivo JSON salvo como {json_filename}!")
        except json.JSONDecodeError:
            st.error("Erro ao carregar o arquivo JSON. Verifique se está bem formatado.")
            return
    
    if "questoes" not in st.session_state:
        st.session_state.questoes = []
    
    # Formulário para adicionar questão
    with st.expander("Adicionar Nova Questão"):
        with st.form("nova_questao_form"):
            question = st.text_input("Pergunta:")
            option_A = st.text_input("Opção A:")
            option_B = st.text_input("Opção B:")
            option_C = st.text_input("Opção C:")
            option_D = st.text_input("Opção D:")
            answer = st.selectbox("Resposta Correta", ["A", "B", "C", "D"])
            content = st.text_input("Conteúdo:")
            topic = st.text_input("Tópico:")
            subtopic = st.text_input("Subtópico:")
            submit = st.form_submit_button("Salvar Questão")

            if submit:
                if question:
                    mapping = {"A": option_A, "B": option_B, "C": option_C, "D": option_D}
                    st.session_state.questoes.append({
                        "question": question,
                        "options": [option_A, option_B, option_C, option_D],
                        "answer": mapping[answer],
                        "tags": {"content": content, "topic": topic, "subtopic": subtopic}
                    })
                    st.success("Questão adicionada com sucesso!")
                    st.write(f"Total de questões: {len(st.session_state.questoes)}")  # Debug
                else:
                    st.error("Preencha a pergunta!")

    # Botão para gerar questionário
    if st.button("Criar Questionário"):
        if not st.session_state.questoes:
            st.error("Nenhuma questão foi adicionada. Adicione questões antes de criar o questionário.")
            return
        
        # Criar pastas se não existirem
        os.makedirs("questionários json", exist_ok=True)
        os.makedirs("questionários py", exist_ok=True)

        json_filename = os.path.join("questionários json", f"{quiz_name}.json")
        py_filename = os.path.join("questionários py", f"{quiz_name}.py")

        save_json(st.session_state.questoes, json_filename)
        generate_quiz_script(quiz_name, json_filename, py_filename)

if __name__ == "__main__":
    main()