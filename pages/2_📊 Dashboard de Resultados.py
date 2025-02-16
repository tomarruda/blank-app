# streamlit_page_name: 📊 Dashboard de Resultados
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
from pathlib import Path

# Configuração da página para widescreen
st.set_page_config(layout="wide")

# Dicionários com probabilidades condicionais e valores alpha
P_C_given_A = {0: 0.308, 1: 0.632, 2: 0.857, 3: 0.973}
alpha_values = {0: 0.25, 1: 0.5, 2: 0.75, 3: 1.0}

def calculate_score(resposta, confidence):
    if pd.isna(confidence) or pd.isna(resposta):
        return 0.0
    confidence = int(confidence)
    P_C_E = 1 - P_C_given_A.get(confidence, 0)
    return P_C_given_A[confidence] if resposta == 1 else -alpha_values[confidence] * (1 - P_C_E)

def process_data(df):
    acertos_cols = df.filter(like='_Acertou').replace({'Sim': 1, 'Não': 0}).apply(pd.to_numeric, errors='coerce').fillna(0)
    df.update(acertos_cols)
    return df

def display_student_stats(df, student_name):
    student_data = df[df['Nome'] == student_name]
    if student_data.empty:
        st.write("Aluno não encontrado.")
        return

    acertos_cols = student_data.filter(like='_Acertou').apply(pd.to_numeric, errors='coerce').fillna(0)
    confidence_cols = student_data.filter(like='_Confiança').apply(pd.to_numeric, errors='coerce').fillna(0)
    
    total_questoes = min(acertos_cols.shape[1], confidence_cols.shape[1])
    acertos = acertos_cols.values.flatten()
    confs = confidence_cols.values.flatten()

    total_acertos = int(sum(acertos))
    media_conf_total = np.mean(confs)

    pontuacao_acertos = sum([P_C_given_A.get(int(c), 0) for a, c in zip(acertos, confs) if a == 1])
    pontuacao_erros = sum([-alpha_values.get(int(c), 0) * (1 - P_C_given_A.get(int(c), 0)) for a, c in zip(acertos, confs) if a == 0])
    pontuacao_ajustada = pontuacao_acertos + pontuacao_erros

    st.write(f"**Número de acertos:** {total_acertos} de {total_questoes}")
    st.write(f"**Pontuação ajustada:** {pontuacao_ajustada:.2f}")
    st.write(f"**Média dos níveis de confiança:** {media_conf_total:.2f}")

    desempenho_df = pd.DataFrame({
        'Questão': list(range(1, total_questoes + 1)),
        'Acerto': ["✅" if x == 1 else "❌" for x in acertos[:total_questoes]],
        'Pontuação': [calculate_score(a, c) for a, c in zip(acertos[:total_questoes], confs[:total_questoes])]
    })

def split_label(label, max_length=20):
    """
    Quebra um rótulo longo em múltiplas linhas para melhor exibição.
    """
    words = label.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            current_line += (" " if current_line else "") + word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)

def plot_radar_chart(df, student_name):
    """
    Cria e exibe um gráfico radar para um aluno específico com base nos conteúdos.
    """
    student_data = df[df['Nome'] == student_name]
    if student_data.empty:
        st.write("Aluno não encontrado.")
        return

    # Seleciona as colunas que contêm informações de conteúdo
    content_columns = [col for col in df.columns if "_Contents" in col]
    if not content_columns:
        st.write("Colunas de conteúdo não encontradas no arquivo.")
        return

    accuracy_per_content = {}
    for col in content_columns:
        content_name = student_data[col].iloc[0]  # Assume que o conteúdo seja o mesmo para todos
        acertou_col = col.replace("_Contents", "_Acertou")
        # Considera 1 se o aluno acertou, 0 caso contrário
        accuracy = 1 if student_data[acertou_col].iloc[0] == 1 else 0
        if content_name not in accuracy_per_content:
            accuracy_per_content[content_name] = []
        accuracy_per_content[content_name].append(accuracy)

    # Calcula a média de acertos por conteúdo
    accuracy_means = {content: np.mean(values) for content, values in accuracy_per_content.items()}
    labels = list(accuracy_means.keys())
    values = list(accuracy_means.values())
    labels_wrapped = [split_label(label, max_length=20) for label in labels]

    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    # Fecha o gráfico conectando o último ponto ao primeiro
    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='blue', alpha=0.3)
    ax.plot(angles, values, marker='o', color='blue')

    # Adiciona a porcentagem de acertos em cada vértice
    for angle, value in zip(angles[:-1], values[:-1]):
        ax.text(angle, value + 0.05, f"{value*100:.1f}%", ha='center', va='center',
                fontsize=10, color='black')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels_wrapped)
    ax.set_yticklabels([])
    ax.set_ylim(0, 1.2)

    st.pyplot(fig)

