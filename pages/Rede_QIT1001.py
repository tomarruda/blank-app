import streamlit as st
import json
from collections import deque

# Configuração do Streamlit para modo "wide"
st.set_page_config(layout="wide")

# Caminho do arquivo JSON do grafo
json_file_path = "QIT1001.json"

# Carregar os dados do JSON
try:
    with open(json_file_path, "r") as file:
        graph_data = json.load(file)
except Exception as e:
    st.error(f"Erro ao carregar o JSON: {e}")
    st.stop()

# Criar um dicionário para mapear rótulos de nós para seus IDs
node_label_to_id = {node["label"]: node["id"] for node in graph_data["nodes"]}

# Criar opções de visualização
view_option = st.radio("Escolha como visualizar o grafo:", ["Ver todo o grafo", "Começar por um nó específico"])

# Criar estado no Streamlit para armazenar nós expandidos
if "expanded_nodes" not in st.session_state:
    st.session_state.expanded_nodes = set()

# Adicionar slider para selecionar profundidade de expansão
expansion_depth = st.slider("Escolha a profundidade de expansão:", 1, 5, 2)

# Criar uma função para filtrar e expandir conexões a partir de um nó
def filter_graph_from_node(graph_data, start_node_id, depth=1, expanded_nodes=None):
    """
    Filtra o grafo para exibir nós e conexões a partir do nó inicial, expandindo até um nível `depth`.
    """
    if expanded_nodes is None:
        expanded_nodes = set()

    filtered_nodes = []
    filtered_edges = []
    visited_nodes = set()
    queue = deque([(start_node_id, 0)])  # (nó_id, nível de profundidade)

    while queue:
        node_id, level = queue.popleft()
        if node_id in visited_nodes or level > depth:
            continue
        visited_nodes.add(node_id)
        expanded_nodes.add(node_id)

        # Adiciona o nó atual
        for node in graph_data["nodes"]:
            if node["id"] == node_id:
                filtered_nodes.append(node)

        # Adiciona conexões e novos nós conectados
        for edge in graph_data["edges"]:
            if edge["from"] == node_id and edge["to"] not in visited_nodes:
                filtered_edges.append(edge)
                queue.append((edge["to"], level + 1))
            elif edge["to"] == node_id and edge["from"] not in visited_nodes:
                filtered_edges.append(edge)
                queue.append((edge["from"], level + 1))

    return {"nodes": filtered_nodes, "edges": filtered_edges}

# Se a opção for "Começar por um nó específico", pegar o input do usuário
filtered_graph = graph_data  # Padrão: todo o grafo
if view_option == "Começar por um nó específico":
    search_query = st.text_input("Digite o nome de um nó para visualizar conexões:")
    if search_query:
        if search_query in node_label_to_id:
            start_node_id = node_label_to_id[search_query]
            filtered_graph = filter_graph_from_node(graph_data, start_node_id, depth=expansion_depth, expanded_nodes=st.session_state.expanded_nodes)
        else:
            st.warning("Nenhum nó encontrado com esse nome.")

# Criar o código HTML com Vis.js para renderizar o grafo
html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        #mynetwork {{
            width: 100%;
            height: 850px;  /* Tela grande */
            border: 1px solid lightgray;
        }}
    </style>
</head>
<body>
    <div id="mynetwork"></div>
    <script type="text/javascript">
        document.addEventListener("DOMContentLoaded", function() {{
            var nodes = new vis.DataSet({json.dumps(filtered_graph["nodes"])});
            var edges = new vis.DataSet({json.dumps(filtered_graph["edges"])});

            var container = document.getElementById('mynetwork');
            var data = {{ nodes: nodes, edges: edges }};
            var options = {{
                physics: {{
                    enabled: true
                }},
                interaction: {{
                    dragNodes: true,
                    dragView: true,
                    zoomView: true
                }},
                edges: {{
                    arrows: "to",
                    color: "#848484",
                    width: 2
                }},
                nodes: {{
                    shape: "dot",
                    size: 15,
                    color: "#97C2FC"
                }},
                manipulation: {{
                    enabled: true
                }}
            }};
            var network = new vis.Network(container, data, options);

            // Expansão interativa ao clicar nos nós
            network.on("click", function(params) {{
                if (params.nodes.length > 0) {{
                    var clickedNode = params.nodes[0];
                    var expandUrl = window.location.href.split('?')[0] + "?expand_node=" + clickedNode;
                    fetch(expandUrl)
                        .then(response => response.json())
                        .then(data => {{
                            nodes.add(data.nodes);
                            edges.add(data.edges);
                        }});
                }}
            }});
        }});
    </script>
</body>
</html>
"""

# Exibir o grafo filtrado no Streamlit
st.components.v1.html(html_template, height=900)

# Atualizar a expansão ao clicar em um nó
query_params = st.query_params()
if "expand_node" in query_params:
    clicked_node = int(query_params["expand_node"][0])
    st.session_state.expanded_nodes.add(clicked_node)
    st.rerun()