import streamlit as st
import requests
import graphviz

st.set_page_config(page_title="Analizador de Algoritmos", layout="wide", page_icon="🧬")

# --- CSS para mejorar la UI ---
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #e0e7ff; color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

st.title("🧬 Analizador de Complejidad Algorítmica")
st.markdown("---")

# --- Helper para Graphviz ---
def build_graphviz(node, dot=None, parent_id=None):
    """Convierte el JSON del AST en un objeto Graphviz recursivamente"""
    if dot is None:
        dot = graphviz.Digraph()
        dot.attr(rankdir='TB', size='10')
        dot.attr('node', shape='box', style='filled', fillcolor='#eef2ff', color='#4f46e5', fontname='Helvetica')
    
    # Crear ID único para el nodo actual
    node_id = str(id(node))
    
    # Etiqueta del nodo (Tipo + Info extra si hay)
    label = node['type']
    if 'name' in node: label += f"\n({node['name']})"
    elif 'op' in node: label += f"\nOP: {node['op']}"
    elif 'value' in node: label += f"\nVAL: {node['value']}"
    
    # Color especial para nodos clave
    color = '#eef2ff'
    if 'Loop' in label: color = '#fef3c7' # Amarillo para bucles
    if 'If' in label: color = '#fee2e2'   # Rojo para if
    if 'Function' in label: color = '#dcfce7' # Verde para funciones
    
    dot.node(node_id, label, fillcolor=color)
    
    if parent_id:
        dot.edge(parent_id, node_id)
        
    # Recursión para hijos
    for key, value in node.items():
        if isinstance(value, dict) and 'type' in value:
            build_graphviz(value, dot, node_id)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and 'type' in item:
                    build_graphviz(item, dot, node_id)
                    
    return dot

# --- UI Principal ---
col_input, col_results = st.columns([4, 6])

with col_input:
    st.subheader("📝 Entrada del Algoritmo")
    code_input = st.text_area(
        "Pseudocódigo o Lenguaje Natural:",
        height=400,
        placeholder="Ej: Haz un bubble sort para un array A de tamaño N..."
    )
    
    analyze_btn = st.button("🚀 Analizar Complejidad", type="primary", use_container_width=True)

if analyze_btn and code_input:
    with col_results:
        with st.spinner("⚙️ Procesando: Normalización -> Parsing -> Matemáticas -> IA..."):
            try:
                res = requests.post("http://127.0.0.1:8000/analyze", json={"code": code_input})
                
                if res.status_code == 200:
                    data = res.json()
                    hard = data.get("hard_analysis", {})
                    soft = data.get("soft_analysis", {})
                    ast_data = data.get("ast_debug")
                    
                    # --- CÁLCULO DE "QUIÉN HIZO QUÉ" ---
                    # Si hay error en hard, la IA hizo el 90%. Si no, 50/50.
                    if "error_details" in hard or hard.get("big_o") == "Indeterminado":
                        deter_pct = 15
                        ai_pct = 85
                        status_color = "orange"
                        status_msg = "Análisis Híbrido (Apoyo IA)"
                    else:
                        deter_pct = 80
                        ai_pct = 20
                        status_color = "green"
                        status_msg = "Análisis Matemático Exacto"

                    # --- VISUALIZACIÓN DE LA CARGA DE TRABAJO ---
                    st.subheader("📊 Desglose de Análisis")
                    st.progress(deter_pct / 100, text=f"Motor Determinista: {deter_pct}% | Consultor IA: {ai_pct}%")
                    if deter_pct > 50:
                        st.success("✅ Cálculo matemático exitoso. La IA solo validó.")
                    else:
                        st.warning("⚠ Limitación estructural detectada. La IA estimó la complejidad.")

                    # --- TABS DE RESULTADOS ---
                    tab1, tab2, tab3, tab4 = st.tabs(["📘 Informe", "🧮 Matemáticas", "🌳 Estructura (AST)", "💻 Código"])
                    
                    with tab1:
                        st.markdown(f"### 🎯 Estrategia: {soft.get('strategy', 'Desconocida')}")
                        st.info(soft.get("explanation"))
                        
                        c1, c2 = st.columns(2)
                        c1.metric("Complejidad Asintótica", hard.get("big_o", soft.get("complexity_validation", "?")))
                        c2.metric("Patrón", soft.get("pattern_identified", "-"))

                    with tab2:
                        if "error_details" in hard:
                            st.error("El motor matemático encontró un obstáculo:")
                            st.code(hard['error_details'])
                        else:
                            st.write("### Derivación Paso a Paso")
                            st.latex(r"T(n) = " + hard.get("cost_expression", ""))
                            st.write("Al aplicar límites cuando $n \\to \\infty$:")
                            st.latex(r"O(" + hard.get("big_o", "") + ")")
                            
                            if hard.get("is_recursive"):
                                st.warning("🔄 Recursividad detectada")
                                st.code(hard.get("recurrence_equation"))

                    with tab3:
                        if ast_data:
                            st.write("Visualización gráfica del algoritmo parseado:")
                            # Renderizamos el primer nodo función
                            graph = build_graphviz(ast_data[0])
                            st.graphviz_chart(graph)
                        else:
                            st.warning("No hay AST disponible.")

                    with tab4:
                        st.code(data['input_analysis']['normalized_pascal'], language="pascal")
                        
                else:
                    st.error(f"Error {res.status_code}: {res.text}")
            
            except Exception as e:
                st.error(f"Error de conexión: {e}")