def compute_adjusted_score(acertos, confs):
    """
    Calcula a pontuação ajustada de um aluno com base nos acertos e níveis de confiança.
    """
    if len(acertos) != len(confs):
        return 0.0  # Segurança contra listas desalinhadas

    pontuacao_acertos = sum([P_C_given_A.get(int(c), 0) for a, c in zip(acertos, confs) if a == 1])
    pontuacao_erros = sum([-alpha_values.get(int(c), 0) * (1 - P_C_given_A.get(int(c), 0)) for a, c in zip(acertos, confs) if a == 0])

    return pontuacao_acertos + pontuacao_erros

def compute_student_stats(df, student_name):
    """
    Calcula as estatísticas de um aluno (usado na visualização geral).
    """
    student_data = df[df['Nome'] == student_name]
    if student_data.empty:
        return None

    # Pegamos diretamente a pontuação já calculada no DataFrame
    pontuacao_ajustada = student_data['Pontuação Ajustada'].values[0] if 'Pontuação Ajustada' in student_data.columns else 0.0

    total_acertos = int(student_data.filter(like='_Acertou').sum(axis=1).values[0])
    media_conf_total = student_data.filter(like='_Confiança').mean(axis=1).values[0]

    return {
        "total_questoes": len(student_data.filter(like='_Acertou').columns),
        "total_acertos": total_acertos,
        "media_conf_total": media_conf_total,
        "pontuacao_ajustada": pontuacao_ajustada
    }

def display_all_stats(df):
    """
    Exibe um gráfico de dispersão com as estatísticas de todos os alunos.
    """
    student_list = df['Nome'].unique()
    stats_list = []
    for student in student_list:
        stats = compute_student_stats(df, student)
        
        if stats is not None:
            stats['Nome'] = student
            stats_list.append(stats)
    if stats_list:
        stats_df = pd.DataFrame(stats_list)
        stats_df['pontuacao_ajustada'] = stats_df['pontuacao_ajustada'].round(2)
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.set_title("Estatísticas dos Alunos")
        scatter = ax.scatter(
            stats_df['total_acertos'],
            stats_df['media_conf_total'],
            c=stats_df['pontuacao_ajustada'],
            cmap='RdYlGn',
            s=100,
            edgecolors='black'
        )
        for i, row in stats_df.iterrows():
            ax.annotate(row['pontuacao_ajustada'], (row['total_acertos'], row['media_conf_total']),
                        textcoords="offset points", xytext=(5, 5), fontsize=9)
        ax.set_xlabel("Número de Questões Corretas")
        ax.set_ylabel("Média do Nível de Confiança")
        ax.set_xlim(0, stats_df['total_questoes'].max() + 1)
        ax.set_ylim(0, 3)
        plt.colorbar(scatter, label="Pontuação")
        st.pyplot(fig)
    else:
        st.write("Nenhum dado disponível para exibir estatísticas.")

def display_all_radar_charts(df):
    """
    Exibe os gráficos radar para todos os alunos (um após o outro).
    """
    student_list = df['Nome'].unique()
    for student in student_list:
        st.subheader(f"Gráfico Radar - {student}")
        plot_radar_chart(df, student)

