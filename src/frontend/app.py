import streamlit as st
import requests
import graphviz
import pandas as pd

st.set_page_config(page_title="Analizador de Algoritmos", layout="wide", page_icon="🧬", initial_sidebar_state="collapsed")

st.markdown("""
<style>

    .stTabs [data-baseweb="tab-list"] { 
        gap: 12px; 
    }

    .stTabs [data-baseweb="tab"] { 
        height: 50px !important;
        padding: 10px 22px !important;
        background-color: #333 !important; 
        border-radius: 8px !important;
        color: #eee !important;
        border: 1px solid #555 !important;
        font-weight: 600;
        transition: 0.2s ease-in-out;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #444 !important;
        border-color: #777 !important;
    }

    .stTabs [aria-selected="true"] { 
        background-color: #666 !important;
        color: white !important;
        border-color: #aaa !important;
    }

    .big-font { font-size: 20px !important; font-weight: bold; }
    .stAlert { margin-top: 1rem; }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4f46e5;
    }

</style>
""", unsafe_allow_html=True)


st.title("🧬 Analizador de Complejidad Algorítmica")
st.markdown("---")

def build_graphviz(node, dot=None, parent_id=None):
    """Convierte el JSON del AST en un objeto Graphviz recursivamente"""
    if dot is None:
        dot = graphviz.Digraph()
        dot.attr(rankdir='TB', size='10')
        dot.attr('node', shape='box', style='filled', fillcolor='#eef2ff', color='#4f46e5', fontname='Helvetica')
    
    # Crear ID único para el nodo actual
    node_id = str(id(node))
    
    # Etiqueta del nodo
    label = node.get('type', 'Node').replace('Node', '')
    if 'name' in node: label += f"\n({node['name']})"
    elif 'op' in node: label += f"\nOP: {node['op']}"
    elif 'value' in node: label += f"\nVAL: {node['value']}"
    
    color = '#eef2ff'
    if 'Loop' in label: color = '#fef3c7'
    if 'If' in label: color = '#fee2e2'
    if 'Function' in label: color = '#dcfce7'
    
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
col_input, col_results = st.columns([5, 6])

with col_input:
    st.subheader("📝 Entrada del Algoritmo")
    code_input = st.text_area(
        "Pseudocódigo o Lenguaje Natural:",
        height=400,
        placeholder="Ej: Haz un bubble sort para un array A de tamaño N..."
    )
    
    analyze_btn = st.button("🚀 Analizar Complejidad", type="primary", use_container_width=True)

    with st.expander("ℹ️ Ayuda de Sintaxis"):
        st.markdown("""
        **Estructuras soportadas:**
        - `FOR i <- 0 TO N DO ...`
        - `WHILE (x < N) DO ...`
        - `IF (cond) THEN ... ELSE ...`
        - Asignación: `x <- 5`
        - Arrays: `A[i] <- val`
        """)

