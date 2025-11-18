import streamlit as st
from streamlit_extras.stylable_container import stylable_container
import plotly.express as px
import pandas as pd



textColor = "#FFFFFF" 
primaryColor = "#6aff67" 
backgroundColor = "#0d0d0d" 
secondaryBackgroundColor = "#1d1d1d"


st.set_page_config(
    page_title="Mi App de Análisis de Datos",
    page_icon="📈", # Un emoji o ruta a un archivo .ico
    layout="wide", # Usa todo el ancho de la pantalla (otras opciones: 'centered')
    initial_sidebar_state="expanded", # Muestra u oculta la barra lateral al inicio
    menu_items={
        'Get Help': 'https://www.ejemplo.com/ayuda',
        'Report a bug': "https://www.ejemplo.com/reporte",
        'About': "# Esta es una app de análisis de datos. Creada con Streamlit."
    }
)


# region --- FUNCIÓN PARA INYECTAR CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    local_css("style.css") 
except FileNotFoundError:
    st.error("Archivo style.css no encontrado. Crea un archivo en la raíz del proyecto.")
# endregion


tab1, tab2 = st.tabs(["Dashboard", "Reportes"]) # NOTE MENU DE NAVEGACION

with tab1:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.title('Hola, Nombre Apellido')
        st.text('Hoy es Lunes, 17 del noviembre de 2025')
    with col2:
        with stylable_container(key="ventasxcategoria", css_styles=""):
            st.text('Ventas por Categoria')

            datos = {
                'Categoría': ['Perros', 'Gatos', 'Peces', 'Aves'],
                'Numero de Ventas': [10,29,4,6]
            }

            df = pd.DataFrame(datos)
            fig = px.pie(
            df,
            values='Numero de Ventas',
            names='Categoría',
            hole=0.5,
            facet_col_wrap=0,
            width=700,
            height=350,
            labels=None,
            color_discrete_sequence=['#d3d3d3', '#767676', '#4f4f4f', '#6aff67','#ffffff']
        )

            fig.update_traces(textposition='inside', textinfo='value+label')
            fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', showlegend=False)
            
            st.plotly_chart(fig, use_container_width=True)
        pass

    with col3:
        column1, column2 = st.columns(2)
        with column1:
            st.metric(label="costo", value=50)
            st.metric(label="costo", value=50)
        with column2:
            st.metric(label="costo", value=50)
            st.metric(label="costo", value=50)
        pass

    data1 = {
        'Categoría': ['A', 'B', 'C', 'D', 'E'],
        'Valor': [25, 40, 15, 30, 55]
    }
    df1 = pd.DataFrame(data1)

    # 2. Crear el gráfico de barras con Plotly Express
    # Plotly Express facilita la creación de gráficos comunes
    fig1 = px.bar(
        df1, 
        x='Categoría', 
        y='Valor', 
        title='Gráfico de Barras Simple con Plotly',
        labels={'Categoría': 'Clasificación', 'Valor': 'Magnitud'},
        color_discrete_sequence=['#d3d3d3', '#767676', '#4f4f4f', '#6aff67','#ffffff'],  # Opcional: para colorear por categoría
        color="Categoría"
    )

    # Opcional: Personalización adicional (e.g., actualizar el diseño)
    fig1.update_layout(
        xaxis_title='Categoría de Datos',
        yaxis_title='Valor Correspondiente',
        font=dict(
            size=14,
            color="White"
        ),
        # Ajustar el ancho de las barras (0.8 es el valor por defecto)
        bargap=0,
        showlegend=False
    )


    # 3. Mostrar el gráfico en Streamlit
    st.title("📈 Demostración de Plotly y Streamlit")
    st.write("Este es un gráfico de barras interactivo generado con `plotly.express` y mostrado con `st.plotly_chart`.")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.header('diego Weko')