def display_general_table(df):
    acertou_cols = df.filter(like='_Acertou').columns.tolist()
    confianca_cols = df.filter(like='_Confiança').columns.tolist()

    # Converter as colunas para object para evitar problemas com categorias/dtypes
    table_data = df[acertou_cols].copy().astype(object)  # Alteração aqui
    table_data.index = df['Nome']

    # Substituir 0 por ❌ e 1 por ✅
    table_data = table_data.applymap(lambda x: '✅' if x == 1 else '❌' if x == 0 else x)

    acertos_count = df[acertou_cols].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)

    def compute_student_total_score(row):
        total_score = 0
        for acerto_col, conf_col in zip(acertou_cols, confianca_cols):
            if pd.notna(row[acerto_col]) and pd.notna(row[conf_col]):  # Evita erro com valores NaN
                total_score += calculate_score(row[acerto_col], row[conf_col])
        return total_score

    pontuacao = df.apply(compute_student_total_score, axis=1)

    table_data['Acertos'] = acertos_count.values
    table_data['Pontuação'] = pontuacao.values

    resumo = {col: f"{pd.to_numeric(df[col], errors='coerce').fillna(0).mean()*100:.1f}%" for col in acertou_cols}
    resumo['Acertos'] = f"{acertos_count.mean():.1f}"
    resumo['Pontuação'] = f"{pontuacao.mean():.2f}"

    resumo_df = pd.DataFrame(resumo, index=["Média Aproveitamento"])

    tabela_final = pd.concat([table_data, resumo_df])

    st.write("### Tabela Geral de Desempenho")
    st.dataframe(tabela_final, width=1400)


def display_confidence_table(df):
    """
    Exibe uma tabela com os valores de confiança de cada questão na forma de barras horizontais,
    incluindo a média de confiança de cada aluno na última coluna.
    """
    # Seleciona as colunas de confiança
    confianca_cols = df.filter(like='_Confiança').columns.tolist()
    
    # Cria um DataFrame somente com as colunas de confiança e define o índice como o nome dos alunos
    table_conf = df[confianca_cols].copy()
    table_conf.index = df['Nome']
    
    # Calcula a média de confiança de cada aluno
    table_conf["Média do Aluno"] = table_conf.mean(axis=1)

    # Calcula a média de confiança de cada questão
    avg_conf = table_conf.mean()
    avg_conf_df = pd.DataFrame(avg_conf).transpose()
    avg_conf_df.index = ["Média Confiança"]

    # Cria uma tabela final combinando os dados individuais e a média
    tabela_final = pd.concat([table_conf, avg_conf_df])

    # Exibe a tabela com barras de progresso para os níveis de confiança e a média de cada aluno
    st.write("### Tabela de Confiança por Questão")

    st.data_editor(
        tabela_final, 
        width=1600,  # Aumenta a largura da tabela
        column_config={
            col: st.column_config.ProgressColumn(
                col,
                min_value=0,
                max_value=3,
                format="%.1f"
            ) for col in confianca_cols
        } | {
            "Média do Aluno": st.column_config.ProgressColumn(
                "Média do Aluno",
                min_value=0,
                max_value=3,
                format="%.1f"
            )
        }
    )
    