if analyze_btn and code_input:
    with col_results:
        with st.spinner("⚙️ Procesando: Normalización -> Parsing -> Matemáticas -> IA..."):
            try:
                res = requests.post("http://127.0.0.1:8000/analyze", json={"code": code_input})
                
                if res.status_code == 200:
                    data = res.json()

                    # Extraer secciones de la respuesta
                    status = data.get("status")
                    mode = data.get("mode", "online")
                    hard = data.get("hard_analysis", {})
                    soft = data.get("soft_analysis", {})
                    pattern = data.get("pattern_analysis", {})
                    warnings = data.get("warnings", [])
                    ast_data = data.get("ast_debug")

                    input_analysis = data.get("input_analysis", {})
                    final_code = input_analysis.get("final_code", "")
                    
                    # --- CÁLCULO DE "QUIÉN HIZO QUÉ" ---
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

                    # --- 1. Estado del Sistema (Online/Offline) ---
                    if mode == "offline":
                        st.warning("⚠️ MODO OFFLINE ACTIVO: Sin acceso a IA. Se muestran solo resultados deterministas y patrones locales.")
                    
                    if warnings:
                        with st.expander("Avisos del Sistema", expanded=False):
                            for w in warnings: st.write(f"- {w}")

                    # --- 2. Resultados Principales ---
                    if data.get("status") == "error":
                        st.error(data.get("error"))
                    else:
                        # Pestañas
                        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📘 Informe", "🧮 Matemáticas Profundas", "📊 Costos por Línea", "🌳 Árbol Sintáctico", "📝 Código Final"])
                        
                        # === PESTAÑA 1: INFORME ===
                        with tab1:
                            # Identificación del Algoritmo
                            st.markdown("### 🔍 Identificación")
                            
                            # Prioridad: Patrón Local > IA > Desconocido
                            algo_name = "Algoritmo Personalizado"
                            strategy = "Análisis Genérico"
                            source = "Motor Matemático"
                            
                            if pattern.get("pattern_found"):
                                algo_name = pattern["name"]
                                strategy = pattern["strategy"]
                                source = "⚡ Base de Datos Local (Rápido)"
                                st.success(f"**Algoritmo Reconocido:** {algo_name}")
                            elif mode == "online" and soft.get("pattern_identified"):
                                algo_name = soft["pattern_identified"]
                                strategy = soft.get("strategy", "Desconocida")
                                source = "🧠 Análisis Semántico (IA)"
                                st.info(f"**Algoritmo Identificado por IA:** {algo_name}")
                            
                            st.caption(f"Fuente del análisis: {source}")
                            
                            # Métricas Principales
                            col_a, col_b = st.columns(2)
                            col_a.metric("Estrategia", strategy)
                            
                            # Complejidad (Prioridad: Determinista > Patrón > IA)
                            final_complexity = hard.get("worst_case", {}).get("notation", "N/A")
                            if final_complexity == "N/A" or "Indeterminado" in final_complexity:
                                final_complexity = pattern.get("expected_complexity", soft.get("complexity_validation", "Indeterminado"))
                                
                            col_b.metric("Complejidad (Peor Caso)", final_complexity)

                            # Explicación (Solo si hay IA o Patrón)
                            st.markdown("#### 💡 Explicación")
                            if mode == "online":
                                st.write(soft.get("explanation", "Sin explicación disponible."))
                            else:
                                st.write("En modo offline, la explicación detallada no está disponible. Se basa en el cálculo matemático puro.")

                        # === PESTAÑA 2: MATEMÁTICAS ===
                        with tab2:
                            st.markdown("### 📐 Análisis Asintótico Completo")
                            
                            if "error" in hard:
                                st.error(f"Error en cálculo matemático: {hard['error']}")
                            else:
                                # Tarjetas para O, Omega, Theta
                                c1, c2, c3 = st.columns(3)
                                
                                with c1:
                                    st.markdown("#### Peor Caso ($O$)")
                                    st.latex(hard.get('worst_case', {}).get('notation', ''))
                                    with st.expander("Ver ecuación exacta"):
                                        st.code(hard.get('worst_case', {}).get('expr', ''))
                                
                                with c2:
                                    st.markdown("#### Mejor Caso ($\Omega$)")
                                    st.latex(hard.get('best_case', {}).get('notation', ''))
                                    with st.expander("Ver ecuación exacta"):
                                        st.code(hard.get('best_case', {}).get('expr', ''))

                                with c3:
                                    st.markdown("#### Caso Promedio ($\Theta$)")
                                    st.latex(hard.get('average_case', {}).get('notation', ''))
                                    with st.expander("Ver ecuación exacta"):
                                        st.code(hard.get('average_case', {}).get('expr', ''))

                                st.markdown("---")
                                if hard.get("is_recursive"):
                                    st.warning("🔄 **Algoritmo Recursivo Detectado**")
                                    st.write(f"Ecuación de Recurrencia Base: `{hard.get('recurrence')}`")
                                else:
                                    st.success("Algoritmo Iterativo (Sin recursión)")

                        # === PESTAÑA 3: COSTOS POR LÍNEA ===
                        with tab3:
                            line_costs = hard.get("line_costs", {})
                            if line_costs and final_code:
                                code_lines = final_code.split('\n')
                                table_data = []
                                
                                for i, line_content in enumerate(code_lines):
                                    line_num = str(i + 1)
                                    cost = line_costs.get(line_num, "")
                                    
                                    # Lógica de visualización de costo
                                    cost_display = ""
                                    if cost == "2": cost_display = "C" # Constante
                                    elif cost: cost_display = cost     # Fórmula
                                    
                                    # Filtrar líneas vacías o estructurales sin costo
                                    if line_content.strip() and cost_display:
                                        table_data.append({
                                            "Línea": i + 1,
                                            "Código": line_content,
                                            "Costo": cost_display
                                        })
                                
                                if table_data:
                                    df = pd.DataFrame(table_data)
                                    st.dataframe(
                                        df, 
                                        hide_index=True, 
                                        use_container_width=True,
                                        column_config={
                                            "Línea": st.column_config.NumberColumn(format="%d"),
                                            "Código": st.column_config.TextColumn(width="medium"),
                                            "Costo": st.column_config.TextColumn(width="small")
                                        }
                                    )
                                else:
                                    st.info("No hay costos significativos para mostrar.")
                            else:
                                st.info("Desglose no disponible.")

                            # === PESTAÑA 4: ÁRBOL GRÁFICO ===
                        with tab4:
                            if ast_data:
                                st.success("Árbol Sintáctico Generado")
                                # ast_data es una lista, graficamos el primer nodo (Function)
                                graph = build_graphviz(ast_data[0])
                                st.graphviz_chart(graph)
                            else:
                                st.warning("No se generó el AST visual.")

                        # === PESTAÑA 5: CÓDIGO ===
                        with tab5:
                            st.markdown("### Código Normalizado (Pascal)")
                            st.code(data['input_analysis']['final_code'], language="pascal")

            except Exception as e:
                st.error(f"Error crítico de conexión o procesamiento: {e}")