import streamlit as st
import pandas as pd
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import graphviz
import io

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="RK Power - Gestor Dinámico de Capacidad", layout="wide", page_icon="⚙️")

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .metric-container {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 20px;
        border-radius: 5px;
        border-left: 5px solid #1f77b4;
    }
    .alert-container {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        padding: 15px;
        border-radius: 5px;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. GESTIÓN DE ESTADO (SESSION STATE) ---
# Aquí inicializamos los datos. Si el usuario ya editó algo, no lo borramos.
if 'df_actividades' not in st.session_state:
    # Datos base extraídos de tus archivos (Generadores 80-100KW)
    default_data = [
        {'ID': 'A', 'Actividad': 'Corte Tanque + Soporteria', 'Duracion_Min': 210.0, 'Predecesores': '', 'Recurso': 'Corte Láser'},
        {'ID': 'B', 'Actividad': 'Corte Cabina', 'Duracion_Min': 65.0, 'Predecesores': '', 'Recurso': 'Corte Láser'},
        {'ID': 'C', 'Actividad': 'Corte Sist. Escape', 'Duracion_Min': 91.0, 'Predecesores': 'B', 'Recurso': 'Corte Láser'},
        {'ID': 'D', 'Actividad': 'Corte Caja Breaker', 'Duracion_Min': 14.3, 'Predecesores': 'C', 'Recurso': 'Corte Láser'},
        {'ID': 'E', 'Actividad': 'Plegado Tanque', 'Duracion_Min': 408.0, 'Predecesores': 'A', 'Recurso': 'Plegadora'},
        {'ID': 'F', 'Actividad': 'Soldadura Tanque', 'Duracion_Min': 328.2, 'Predecesores': 'E', 'Recurso': 'Soldadura'},
        {'ID': 'G', 'Actividad': 'Plegado Cabina', 'Duracion_Min': 510.0, 'Predecesores': 'B', 'Recurso': 'Plegadora'},
        {'ID': 'H', 'Actividad': 'Soldadura Cabina', 'Duracion_Min': 360.0, 'Predecesores': 'G', 'Recurso': 'Soldadura'},
        {'ID': 'I', 'Actividad': 'Plegado Caja', 'Duracion_Min': 45.0, 'Predecesores': 'D', 'Recurso': 'Plegadora'},
        {'ID': 'J', 'Actividad': 'Soldadura Caja', 'Duracion_Min': 90.0, 'Predecesores': 'I', 'Recurso': 'Soldadura'},
        {'ID': 'K', 'Actividad': 'Pintura Tanque', 'Duracion_Min': 220.0, 'Predecesores': 'F', 'Recurso': 'Pintura (Auto)'},
        {'ID': 'L', 'Actividad': 'Pintura Cabina', 'Duracion_Min': 545.0, 'Predecesores': 'H', 'Recurso': 'Pintura (Semi)'},
        {'ID': 'M', 'Actividad': 'Ensamble Mecánico', 'Duracion_Min': 160.0, 'Predecesores': 'K,L', 'Recurso': 'Ensamble'},
        {'ID': 'N', 'Actividad': 'Ensamble Eléctrico', 'Duracion_Min': 210.0, 'Predecesores': 'M,J', 'Recurso': 'Ensamble'},
        {'ID': 'O', 'Actividad': 'Pruebas Carga', 'Duracion_Min': 37.5, 'Predecesores': 'N', 'Recurso': 'Pruebas'},
        {'ID': 'P', 'Actividad': 'Empaque Final', 'Duracion_Min': 15.0, 'Predecesores': 'O', 'Recurso': 'Empaque'}
    ]
    st.session_state.df_actividades = pd.DataFrame(default_data)

# --- SIDEBAR: PARAMETROS GLOBALES ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    
    st.subheader("1. Turnos y Horarios")
    dias_sem = st.number_input("Días/Semana", 1, 7, 5)
    horas_dia = st.number_input("Horas/Turno", 1.0, 24.0, 8.55)
    turnos = st.number_input("Cant. Turnos", 1, 3, 1)
    tiempo_disponible = dias_sem * horas_dia * turnos * 60 # Minutos totales
    
    st.metric("Tiempo Disponible (Semanal)", f"{tiempo_disponible:,.0f} min")
    
    st.subheader("2. Demanda Objetivo")
    meta_equipos = st.number_input("Meta Equipos/Semana", 1, 50, 6)
    takt_time = tiempo_disponible / meta_equipos
    st.metric("Takt Time (Ritmo Necesario)", f"{takt_time:.1f} min/eq", delta_color="inverse")
    
    st.markdown("---")
    st.subheader("💾 Gestión de Archivos")
    # Botón para descargar la configuración actual
    csv = st.session_state.df_actividades.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Descargar Configuración Actual", data=csv, file_name="rk_config_actual.csv", mime="text/csv")
    
    # Botón para subir una configuración nueva
    uploaded_file = st.file_uploader("⬆️ Cargar Configuración (CSV)", type="csv")
    if uploaded_file is not None:
        try:
            df_uploaded = pd.read_csv(uploaded_file)
            # Validación básica de columnas
            required_cols = ['ID', 'Actividad', 'Duracion_Min', 'Predecesores', 'Recurso']
            if all(col in df_uploaded.columns for col in required_cols):
                st.session_state.df_actividades = df_uploaded
                st.success("¡Datos cargados correctamente!")
                st.rerun()
            else:
                st.error("El CSV debe tener columnas: ID, Actividad, Duracion_Min, Predecesores, Recurso")
        except Exception as e:
            st.error(f"Error al leer archivo: {e}")

# --- PÁGINA PRINCIPAL ---
st.title("🏭 RK Power: Centro de Ingeniería de Procesos")

# TABS PRINCIPALES
tab_editor, tab_analisis, tab_pert = st.tabs(["✏️ Editor de Actividades", "📊 Análisis de Capacidad", "🕸️ Diagrama PERT"])

# --- TAB 1: EDITOR DE DATOS (EL CORAZÓN DE LA APP) ---
with tab_editor:
    st.markdown("### 🛠️ Tabla Maestra de Actividades")
    st.info("Modifica los tiempos, nombres o recursos aquí. Los cálculos se actualizarán automáticamente. Puedes agregar filas para nuevas tareas.")
    
    # WIDGET DE EDICIÓN DE DATOS
    # num_rows="dynamic" permite añadir o borrar filas
    edited_df = st.data_editor(
        st.session_state.df_actividades,
        num_rows="dynamic",
        column_config={
            "ID": st.column_config.TextColumn("ID", max_chars=5, required=True),
            "Actividad": st.column_config.TextColumn("Descripción", required=True),
            "Duracion_Min": st.column_config.NumberColumn("Duración (min)", min_value=0.1, format="%.1f"),
            "Predecesores": st.column_config.TextColumn("Predecesores (ID separados por coma)"),
            "Recurso": st.column_config.SelectboxColumn("Área / Recurso", options=[
                "Corte Láser", "Plegadora", "Soldadura", "Pintura (Auto)", 
                "Pintura (Semi)", "Ensamble", "Pruebas", "Empaque", "Otros"
            ], required=True)
        },
        use_container_width=True,
        key="editor_data"
    )
    
    # Guardar cambios en Session State automáticamente
    if not edited_df.equals(st.session_state.df_actividades):
        st.session_state.df_actividades = edited_df
        st.rerun()

# --- LÓGICA DE CÁLCULO (SE EJECUTA CON LOS DATOS EDITADOS) ---
# 1. Agrupar por Recurso para Capacidad
df_recursos = edited_df.groupby('Recurso')['Duracion_Min'].sum().reset_index()
df_recursos['Capacidad_Max_Eq'] = tiempo_disponible / df_recursos['Duracion_Min']
df_recursos['Utilizacion_%'] = (df_recursos['Duracion_Min'] / takt_time) * 100
df_recursos['Estado'] = df_recursos['Utilizacion_%'].apply(lambda x: "🔴 Cuello Botella" if x > 100 else ("🟡 Alerta" if x > 85 else "🟢 OK"))

# --- TAB 2: ANÁLISIS DE CAPACIDAD ---
with tab_analisis:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Carga de Trabajo vs Takt Time")
        
        # Gráfico de barras mejorado
        fig = go.Figure()
        
        # Barras de carga
        fig.add_trace(go.Bar(
            x=df_recursos['Recurso'],
            y=df_recursos['Duracion_Min'],
            name='Carga Total (min)',
            marker_color=df_recursos['Estado'].map({
                "🔴 Cuello Botella": "#ff4b4b", 
                "🟡 Alerta": "#ffc107", 
                "🟢 OK": "#28a745"
            }),
            text=df_recursos['Utilizacion_%'].apply(lambda x: f"{x:.0f}%"),
            textposition='auto'
        ))
        
        # Línea de Takt Time
        fig.add_trace(go.Scatter(
            x=df_recursos['Recurso'],
            y=[takt_time] * len(df_recursos),
            mode='lines',
            name='Takt Time (Límite)',
            line=dict(color='black', width=3, dash='dash')
        ))
        
        fig.update_layout(yaxis_title="Minutos por Equipo", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Diagnóstico de Restricciones")
        
        bottlenecks = df_recursos[df_recursos['Estado'] == "🔴 Cuello Botella"]
        
        if not bottlenecks.empty:
            st.error(f"⛔ El sistema NO puede cumplir la meta de {meta_equipos} equipos.")
            st.write("Recursos limitantes:")
            for _, row in bottlenecks.iterrows():
                deficit = row['Duracion_Min'] - takt_time
                st.markdown(f"""
                <div class="alert-container">
                    <strong>{row['Recurso']}</strong><br>
                    ⏱️ Ciclo: {row['Duracion_Min']:.1f} min<br>
                    📉 Exceso: +{deficit:.1f} min<br>
                    📦 Capacidad Real: {row['Capacidad_Max_Eq']:.2f} eq/sem
                </div><br>
                """, unsafe_allow_html=True)
                
                # Recomendación automática
                st.info(f"💡 Sugerencia para {row['Recurso']}: Necesitas reducir el tiempo en un {row['Utilizacion_%']-100:.1f}% o agregar turnos.")
        else:
            st.success(f"✅ ¡Excelente! Tu planta tiene capacidad para {meta_equipos} equipos/semana.")
            st.write(f"Cuello de botella más cercano: **{df_recursos.loc[df_recursos['Utilizacion_%'].idxmax(), 'Recurso']}** ({df_recursos['Utilizacion_%'].max():.1f}%)")

# --- TAB 3: PERT Y RUTA CRÍTICA ---
with tab_pert:
    st.subheader("Diagrama de Flujo y Cálculo de Ruta Crítica")
    
    # Lógica de Grafos
    G = nx.DiGraph()
    
    # 1. Nodos
    for _, row in edited_df.iterrows():
        G.add_node(row['ID'], duration=row['Duracion_Min'], desc=row['Actividad'])
    
    # 2. Aristas (Conexiones)
    try:
        for _, row in edited_df.iterrows():
            if pd.notna(row['Predecesores']) and str(row['Predecesores']).strip() != "":
                preds = [p.strip() for p in str(row['Predecesores']).split(',')]
                for p in preds:
                    if p in G.nodes:
                        G.add_edge(p, row['ID'])
        
        # 3. Cálculo CPM
        if not nx.is_directed_acyclic_graph(G):
            st.error("❌ Error: Se detectó un ciclo en las dependencias (ej: A depende de B y B depende de A). Revisa la columna 'Predecesores'.")
        else:
            # Forward Pass
            ES = {}; EF = {}
            for n in nx.topological_sort(G):
                dur = G.nodes[n]['duration']
                preds = list(G.predecessors(n))
                start = max([EF[p] for p in preds]) if preds else 0
                ES[n] = start
                EF[n] = start + dur
            
            project_duration = max(EF.values()) if EF else 0
            
            # Backward Pass
            LS = {}; LF = {}; Slack = {}
            for n in reversed(list(nx.topological_sort(G))):
                dur = G.nodes[n]['duration']
                succs = list(G.successors(n))
                finish = min([LS[s] for s in succs]) if succs else project_duration
                LF[n] = finish
                LS[n] = finish - dur
                Slack[n] = LS[n] - ES[n]
                G.nodes[n]['Critical'] = (abs(Slack[n]) < 0.001)

            # --- KPIs ---
            ruta_critica_ids = [n for n in G.nodes if G.nodes[n]['Critical']]
            
            col_k1, col_k2, col_k3 = st.columns(3)
            col_k1.metric("🕐 Lead Time", f"{project_duration:.1f} min")
            col_k2.metric("🔴 Tareas Críticas", f"{len(ruta_critica_ids)} de {len(G.nodes)}")
            col_k3.metric("🛣️ Ruta Crítica", " → ".join(ruta_critica_ids))
            
            # --- Sub-Tabs: Red PERT + Gantt ---
            sub_pert, sub_gantt, sub_datos = st.tabs(["🕸️ Red PERT", "📅 Gantt", "📋 Datos CPM"])
            
            with sub_pert:
                # Selector de orientación
                orientacion = st.radio("Orientación:", ["Horizontal", "Vertical (Móvil)"], horizontal=True)
                rankdir_val = 'TB' if 'Vertical' in orientacion else 'LR'
                
                # Encontrar cuello de botella (tarea más larga)
                nodos_dur = {n: G.nodes[n]['duration'] for n in G.nodes}
                cb_id = max(nodos_dur, key=nodos_dur.get)
                
                viz = graphviz.Digraph()
                viz.attr(rankdir=rankdir_val, splines='ortho', nodesep='0.6')
                viz.attr('node', shape='record', style='filled', fontname='Arial', fontsize='10')
                
                for n in G.nodes:
                    d = G.nodes[n]
                    color = '#ffcccc' if d['Critical'] else '#f0f0f0'
                    if n == cb_id:
                        color = '#ffe0b2'
                    penwidth = '3.0' if d['Critical'] else '1.0'
                    label = f"{{ {n}: {d['desc']} | {d['duration']:.1f} min }} | {{ ES: {ES[n]:.1f} | EF: {EF[n]:.1f} }} | {{ LS: {LS[n]:.1f} | LF: {LF[n]:.1f} }}"
                    viz.node(n, label=label, fillcolor=color, penwidth=penwidth, color='red' if d['Critical'] else 'black')
                
                for u, v in G.edges():
                    is_crit = G.nodes[u]['Critical'] and G.nodes[v]['Critical']
                    viz.edge(u, v, color='red' if is_crit else 'gray', penwidth='2.0' if is_crit else '1.0')
                
                st.graphviz_chart(viz, use_container_width=True)
                st.caption("🟠 Naranja: Cuello de Botella | 🔴 Rojo: Ruta Crítica")
                
                # Botón descarga PNG
                try:
                    png_data = viz.pipe(format='png')
                    st.download_button("⬇️ Descargar Red PERT (PNG)", data=png_data, file_name="red_pert.png", mime="image/png")
                except Exception:
                    st.caption("ℹ️ Instala Graphviz en tu PC para descargar PNG.")
            
            with sub_gantt:
                gantt_data = []
                for n in G.nodes:
                    gantt_data.append({
                        'Tarea': f"{n} - {G.nodes[n]['desc']}",
                        'Inicio': ES[n],
                        'Fin': EF[n],
                        'Duración': G.nodes[n]['duration'],
                        'Crítica': 'Sí' if G.nodes[n]['Critical'] else 'No'
                    })
                
                df_gantt = pd.DataFrame(gantt_data)
                
                if not df_gantt.empty:
                    fig_gantt = px.bar(
                        df_gantt, 
                        x='Duración', 
                        y='Tarea', 
                        base='Inicio',
                        orientation='h',
                        color='Crítica',
                        color_discrete_map={'Sí': '#ff4b4b', 'No': '#adb5bd'},
                        title="Cronograma de Producción (Ruta Crítica en Rojo)"
                    )
                    fig_gantt.update_layout(xaxis_title="Minutos Acumulados")
                    st.plotly_chart(fig_gantt, use_container_width=True)
            
            with sub_datos:
                tabla_cpm = []
                for n in G.nodes:
                    tabla_cpm.append({
                        'ID': n, 'Actividad': G.nodes[n]['desc'],
                        'Duración': G.nodes[n]['duration'],
                        'ES': ES[n], 'EF': EF[n], 'LS': LS[n], 'LF': LF[n],
                        'Holgura': Slack[n],
                        '¿Crítica?': '✅' if G.nodes[n]['Critical'] else '❌'
                    })
                st.dataframe(tabla_cpm, use_container_width=True, hide_index=True)

    except Exception as e:
        st.warning(f"Esperando datos válidos de predecesores... ({e})")
