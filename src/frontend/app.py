import streamlit as st
import requests
import json

# Configuración de la página
st.set_page_config(page_title="Analizador de Complejidad Algorítmica", layout="wide")

st.title("🧩 Analizador de Complejidad (Híbrido)")
st.markdown("""
Este sistema combina un **Motor de Análisis Matemático** (Determinista) con 
**Inteligencia Artificial** (Semántico) para analizar algoritmos.
""")

# Área de entrada
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Entrada del Algoritmo")
    input_text = st.text_area(
        "Escribe tu pseudocódigo o descripción en lenguaje natural:",
        height=300,
        placeholder="Ej: Haz un algoritmo que ordene un vector usando burbuja..."
    )
    analyze_btn = st.button("🔍 Analizar Complejidad", type="primary")

# Lógica de llamada a la API
if analyze_btn and input_text:
    with col2:
        st.subheader("Resultados del Análisis")
        with st.spinner('Procesando algoritmo... (Normalizando -> Parseando -> Analizando)'):
            try:
                # Llamada a TU API (Asegúrate de que uvicorn esté corriendo)
                response = requests.post("http://127.0.0.1:8000/analyze", json={"code": input_text})
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 1. Pestañas para organizar la info
                    tab1, tab2, tab3 = st.tabs(["📊 Informe Técnico", "🧮 Análisis Matemático", "📝 Código Generado"])
                    
                    # --- Pestaña 1: Informe (Lo que ve el usuario final) ---
                    soft = data.get("soft_analysis", {})
                    hard = data.get("hard_analysis", {})
                    
                    with tab1:
                        # Mostrar Estrategia con colorines
                        st.info(f"**Estrategia Identificada:** {soft.get('strategy', 'Desconocida')}")
                        st.success(f"**Complejidad Asintótica:** {hard.get('big_o', 'Indeterminada')}")
                        
                        st.write("### Explicación Técnica")
                        st.write(soft.get('explanation', 'Sin explicación.'))
                        
                        st.write("### Validación de Complejidad")
                        st.write(soft.get('complexity_validation', '-'))
                        
                        if soft.get('pattern_identified'):
                            st.write(f"**Patrón Similar:** {soft.get('pattern_identified')}")

                    # --- Pestaña 2: Detalles Matemáticos (Hard Analysis) ---
                    with tab2:
                        if "error_details" in hard:
                            st.error(f"El análisis determinista encontró limitaciones estructurales:")
                            st.code(hard['error_details'], language="text")
                            st.warning("Se ha utilizado la estimación heurística de la IA en el informe.")
                        else:
                            st.write(f"**Ecuación de Coste T(n):**")
                            st.latex(hard.get('cost_expression', ''))
                            
                            if hard.get('is_recursive'):
                                st.write("**Recursividad Detectada:** Sí")
                                st.write(f"Ecuación de Recurrencia: `{hard.get('recurrence_equation')}`")
                            else:
                                st.write("**Recursividad Detectada:** No (Iterativo)")

                    # --- Pestaña 3: Código Normalizado (Debugging) ---
                    with tab3:
                        st.write("El LLM tradujo tu entrada a este Pascal estricto:")
                        st.code(data['input_analysis']['normalized_pascal'], language="pascal")

                else:
                    st.error(f"Error del Servidor: {response.status_code}")
                    st.write(response.text)

            except Exception as e:
                st.error(f"No se pudo conectar con el backend. ¿Está corriendo uvicorn?")
                st.error(f"Detalle: {e}")