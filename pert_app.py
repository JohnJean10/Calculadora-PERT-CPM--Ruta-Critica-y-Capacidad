import streamlit as st
import pandas as pd
import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
import graphviz
import io
import copy

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="RK Power - Sistema de Planificación Multi-Modelo", layout="wide", page_icon="⚙️")

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
    .success-container {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 15px;
        border-radius: 5px;
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

# --- DEFINICIÓN DE RECETAS POR MODELO ---
RECETAS_DEFAULT = {
    "80-100KW": [
        {'ID': 'A', 'Actividad': 'Corte Tanque + Soporteria', 'Duracion_Min': 210.0, 'Predecesores': '', 'Recurso': 'Corte Láser', 'Componente': 'Tanque'},
        {'ID': 'B', 'Actividad': 'Corte Cabina', 'Duracion_Min': 65.0, 'Predecesores': '', 'Recurso': 'Corte Láser', 'Componente': 'Cabina'},
        {'ID': 'C', 'Actividad': 'Corte Sist. Escape', 'Duracion_Min': 91.0, 'Predecesores': 'B', 'Recurso': 'Corte Láser', 'Componente': 'Sistema Escape'},
        {'ID': 'D', 'Actividad': 'Corte Caja Breaker', 'Duracion_Min': 14.3, 'Predecesores': 'C', 'Recurso': 'Corte Láser', 'Componente': 'Caja Breaker'},
        {'ID': 'E', 'Actividad': 'Plegado Tanque', 'Duracion_Min': 408.0, 'Predecesores': 'A', 'Recurso': 'Plegadora', 'Componente': 'Tanque'},
        {'ID': 'F', 'Actividad': 'Soldadura Tanque', 'Duracion_Min': 328.2, 'Predecesores': 'E', 'Recurso': 'Soldadura', 'Componente': 'Tanque'},
        {'ID': 'G', 'Actividad': 'Plegado Cabina', 'Duracion_Min': 510.0, 'Predecesores': 'B', 'Recurso': 'Plegadora', 'Componente': 'Cabina'},
        {'ID': 'H', 'Actividad': 'Soldadura Cabina', 'Duracion_Min': 360.0, 'Predecesores': 'G', 'Recurso': 'Soldadura', 'Componente': 'Cabina'},
        {'ID': 'I', 'Actividad': 'Plegado Caja', 'Duracion_Min': 45.0, 'Predecesores': 'D', 'Recurso': 'Plegadora', 'Componente': 'Caja Breaker'},
        {'ID': 'J', 'Actividad': 'Soldadura Caja', 'Duracion_Min': 90.0, 'Predecesores': 'I', 'Recurso': 'Soldadura', 'Componente': 'Caja Breaker'},
        {'ID': 'K', 'Actividad': 'Pintura Tanque', 'Duracion_Min': 220.0, 'Predecesores': 'F', 'Recurso': 'Pintura (Auto)', 'Componente': 'Tanque'},
        {'ID': 'L', 'Actividad': 'Pintura Cabina', 'Duracion_Min': 545.0, 'Predecesores': 'H', 'Recurso': 'Pintura (Semi)', 'Componente': 'Cabina'},
        {'ID': 'M', 'Actividad': 'Ensamble Mecánico', 'Duracion_Min': 160.0, 'Predecesores': 'K,L', 'Recurso': 'Ensamble', 'Componente': 'Equipo Completo'},
        {'ID': 'N', 'Actividad': 'Ensamble Eléctrico', 'Duracion_Min': 210.0, 'Predecesores': 'M,J', 'Recurso': 'Ensamble', 'Componente': 'Equipo Completo'},
        {'ID': 'O', 'Actividad': 'Pruebas Carga', 'Duracion_Min': 37.5, 'Predecesores': 'N', 'Recurso': 'Pruebas', 'Componente': 'Equipo Completo'},
        {'ID': 'P', 'Actividad': 'Empaque Final', 'Duracion_Min': 15.0, 'Predecesores': 'O', 'Recurso': 'Empaque', 'Componente': 'Equipo Completo'}
    ],
    "125-200KW": [
        # Tiempos ~20% más altos para modelo más grande
        {'ID': 'A', 'Actividad': 'Corte Tanque + Soporteria', 'Duracion_Min': 252.0, 'Predecesores': '', 'Recurso': 'Corte Láser', 'Componente': 'Tanque'},
        {'ID': 'B', 'Actividad': 'Corte Cabina', 'Duracion_Min': 78.0, 'Predecesores': '', 'Recurso': 'Corte Láser', 'Componente': 'Cabina'},
        {'ID': 'C', 'Actividad': 'Corte Sist. Escape', 'Duracion_Min': 109.2, 'Predecesores': 'B', 'Recurso': 'Corte Láser', 'Componente': 'Sistema Escape'},
        {'ID': 'D', 'Actividad': 'Corte Caja Breaker', 'Duracion_Min': 17.2, 'Predecesores': 'C', 'Recurso': 'Corte Láser', 'Componente': 'Caja Breaker'},
        {'ID': 'E', 'Actividad': 'Plegado Tanque', 'Duracion_Min': 489.6, 'Predecesores': 'A', 'Recurso': 'Plegadora', 'Componente': 'Tanque'},
        {'ID': 'F', 'Actividad': 'Soldadura Tanque', 'Duracion_Min': 393.8, 'Predecesores': 'E', 'Recurso': 'Soldadura', 'Componente': 'Tanque'},
        {'ID': 'G', 'Actividad': 'Plegado Cabina', 'Duracion_Min': 612.0, 'Predecesores': 'B', 'Recurso': 'Plegadora', 'Componente': 'Cabina'},
        {'ID': 'H', 'Actividad': 'Soldadura Cabina', 'Duracion_Min': 432.0, 'Predecesores': 'G', 'Recurso': 'Soldadura', 'Componente': 'Cabina'},
        {'ID': 'I', 'Actividad': 'Plegado Caja', 'Duracion_Min': 54.0, 'Predecesores': 'D', 'Recurso': 'Plegadora', 'Componente': 'Caja Breaker'},
        {'ID': 'J', 'Actividad': 'Soldadura Caja', 'Duracion_Min': 108.0, 'Predecesores': 'I', 'Recurso': 'Soldadura', 'Componente': 'Caja Breaker'},
        {'ID': 'K', 'Actividad': 'Pintura Tanque', 'Duracion_Min': 264.0, 'Predecesores': 'F', 'Recurso': 'Pintura (Auto)', 'Componente': 'Tanque'},
        {'ID': 'L', 'Actividad': 'Pintura Cabina', 'Duracion_Min': 654.0, 'Predecesores': 'H', 'Recurso': 'Pintura (Semi)', 'Componente': 'Cabina'},
        {'ID': 'M', 'Actividad': 'Ensamble Mecánico', 'Duracion_Min': 192.0, 'Predecesores': 'K,L', 'Recurso': 'Ensamble', 'Componente': 'Equipo Completo'},
        {'ID': 'N', 'Actividad': 'Ensamble Eléctrico', 'Duracion_Min': 252.0, 'Predecesores': 'M,J', 'Recurso': 'Ensamble', 'Componente': 'Equipo Completo'},
        {'ID': 'O', 'Actividad': 'Pruebas Carga', 'Duracion_Min': 45.0, 'Predecesores': 'N', 'Recurso': 'Pruebas', 'Componente': 'Equipo Completo'},
        {'ID': 'P', 'Actividad': 'Empaque Final', 'Duracion_Min': 18.0, 'Predecesores': 'O', 'Recurso': 'Empaque', 'Componente': 'Equipo Completo'}
    ],
    "250-500KW": [
        # Tiempos ~50% más altos que el base
        {'ID': 'A', 'Actividad': 'Corte Tanque + Soporteria', 'Duracion_Min': 315.0, 'Predecesores': '', 'Recurso': 'Corte Láser', 'Componente': 'Tanque'},
        {'ID': 'B', 'Actividad': 'Corte Cabina', 'Duracion_Min': 97.5, 'Predecesores': '', 'Recurso': 'Corte Láser', 'Componente': 'Cabina'},
        {'ID': 'C', 'Actividad': 'Corte Sist. Escape', 'Duracion_Min': 136.5, 'Predecesores': 'B', 'Recurso': 'Corte Láser', 'Componente': 'Sistema Escape'},
        {'ID': 'D', 'Actividad': 'Corte Caja Breaker', 'Duracion_Min': 21.5, 'Predecesores': 'C', 'Recurso': 'Corte Láser', 'Componente': 'Caja Breaker'},
        {'ID': 'E', 'Actividad': 'Plegado Tanque', 'Duracion_Min': 612.0, 'Predecesores': 'A', 'Recurso': 'Plegadora', 'Componente': 'Tanque'},
        {'ID': 'F', 'Actividad': 'Soldadura Tanque', 'Duracion_Min': 492.3, 'Predecesores': 'E', 'Recurso': 'Soldadura', 'Componente': 'Tanque'},
        {'ID': 'G', 'Actividad': 'Plegado Cabina', 'Duracion_Min': 765.0, 'Predecesores': 'B', 'Recurso': 'Plegadora', 'Componente': 'Cabina'},
        {'ID': 'H', 'Actividad': 'Soldadura Cabina', 'Duracion_Min': 540.0, 'Predecesores': 'G', 'Recurso': 'Soldadura', 'Componente': 'Cabina'},
        {'ID': 'I', 'Actividad': 'Plegado Caja', 'Duracion_Min': 67.5, 'Predecesores': 'D', 'Recurso': 'Plegadora', 'Componente': 'Caja Breaker'},
        {'ID': 'J', 'Actividad': 'Soldadura Caja', 'Duracion_Min': 135.0, 'Predecesores': 'I', 'Recurso': 'Soldadura', 'Componente': 'Caja Breaker'},
        {'ID': 'K', 'Actividad': 'Pintura Tanque', 'Duracion_Min': 330.0, 'Predecesores': 'F', 'Recurso': 'Pintura (Auto)', 'Componente': 'Tanque'},
        {'ID': 'L', 'Actividad': 'Pintura Cabina', 'Duracion_Min': 817.5, 'Predecesores': 'H', 'Recurso': 'Pintura (Semi)', 'Componente': 'Cabina'},
        {'ID': 'M', 'Actividad': 'Ensamble Mecánico', 'Duracion_Min': 240.0, 'Predecesores': 'K,L', 'Recurso': 'Ensamble', 'Componente': 'Equipo Completo'},
        {'ID': 'N', 'Actividad': 'Ensamble Eléctrico', 'Duracion_Min': 315.0, 'Predecesores': 'M,J', 'Recurso': 'Ensamble', 'Componente': 'Equipo Completo'},
        {'ID': 'O', 'Actividad': 'Pruebas Carga', 'Duracion_Min': 56.3, 'Predecesores': 'N', 'Recurso': 'Pruebas', 'Componente': 'Equipo Completo'},
        {'ID': 'P', 'Actividad': 'Empaque Final', 'Duracion_Min': 22.5, 'Predecesores': 'O', 'Recurso': 'Empaque', 'Componente': 'Equipo Completo'}
    ]
}

# --- GESTIÓN DE ESTADO ---
if 'recetas' not in st.session_state:
    st.session_state.recetas = copy.deepcopy(RECETAS_DEFAULT)

if 'modelo_activo' not in st.session_state:
    st.session_state.modelo_activo = "80-100KW"

if 'plan_produccion' not in st.session_state:
    st.session_state.plan_produccion = pd.DataFrame({
        'Modelo': list(st.session_state.recetas.keys()),
        'Sem1': [2, 1, 0],
        'Sem2': [3, 1, 1],
        'Sem3': [2, 2, 0],
        'Sem4': [1, 0, 1]
    })

# --- SIDEBAR: CONFIGURACIÓN GLOBAL ---
with st.sidebar:
    st.header("⚙️ Configuración Global")
    
    st.subheader("📦 Modelo Activo")
    modelo_seleccionado = st.selectbox(
        "Selecciona modelo para editar receta:",
        list(st.session_state.recetas.keys())
    )
    st.session_state.modelo_activo = modelo_seleccionado
    
    st.divider()
    st.subheader("⏰ Turnos y Horarios")
    dias_sem = st.number_input("Días/Semana", 1, 7, 5)
    horas_dia = st.number_input("Horas/Turno", 1.0, 24.0, 8.55)
    turnos = st.number_input("Cant. Turnos", 1, 3, 1)
    tiempo_disponible = dias_sem * horas_dia * turnos * 60  # Minutos totales
    
    st.metric("Tiempo Disponible (Semanal)", f"{tiempo_disponible:,.0f} min")
    
    st.divider()
    st.subheader("💾 Gestión de Recetas")
    
    # Descargar receta del modelo activo
    df_receta_activa = pd.DataFrame(st.session_state.recetas[st.session_state.modelo_activo])
    csv_receta = df_receta_activa.to_csv(index=False).encode('utf-8')
    st.download_button(
        f"⬇️ Descargar {st.session_state.modelo_activo}",
        data=csv_receta, 
        file_name=f"receta_{st.session_state.modelo_activo}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    # Cargar receta
    uploaded_receta = st.file_uploader("⬆️ Cargar Receta (CSV)", type="csv", key="upload_receta")
    if uploaded_receta is not None:
        try:
            df_nueva_receta = pd.read_csv(uploaded_receta)
            required_cols = ['ID', 'Actividad', 'Duracion_Min', 'Predecesores', 'Recurso', 'Componente']
            if all(col in df_nueva_receta.columns for col in required_cols):
                st.session_state.recetas[st.session_state.modelo_activo] = df_nueva_receta.to_dict('records')
                st.success(f"Receta cargada para {st.session_state.modelo_activo}")
                st.rerun()
            else:
                st.error("El CSV debe tener: ID, Actividad, Duracion_Min, Predecesores, Recurso, Componente")
        except Exception as e:
            st.error(f"Error: {e}")

# --- PÁGINA PRINCIPAL ---
st.title("🏭 RK Power: Sistema Multi-Modelo con Heijunka")

# TABS PRINCIPALES
tab_editor, tab_planificacion, tab_componentes, tab_capacidad, tab_pert = st.tabs([
    "✏️ Editor de Recetas", 
    "📅 Planificación",
    "🔩 Componentes",
    "📊 Análisis de Capacidad", 
    "🕸️ Red PERT"
])

# --- TAB 1: EDITOR DE RECETAS ---
with tab_editor:
    st.markdown(f"### 🛠️ Receta del Modelo: **{st.session_state.modelo_activo}**")
    st.info("Edita los tiempos y secuencias. Los cambios afectarán solo este modelo.")
    
    df_modelo_actual = pd.DataFrame(st.session_state.recetas[st.session_state.modelo_activo])
    
    edited_receta = st.data_editor(
        df_modelo_actual,
        num_rows="dynamic",
        column_config={
            "ID": st.column_config.TextColumn("ID", max_chars=5, required=True),
            "Actividad": st.column_config.TextColumn("Descripción", required=True),
            "Duracion_Min": st.column_config.NumberColumn("Duración (min)", min_value=0.1, format="%.1f"),
            "Predecesores": st.column_config.TextColumn("Predecesores (separados por coma)"),
            "Recurso": st.column_config.SelectboxColumn("Área / Recurso", options=[
                "Corte Láser", "Plegadora", "Soldadura", "Pintura (Auto)", 
                "Pintura (Semi)", "Ensamble", "Pruebas", "Empaque", "Otros"
            ], required=True),
            "Componente": st.column_config.TextColumn("Componente")
        },
        use_container_width=True,
        key=f"editor_{st.session_state.modelo_activo}"
    )
    
    if not edited_receta.equals(df_modelo_actual):
        st.session_state.recetas[st.session_state.modelo_activo] = edited_receta.to_dict('records')
        st.rerun()

# --- TAB 2: PLANIFICACIÓN ---
with tab_planificacion:
    st.markdown("### 📅 Plan de Producción Multi-Modelo")
    st.info("Define cuántos equipos de cada modelo producir por semana. El sistema calculará la carga total y secuencia Heijunka.")
    
    # Editor de demanda
    plan_editado = st.data_editor(
        st.session_state.plan_produccion,
        column_config={
            "Modelo": st.column_config.TextColumn("Modelo", disabled=True),
            "Sem1": st.column_config.NumberColumn("Semana 1", min_value=0, format="%d"),
            "Sem2": st.column_config.NumberColumn("Semana 2", min_value=0, format="%d"),
            "Sem3": st.column_config.NumberColumn("Semana 3", min_value=0, format="%d"),
            "Sem4": st.column_config.NumberColumn("Semana 4", min_value=0, format="%d"),
        },
        use_container_width=True,
        hide_index=True,
        key="plan_produccion_editor"
    )
    
    if not plan_editado.equals(st.session_state.plan_produccion):
        st.session_state.plan_produccion = plan_editado
        st.rerun()
    
    st.divider()
    
    # Calcular carga total por recurso
    col_vista1, col_vista2 = st.columns([2, 1])
    
    with col_vista1:
        st.subheader("Carga Agregada por Recurso (Semana 1)")
        
        # Calcular para Semana 1
        carga_total = {}
        for idx, row in st.session_state.plan_produccion.iterrows():
            modelo = row['Modelo']
            cantidad = row['Sem1']
            
            if cantidad > 0:
                receta = st.session_state.recetas[modelo]
                for actividad in receta:
                    recurso = actividad['Recurso']
                    tiempo = actividad['Duracion_Min'] * cantidad
                    
                    if recurso in carga_total:
                        carga_total[recurso] += tiempo
                    else:
                        carga_total[recurso] = tiempo
        
        if carga_total:
            df_carga = pd.DataFrame([
                {'Recurso': k, 'Carga_Min': v} for k, v in carga_total.items()
            ])
            df_carga['Capacidad_%'] = (df_carga['Carga_Min'] / tiempo_disponible) * 100
            df_carga['Estado'] = df_carga['Capacidad_%'].apply(
                lambda x: "🔴 Sobrecarga" if x > 100 else ("🟡 Alerta" if x > 85 else "🟢 OK")
            )
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_carga['Recurso'],
                y=df_carga['Carga_Min'],
                name='Carga (min)',
                marker_color=df_carga['Estado'].map({
                    "🔴 Sobrecarga": "#ff4b4b",
                    "🟡 Alerta": "#ffc107",
                    "🟢 OK": "#28a745"
                }),
                text=df_carga['Capacidad_%'].apply(lambda x: f"{x:.0f}%"),
                textposition='auto'
            ))
            fig.add_trace(go.Scatter(
                x=df_carga['Recurso'],
                y=[tiempo_disponible] * len(df_carga),
                mode='lines',
                name='Capacidad',
                line=dict(color='black', width=2, dash='dash')
            ))
            fig.update_layout(yaxis_title="Minutos", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay demanda planificada para Semana 1")
    
    with col_vista2:
        st.subheader("Secuencia Heijunka (Sem 1)")
        
        # Generar secuencia nivelada
        total_sem1 = st.session_state.plan_produccion['Sem1'].sum()
        if total_sem1 > 0:
            secuencia = []
            demanda_dict = dict(zip(
                st.session_state.plan_produccion['Modelo'],
                st.session_state.plan_produccion['Sem1']
            ))
            
            # Algoritmo de nivelación simple (repetir hasta completar)
            while sum(demanda_dict.values()) > 0:
                for modelo, cant in demanda_dict.items():
                    if cant > 0:
                        secuencia.append(modelo)
                        demanda_dict[modelo] -= 1
            
            st.write(f"**Total:** {total_sem1} equipos")
            st.write("**Orden de producción:**")
            st.code(" → ".join(secuencia[:20]) + ("..." if len(secuencia) > 20 else ""))
            
            st.metric("WIP Recomendado", f"{min(3, total_sem1)} equipos", 
                     help="Máximo de equipos en proceso simultáneo")
        else:
            st.info("Sin producción esta semana")

# --- TAB 3: COMPONENTES ---
with tab_componentes:
    st.markdown("### 🔩 Vista por Componentes (Semana 1)")
    st.info("Desglosa la producción a nivel de componente individual (Tanque, Cabina, etc.)")
    
    componentes_totales = {}
    
    for idx, row in st.session_state.plan_produccion.iterrows():
        modelo = row['Modelo']
        cantidad_sem1 = row['Sem1']
        
        if cantidad_sem1 > 0:
            receta = st.session_state.recetas[modelo]
            for actividad in receta:
                comp = actividad['Componente']
                if comp not in componentes_totales:
                    componentes_totales[comp] = {'cantidad': 0, 'modelos': set()}
                componentes_totales[comp]['cantidad'] += cantidad_sem1
                componentes_totales[comp]['modelos'].add(modelo)
    
    if componentes_totales:
        df_comp = pd.DataFrame([
            {
                'Componente': k,
                'Cantidad Total': v['cantidad'],
                'Modelos': ', '.join(v['modelos'])
            }
            for k, v in componentes_totales.items()
        ])
        
        st.dataframe(df_comp, use_container_width=True, hide_index=True)
        
        # Gráfico de componentes
        fig_comp = px.bar(df_comp, x='Componente', y='Cantidad Total', 
                          title="Demanda de Componentes - Semana 1")
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.warning("No hay producción planificada")

# --- TAB 4: ANÁLISIS DE CAPACIDAD ---
with tab_capacidad:
    st.markdown("### 📊 Análisis de Capacidad Multi-Modelo")
    
    # Mostrar tabla detallada
    if carga_total:
        st.dataframe(df_carga, use_container_width=True, hide_index=True)
        
        sobrecargas = df_carga[df_carga['Capacidad_%'] > 100]
        if not sobrecargas.empty:
            st.error(f"⛔ {len(sobrecargas)} recursos sobrecargados")
            for _, rec in sobrecargas.iterrows():
                st.markdown(f"""
                <div class="alert-container">
                    <strong>{rec['Recurso']}</strong><br>
                    Carga: {rec['Carga_Min']:.0f} min ({rec['Capacidad_%']:.0f}%)<br>
                    Exceso: +{rec['Carga_Min'] - tiempo_disponible:.0f} min<br>
                    💡 Necesitas agregar turnos o reducir demanda
                </div><br>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ Todos los recursos tienen capacidad suficiente")
    else:
        st.info("Configura demanda en el tab Planificación")

# --- TAB 5: RED PERT (del modelo activo) ---
with tab_pert:
    st.markdown(f"### 🕸️ Red PERT: **{st.session_state.modelo_activo}**")
    
    receta_activa = st.session_state.recetas[st.session_state.modelo_activo]
    edited_df = pd.DataFrame(receta_activa)
    
    G = nx.DiGraph()
    
    for _, row in edited_df.iterrows():
        G.add_node(row['ID'], duration=row['Duracion_Min'], desc=row['Actividad'])
    
    try:
        for _, row in edited_df.iterrows():
            if pd.notna(row['Predecesores']) and str(row['Predecesores']).strip() != "":
                preds = [p.strip() for p in str(row['Predecesores']).split(',')]
                for p in preds:
                    if p in G.nodes:
                        G.add_edge(p, row['ID'])
        
        if not nx.is_directed_acyclic_graph(G):
            st.error("❌ Ciclo detectado en dependencias")
        else:
            # Cálculo CPM
            ES = {}; EF = {}
            for n in nx.topological_sort(G):
                dur = G.nodes[n]['duration']
                preds = list(G.predecessors(n))
                start = max([EF[p] for p in preds]) if preds else 0
                ES[n] = start
                EF[n] = start + dur
            
            project_duration = max(EF.values()) if EF else 0
            
            LS = {}; LF = {}; Slack = {}
            for n in reversed(list(nx.topological_sort(G))):
                dur = G.nodes[n]['duration']
                succs = list(G.successors(n))
                finish = min([LS[s] for s in succs]) if succs else project_duration
                LF[n] = finish
                LS[n] = finish - dur
                Slack[n] = LS[n] - ES[n]
                G.nodes[n]['Critical'] = (abs(Slack[n]) < 0.001)
            
            # KPIs
            ruta_critica_ids = [n for n in G.nodes if G.nodes[n]['Critical']]
            
            col_k1, col_k2, col_k3 = st.columns(3)
            col_k1.metric("🕐 Lead Time", f"{project_duration:.1f} min")
            col_k2.metric("🔴 Tareas Críticas", f"{len(ruta_critica_ids)} de {len(G.nodes)}")
            col_k3.metric("🛣️ Ruta Crítica", " → ".join(ruta_critica_ids))
            
            sub_pert, sub_gantt, sub_datos = st.tabs(["🕸️ Red PERT", "📅 Gantt", "📋 Datos CPM"])
            
            with sub_pert:
                orientacion = st.radio("Orientación:", ["Horizontal", "Vertical (Móvil)"], horizontal=True)
                rankdir_val = 'TB' if 'Vertical' in orientacion else 'LR'
                
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
                
                try:
                    png_data = viz.pipe(format='png')
                    st.download_button("⬇️ Descargar Red PERT (PNG)", data=png_data, file_name=f"pert_{st.session_state.modelo_activo}.png", mime="image/png")
                except Exception:
                    st.caption("ℹ️ Instala Graphviz para descargar PNG")
            
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
                        title=f"Cronograma: {st.session_state.modelo_activo}"
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
        st.warning(f"Error en cálculo PERT: {e}")