def main():
    st.title("📊 Dashboard de Resultados")

    DIRETORIO_BASE = Path("/workspaces/blank-app/pages/resultados_csv/")

    if not DIRETORIO_BASE.exists():
        st.error(f"Diretório não encontrado: {DIRETORIO_BASE}")
        st.stop()

    try:
        arquivos_csv = [f.name for f in DIRETORIO_BASE.glob("*.csv") if f.is_file() and not f.name.startswith('.')]
    except Exception as e:
        st.error(f"Erro ao acessar o diretório: {str(e)}")
        st.stop()

    if not arquivos_csv:
        st.warning("Nenhum arquivo CSV encontrado no diretório")
        st.stop()

    arquivo_selecionado = st.selectbox("📁 Selecione um arquivo:", arquivos_csv, index=0)

    try:
        caminho_completo = DIRETORIO_BASE / arquivo_selecionado
        df = pd.read_csv(caminho_completo)
        df = process_data(df)
    except Exception as e:
        st.error(f"Falha ao carregar arquivo: {str(e)}")
        st.stop()

    aba1, aba2, aba3, aba4 = st.tabs([
        "📊 Estatística Geral do Aluno",
        "📈 Gráfico Geral",
        "📈 Desempenho Geral por Questão",
        "📊 Níveis de Confiança por questão"
    ])

    # 🔹 Corrigindo a indentação para manter selected_student dentro da aba correta
    with aba1:
        selected_student = st.selectbox("👤 Selecione um aluno:", df['Nome'].unique(), key="estatisticas_aluno")

        if selected_student:
            student_data = df[df['Nome'] == selected_student]

            if not student_data.empty:
                acertos_cols = student_data.filter(like='_Acertou').apply(pd.to_numeric, errors='coerce').fillna(0)
                confidence_cols = student_data.filter(like='_Confiança').apply(pd.to_numeric, errors='coerce').fillna(0)

                total_questoes = min(acertos_cols.shape[1], confidence_cols.shape[1])
                acertos = acertos_cols.values.flatten()
                confs = confidence_cols.values.flatten()

                total_acertos = int(sum(acertos))
                media_conf_total = np.mean(confs)

                st.write(f"**Número de acertos:** {total_acertos} de {total_questoes}")
                st.write(f"**Média dos níveis de confiança:** {media_conf_total:.2f}")

                col1, col2, col3 = st.columns([2, 3, 2.6])

                with col1:
                    st.write("### Tabela de Desempenho")
                    desempenho_df = pd.DataFrame({
                        'Questão': list(range(1, total_questoes + 1)),
                        'Acerto': ["✅" if x == 1 else "❌" for x in acertos[:total_questoes]],
                        'Confiança': confs[:total_questoes],
                        'Pontuação': [calculate_score(a, c) for a, c in zip(acertos[:total_questoes], confs[:total_questoes])]
                    })
                    total_acertos = sum(acertos[:total_questoes])
                    media_confianca = sum(confs[:total_questoes]) / total_questoes if total_questoes > 0 else 0
                    pontuacao_final = sum(desempenho_df['Pontuação'])

                    linha_total = pd.DataFrame({
                        'Questão': ["Total"],
                        'Acerto': [f"{total_acertos}/{total_questoes}"],
                        'Confiança': [round(media_confianca, 2)],
                        'Pontuação': [round(pontuacao_final, 2)]
                    })

                    desempenho_df = pd.concat([desempenho_df, linha_total], ignore_index=True)

                    st.write(desempenho_df)

                with col2:
                    st.write("### Gráfico de Dispersão")
                    fig, ax = plt.subplots()
                    scatter = ax.scatter(
                        [total_acertos],
                        [media_conf_total],
                        c=[pontuacao_final],  # Cor baseada na pontuação final
                        cmap='RdYlGn',
                        edgecolors='black',
                        s=200,
                        vmin=-total_questoes,  # Limite inferior da colorbar
                        vmax=total_questoes    # Limite superior da colorbar
                    )

                    ax.set_xlabel("Acertos")
                    ax.set_ylabel("Confiança Média")
                    ax.set_xlim([0, total_questoes])
                    ax.set_ylim([0, 3])
                    
                    cbar = plt.colorbar(scatter, ax=ax)
                    cbar.set_label("Pontuação")
                    cbar.set_ticks(np.linspace(-total_questoes, total_questoes, num=5))  # Define pontos na escala
                    st.pyplot(fig)

                with col3:
                    st.write("### Gráfico Radar")
                    plot_radar_chart(df, selected_student)

    with aba2:
        display_all_stats(df)

    with aba3:
        display_general_table(df)

    with aba4:
        display_confidence_table(df)

if __name__ == "__main__":
    main()