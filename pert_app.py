import streamlit as st
import graphviz
import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math
import io

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Calculadora PERT/CPM", layout="wide")
st.markdown("""
<style>
    .metric-card {
        background-color: #fff3e0 !important; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #ff4b4b;
        color: #1a1a1a !important;
    }
    .metric-card b, .metric-card li, .metric-card ul {
        color: #1a1a1a !important;
    }
    .success-card {
        background-color: #e8f5e9 !important; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #2e7d32;
        color: #1a1a1a !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE EXPORTACIÓN EXCEL ---
def generar_excel(dfs_dict):
    """Genera un archivo Excel en memoria con múltiples hojas y formato."""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    workbook = writer.book
    header_fmt = workbook.add_format({
        'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#4F81BD', 'font_color': '#FFFFFF', 'border': 1
    })
    
    for sheet_name, df in dfs_dict.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        
        # Ajustar ancho de columnas y aplicar formato
        for idx, col in enumerate(df.columns):
            series = df[col]
            max_len =  max((
                series.astype(str).map(len).max(),
                len(str(col))
            )) + 2
            worksheet.set_column(idx, idx, max_len)
            worksheet.write(0, idx, col, header_fmt)
            
    writer.close()
    return output.getvalue()

# --- 2. MOTOR LÓGICO CPM ---
def calcular_cpm(tareas):
# ... resto de la importacion original hasta la UI ...
# (Mantengo el resto del codigo igual hasta la seccion de tabs, donde insertare los botones)

    """
    Recibe una lista de diccionarios: {'id': 'A', 'nombre': 'Proceso', 'dur': 3, 'preds': ['B']}
    Retorna un grafo con atributos calculados (ES, EF, LS, LF, Holgura).
    """
    G = nx.DiGraph()
    
    # Crear diccionario de nombres para referencia
    nombres_tareas = {t['id']: t.get('nombre', t['id']) for t in tareas}
    
    # 1. Construir el Grafo
    for t in tareas:
        G.add_node(t['id'], duration=t['dur'], nombre=t.get('nombre', t['id']))
    
    for t in tareas:
        for p in t['preds']:
            if p in G.nodes:
                G.add_edge(p, t['id'])
    
    # Verificar ciclos (IMPORTANTE)
    if not nx.is_directed_acyclic_graph(G):
        return None, "Error: El diagrama tiene un bucle (ciclo) infinito."

    # 2. Forward Pass (Ida) -> ES y EF
    topo_order = list(nx.topological_sort(G))
    
    for n in topo_order:
        dur = G.nodes[n]['duration']
        preds = list(G.predecessors(n))
        if not preds:
            es = 0
        else:
            es = max([G.nodes[p]['EF'] for p in preds])
        
        ef = es + dur
        G.nodes[n]['ES'] = es
        G.nodes[n]['EF'] = ef

    # 3. Backward Pass (Vuelta) -> LS y LF
    max_ef = max([G.nodes[n]['EF'] for n in G.nodes])
    
    for n in reversed(topo_order):
        dur = G.nodes[n]['duration']
        succs = list(G.successors(n))
        
        if not succs:
            lf = max_ef
        else:
            lf = min([G.nodes[s]['LS'] for s in succs])
            
        ls = lf - dur
        holgura = ls - G.nodes[n]['ES']
        
        G.nodes[n]['LF'] = lf
        G.nodes[n]['LS'] = ls
        G.nodes[n]['Holgura'] = holgura
        G.nodes[n]['EsCritica'] = (holgura == 0)

    return G, max_ef

# --- FUNCIÓN DE ANÁLISIS DE WIP ---
def analizar_carga_wip(grafo, duracion_total):
    """Analiza la carga de trabajo (WIP) en el tiempo para ASAP y ALAP."""
    eje_tiempo = list(range(duracion_total + 1))
    
    wip_asap = [0] * len(eje_tiempo)
    wip_alap = [0] * len(eje_tiempo)
    
    nodos_data = []
    
    for n, datos in grafo.nodes(data=True):
        nombre_completo = f"{n}: {datos.get('nombre', n)}"
        nodos_data.append({
            'Tarea': nombre_completo, 
            'Inicio_ES': datos['ES'], 'Fin_EF': datos['EF'],
            'Inicio_LS': datos['LS'], 'Fin_LF': datos['LF'],
            'Critica': datos['EsCritica']
        })
        
        for t in range(datos['ES'], datos['EF']):
            if t < len(wip_asap):
                wip_asap[t] += 1
                
        for t in range(datos['LS'], datos['LF']):
            if t < len(wip_alap):
                wip_alap[t] += 1

    return wip_asap, wip_alap, pd.DataFrame(nodos_data), eje_tiempo

# --- 3. INTERFAZ PRINCIPAL ---
st.title("📊 Calculadora PERT/CPM - Ruta Crítica y Capacidad")

# --- SIDEBAR: DATOS DE ENTRADA ---
with st.sidebar:
    st.header("⚙️ Configuración del Proyecto")
    
    # Selector de unidad de tiempo
    if 'unidad_tiempo' not in st.session_state:
        st.session_state.unidad_tiempo = "minutos"
    
    unidad = st.selectbox(
        "Unidad de Duración:",
        ["minutos", "horas", "días", "semanas", "meses"],
        index=["minutos", "horas", "días", "semanas", "meses"].index(st.session_state.unidad_tiempo)
    )
    st.session_state.unidad_tiempo = unidad
    
    tiempo_semanal = st.number_input(f"{unidad.capitalize()} Disponibles por Periodo", value=40, help="Ej: 40 horas semanales, 5 días hábiles, etc.")
    meta_semanal = st.number_input("Meta de Entregas por Periodo", value=1, min_value=1)
    
    st.divider()
    st.header("📋 Definir Tareas")
    
    # Datos iniciales precargados (ejemplo genérico)
    if 'lista_tareas' not in st.session_state:
        st.session_state.lista_tareas = [
            {'id': 'A', 'nombre': 'Planificación', 'dur': 3, 'preds': []},
            {'id': 'B', 'nombre': 'Diseño', 'dur': 5, 'preds': ['A']},
            {'id': 'C', 'nombre': 'Desarrollo', 'dur': 8, 'preds': ['B']},
            {'id': 'D', 'nombre': 'Pruebas', 'dur': 4, 'preds': ['C']},
            {'id': 'E', 'nombre': 'Documentación', 'dur': 2, 'preds': ['C']},
            {'id': 'F', 'nombre': 'Entrega Final', 'dur': 1, 'preds': ['D', 'E']}
        ]

    # Formulario para agregar nueva tarea
    with st.form("form_agregar"):
        st.subheader("➕ Agregar Nueva Tarea")
        col1, col2 = st.columns(2)
        nuevo_id = col1.text_input("ID Tarea").upper()
        nueva_dur = col2.number_input(f"Duración ({unidad})", min_value=1, value=1)
        nuevo_nombre = st.text_input("Nombre de la Actividad")
        nuevos_preds = st.text_input("Predecesores (separados por coma)")
        
        submit = st.form_submit_button("➕ Agregar Tarea", use_container_width=True)
        
        if submit and nuevo_id:
            ids_existentes = [t['id'] for t in st.session_state.lista_tareas]
            if nuevo_id in ids_existentes:
                st.error(f"⚠️ Ya existe una tarea con ID '{nuevo_id}'")
            else:
                preds_list = [p.strip().upper() for p in nuevos_preds.split(',') if p.strip()]
                st.session_state.lista_tareas.append({
                    'id': nuevo_id,
                    'nombre': nuevo_nombre if nuevo_nombre else nuevo_id,
                    'dur': nueva_dur,
                    'preds': preds_list
                })
                st.rerun()

    st.divider()
    
    if st.button("🗑️ Reiniciar Datos", use_container_width=True):
        st.session_state.lista_tareas = []
        st.rerun()

    st.divider()
    st.subheader("📋 Lista de Tareas")
    
    if st.session_state.lista_tareas:
        # Estado de edición
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False

        if not st.session_state.edit_mode:
            # VISTA DE LECTURA
            tabla_tareas = []
            for t in st.session_state.lista_tareas:
                tabla_tareas.append({
                    "ID": t['id'],
                    "Nombre": t.get('nombre', t['id']),
                    f"Dur ({unidad[:3]})": t['dur'],
                    "Pred.": ", ".join(t['preds']) if t['preds'] else "—"
                })
            
            st.dataframe(tabla_tareas, use_container_width=True, hide_index=True)
            
            # Botón descargar lista
            df_lista = pd.DataFrame(tabla_tareas)
            excel_lista = generar_excel({"Lista de Tareas": df_lista})
            st.download_button(
                label="⬇️ Descargar Lista",
                data=excel_lista,
                file_name="lista_tareas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descargar lista actual en Excel",
                use_container_width=True
            )
            
            if st.button("✏️ Editar Lista Completa", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()
                
        else:
            # VISTA DE EDICIÓN
            st.info("📝 Editando tareas... Modifica y guarda.")
            
            # Preparamos datos para el editor
            df_edit = pd.DataFrame(st.session_state.lista_tareas)
            
            # Ajustamos columnas para que sean amigables
            df_edit = df_edit.rename(columns={
                'id': 'ID', 
                'nombre': 'Nombre', 
                'dur': f'Duración', 
                'preds': 'Predecesores'
            })
            
            # Convertir lista de predecesores a string para editar
            df_edit['Predecesores'] = df_edit['Predecesores'].apply(lambda x: ",".join(x))
            
            # Editor de datos
            edited_df = st.data_editor(
                df_edit, 
                use_container_width=True,
                num_rows="dynamic",
                key="editor_tareas"
            )
            
            col_save, col_cancel = st.columns(2)
            
            if col_save.button("✅ Guardar Cambios", use_container_width=True, type="primary"):
                # Reconstruir la lista de tareas desde el dataframe editado
                nueva_lista = []
                for index, row in edited_df.iterrows():
                    # Parsear predecesores
                    preds_str = str(row['Predecesores'])
                    preds_list = [p.strip().upper() for p in preds_str.split(',') if p.strip()]
                    
                    nueva_lista.append({
                        'id': str(row['ID']).upper(),
                        'nombre': str(row['Nombre']),
                        'dur': int(row['Duración']) if row['Duración'] > 0 else 1,
                        'preds': preds_list
                    })
                
                st.session_state.lista_tareas = nueva_lista
                st.session_state.edit_mode = False
                st.rerun()
                
            if col_cancel.button("❌ Descartar", use_container_width=True):
                st.session_state.edit_mode = False
                st.rerun()

# --- CUERPO PRINCIPAL ---
if st.session_state.lista_tareas:
    grafo, t_proyecto = calcular_cpm(st.session_state.lista_tareas)
    
    if grafo:
        # ---------------------------------------------------------
        # MÓDULO INTELIGENTE: ANÁLISIS DE CAPACIDAD
        # ---------------------------------------------------------
        st.subheader("📊 Diagnóstico de Ingeniería")
        
        # 1. Encontrar el Cuello de Botella (La tarea más larga)
        nodos_duracion = {n: d['duration'] for n, d in grafo.nodes(data=True)}
        cuello_botella_id = max(nodos_duracion, key=nodos_duracion.get)
        tiempo_cb = nodos_duracion[cuello_botella_id]
        nombre_cb = grafo.nodes[cuello_botella_id].get('nombre', cuello_botella_id)
        
        # 2. Cálculos de Capacidad
        capacidad_actual = tiempo_semanal / tiempo_cb
        takt_time_meta = tiempo_semanal / meta_semanal
        deficit_minutos = (tiempo_cb * meta_semanal) - tiempo_semanal
        
        # 3. Mostrar KPIs
        # 3. Mostrar KPIs
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("🔴 Cuello Botella", f"{cuello_botella_id}", f"{tiempo_cb} {unidad[:3]}")
        kpi2.metric("📈 Capacidad", f"{capacidad_actual:.2f} uds", delta=f"{capacidad_actual - meta_semanal:.2f} vs Meta")
        kpi3.metric("⏱️ Takt Time", f"{takt_time_meta:.1f} {unidad[:3]}", "Meta")
        kpi4.metric("🕐 Lead Time", f"{t_proyecto} {unidad[:3]}", "Crítico")

        # 4. Análisis de "What-If" (Escenarios)
        st.markdown("---")
        c1, c2 = st.columns([2, 1])
        
        with c1:
            if capacidad_actual < meta_semanal:
                st.error(f"⚠️ **ALERTA DE CAPACIDAD:** No puedes cumplir la meta de {meta_semanal} entregas.")
                
                minutos_totales_necesarios = tiempo_cb * meta_semanal
                turnos_extra = (minutos_totales_necesarios - tiempo_semanal) / 480
                
                st.markdown(f"""
                <div class="metric-card">
                    <b>Diagnóstico:</b> La Tarea <b>{cuello_botella_id} ({nombre_cb})</b> tarda {tiempo_cb} {unidad}. 
                    Para completar {meta_semanal} unidades, necesitas <b>{minutos_totales_necesarios} {unidad}</b> de trabajo por periodo.<br><br>
                    <b>Soluciones Recomendadas:</b>
                    <ul>
                        <li>🛑 <b>Opción A (Recursos):</b> Te faltan {int(max(0, deficit_minutos))} {unidad}. Necesitas agregar <b>{max(0, math.ceil(turnos_extra))} recursos adicionales</b> para la actividad {cuello_botella_id}.</li>
                        <li>⚡ <b>Opción B (Optimización):</b> Debes reducir el tiempo de {cuello_botella_id} a <b>menos de {int(takt_time_meta)} {unidad}</b> (Reducción del {max(0, ((tiempo_cb-takt_time_meta)/tiempo_cb)*100):.1f}%).</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                ocupacion = ((tiempo_cb * meta_semanal) / tiempo_semanal) * 100
                st.success(f"✅ **CAPACIDAD SUFICIENTE:** Tu sistema soporta la demanda. La tarea {cuello_botella_id} ({nombre_cb}) está al {ocupacion:.1f}% de ocupación.")

        with c2:
            wip_ideal = (meta_semanal / tiempo_semanal) * t_proyecto
            st.info(f"💡 **WIP Óptimo Sugerido:**\nMantén **{math.ceil(wip_ideal)} a {math.ceil(wip_ideal)+1} unidades** en proceso para lograr flujo continuo.")

        # ---------------------------------------------------------
        # VISUALIZACIÓN GRÁFICA (PERT, GANTT, WIP)
        # ---------------------------------------------------------
        st.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Diagrama PERT", "📅 Gantt Interactivo", "📈 Análisis WIP", "📋 Datos Crudos"])
        
        with tab1:
            # Selector de orientación para móviles
            col_opciones, _ = st.columns([1, 2])
            orientacion = col_opciones.selectbox(
                "Orientación del Diagrama 📱:", 
                ["Horizontal (Escritorio)", "Vertical (Móvil)"],
                index=0
            )
            
            rankdir_val = 'TB' if orientacion == "Vertical (Móvil)" else 'LR'
            
            viz = graphviz.Digraph()
            viz.attr(rankdir=rankdir_val, splines='ortho', nodesep='0.6')
            viz.attr('node', shape='record', style='filled', fontname="Arial", fontsize="10")
            
            for n, d in grafo.nodes(data=True):
                color = "#ffcccc" if d['EsCritica'] else "#f0f0f0"
                if n == cuello_botella_id:
                    color = "#ffe0b2"
                
                penwidth = "3.0" if d['EsCritica'] else "1.0"
                nombre_proceso = d.get('nombre', n)
                label = f"{{ {n}: {nombre_proceso} | {d['duration']} {unidad[:3]} }} | {{ ES: {d['ES']} | EF: {d['EF']} }} | {{ LS: {d['LS']} | LF: {d['LF']} }}"
                viz.node(n, label=label, fillcolor=color, penwidth=penwidth, color="red" if d['EsCritica'] else "black")
                
            for u, v in grafo.edges():
                is_crit = grafo.nodes[u]['EsCritica'] and grafo.nodes[v]['EsCritica']
                viz.edge(u, v, color="red" if is_crit else "gray", penwidth="2.0" if is_crit else "1.0")
                
            st.graphviz_chart(viz, use_container_width=True)
            
            # Botón de Descarga Imagen
            try:
                png_data = viz.pipe(format='png')
                st.download_button(
                    label="⬇️ Descargar Imagen (PNG)", 
                    data=png_data, 
                    file_name="diagrama_pert.png", 
                    mime="image/png"
                )
            except Exception as e:
                st.warning("⚠️ Instala [Graphviz](https://graphviz.org/download/) en tu PC para descargar imágenes PNG.")
                st.caption(f"Error técnico: {str(e)}")
            st.caption("� Nodo Naranja: Cuello de Botella (Restricción de Capacidad) | 🔴 Borde Rojo: Ruta Crítica (Restricción de Tiempo)")

        with tab2:
            gantt_data = []
            for n, d in grafo.nodes(data=True):
                nombre_completo = f"{n}: {d.get('nombre', n)}"
                gantt_data.append(dict(Tarea=nombre_completo, Inicio=d['ES'], Fin=d['EF'], Tipo="Temprano (ASAP)", Critica=d['EsCritica']))
                gantt_data.append(dict(Tarea=nombre_completo, Inicio=d['LS'], Fin=d['LF'], Tipo="Tardío (ALAP)", Critica=d['EsCritica']))
            
            df_gantt = pd.DataFrame(gantt_data)
            mode = st.radio("Modo de Planificación:", ["Temprano (ASAP)", "Tardío (ALAP)"], horizontal=True)
            df_show = df_gantt[df_gantt['Tipo'] == mode]
            
            fig = px.bar(df_show, x=df_show['Fin']-df_show['Inicio'], y='Tarea', base='Inicio', orientation='h',
                         color='Critica', color_discrete_map={True: '#ff4b4b', False: '#bdc3c7'},
                         text=df_show['Fin']-df_show['Inicio'],
                         title=f"Cronograma {mode}")
            fig.update_layout(xaxis_title=f"{unidad.capitalize()} desde el inicio", yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.subheader("🏭 Análisis de Capacidad y Nivelación (Heijunka)")
            
            wip_early, wip_late, df_tareas, tiempo = analizar_carga_wip(grafo, t_proyecto)
            
            df_wip = pd.DataFrame({
                'Tiempo': tiempo,
                'WIP (Escenario ASAP)': wip_early,
                'WIP (Escenario Nivelado/ALAP)': wip_late
            })
            
            fig_wip = px.line(df_wip, x='Tiempo', y=['WIP (Escenario ASAP)', 'WIP (Escenario Nivelado/ALAP)'],
                              title=f'Perfil de Carga de Trabajo (WIP) en el Tiempo ({unidad})',
                              labels={'value': 'Cantidad de Tareas Activas (WIP)', 'variable': 'Estrategia'})
            fig_wip.update_traces(fill='tozeroy', mode='lines')
            st.plotly_chart(fig_wip, use_container_width=True)
            
            st.info("""
            **Interpretación Ingenieril:**
            * **Línea Azul (ASAP):** Muestra picos altos al inicio. Mucho inventario en proceso, alto estrés en recursos.
            * **Línea Roja (ALAP):** Aplaza tareas con holgura. Notarás que el pico se mueve o se aplana (Heijunka).
            * **El objetivo:** Mantener la curva lo más plana posible (sin picos) para estabilizar la capacidad.
            """)

        with tab4:
            st.subheader("📊 Tabla de Resultados Detallada")
            tabla_datos = []
            for n, datos in grafo.nodes(data=True):
                tabla_datos.append({
                    "ID": n,
                    "Nombre": datos.get('nombre', n),
                    f"Duración ({unidad})": datos['duration'],
                    "ES": datos['ES'],
                    "EF": datos['EF'],
                    "LS": datos['LS'],
                    "LF": datos['LF'],
                    "Holgura": datos['Holgura'],
                    "¿Crítica?": "✅ Sí" if datos['EsCritica'] else "❌ No"
                })
            
            # Botón de Descarga Excel
            df_resultados = pd.DataFrame(tabla_datos)
            excel_bytes = generar_excel({"Resultados": df_resultados})
            
            st.download_button(
                label="📥 Descargar Tabla (Excel)",
                data=excel_bytes,
                file_name="resultados_proyecto.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.dataframe(tabla_datos, use_container_width=True)
    else:
        st.error(t_proyecto)
else:
    st.info("👈 Agrega tareas en el panel lateral para comenzar.")
