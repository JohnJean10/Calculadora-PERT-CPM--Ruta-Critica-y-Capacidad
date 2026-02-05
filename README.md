# 📊 Calculadora PERT/CPM & Simulador de Capacidad

Esta es una poderosa herramienta interactiva desarrollada en **Python** y **Streamlit** para la gestión de proyectos y análisis de procesos industriales. 

Permite calcular automáticamente la **Ruta Crítica (CPM)**, generar diagramas **PERT**, analizar la capacidad del sistema (detección de cuellos de botella) y simular nivelación de carga de trabajo (**Heijunka**).

![Demo App](https://via.placeholder.com/800x400?text=PERT+CPM+Simulator+Demo)

## 🚀 Características Principales

*   **⚡ Motor CPM Automático:** Calcula Inicio Temprano/Tardío (ES/LS), Fin Temprano/Tardío (EF/LF) y Holguras al instante.
*   **🏭 Análisis de Capacidad:**
    *   Detección automática de **Cuellos de Botella**.
    *   Cálculo de **Takt Time** y **Lead Time**.
    *   Alertas de capacidad vs meta de producción con recomendaciones de ingeniería.
*   **📈 Análisis de Nivelación (Heijunka):**
    *   Gráficos comparativos de carga de trabajo **ASAP** (Early Start) vs **ALAP** (Late Start).
    *   Diagramas de Gantt interactivos.
*   **🎨 Interfaz Intuitiva:**
    *   Editor de tabla estilo Excel para ingresar tareas masivamente.
    *   Visualización de grafos con **Graphviz** (Redes) y **Plotly** (Datos).
    *   Totalmente neutral y adaptable a cualquier industria (Software, Construcción, Manufactura).

## 🛠️ Tecnologías

*   [Streamlit](https://streamlit.io/) - Framework de UI
*   [NetworkX](https://networkx.org/) - Teoría de grafos y algoritmos CPM
*   [Graphviz](https://graphviz.org/) - Visualización de redes PERT
*   [Plotly](https://plotly.com/) - Gráficos interactivos y Gantt
*   [Pandas](https://pandas.pydata.org/) - Manejo de datos

## 📦 Instalación y Uso

1.  Clona el repositorio:
    ```bash
    git clone https://github.com/tu-usuario/process-flow-optimizer.git
    cd process-flow-optimizer
    ```

2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
    *Nota: Necesitas tener instalado Graphviz en tu sistema operativo.*

3.  Ejecuta la aplicación:
    ```bash
    streamlit run pert_app.py
    ```

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Si tienes ideas para mejorar el algoritmo de nivelación o nuevos KPIs, siéntete libre de abrir un Pull Request.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE.md](LICENSE.md) para más detalles.
