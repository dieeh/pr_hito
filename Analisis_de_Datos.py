import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from db import get_connection

textColor = "#FFFFFF"
primaryColor = "#6aff67"
backgroundColor = "#0d0d0d"
secondaryBackgroundColor = "#1d1d1d"


st.set_page_config(
    page_title="Mi App de Análisis de Datos",
    page_icon="📈",  # Un emoji o ruta a un archivo .ico
    layout="wide",  # Usa todo el ancho de la pantalla (otras opciones: 'centered')
    initial_sidebar_state="expanded",  # Muestra u oculta la barra lateral al inicio
    menu_items={
        "Get Help": "https://www.ejemplo.com/ayuda",
        "Report a bug": "https://www.ejemplo.com/reporte",
        "About": "# Esta es una app de análisis de datos. Creada con Streamlit.",
    },
)


# region --- FUNCIÓN PARA INYECTAR CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


try:
    local_css("style.css")
except FileNotFoundError:
    st.error(
        "Archivo style.css no encontrado. Crea un archivo en la raíz del proyecto."
    )
# endregion


tab1, tab2 = st.tabs(["Dashboard", "Reportes"])  # NOTE MENU DE NAVEGACION

with tab1:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.title("Hola, Nombre Apellido")
        st.text("Hoy es Lunes, 17 del noviembre de 2025")
    with col2:
        with stylable_container(key="ventasxcategoria", css_styles=""):
            st.text("Ventas por Categoria")

            datos = {
                "Categoría": ["Perros", "Gatos", "Peces", "Aves"],
                "Numero de Ventas": [10, 29, 4, 6],
            }

            df = pd.DataFrame(datos)
            fig = px.pie(
                df,
                values="Numero de Ventas",
                names="Categoría",
                hole=0.5,
                facet_col_wrap=0,
                width=700,
                height=350,
                labels=None,
                color_discrete_sequence=[
                    "#d3d3d3",
                    "#767676",
                    "#4f4f4f",
                    "#6aff67",
                    "#ffffff",
                ],
            )

            fig.update_traces(textposition="inside", textinfo="value+label")
            fig.update_layout(
                uniformtext_minsize=12, uniformtext_mode="hide", showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)
        pass

    with col3:
        with stylable_container(key="globalmetrics", css_styles=""):
            column1, column2 = st.columns(2)
            with column1:
                st.metric(label="costo", value=50)
                st.metric(label="costo", value=50)
            with column2:
                st.metric(label="costo", value=50)
                st.metric(label="costo", value=50)
            st.metric(label="Valor Total", value=200)
            pass

    col11, col12 = st.columns([2, 1])
    with col11:
        data1 = {"Categoría": ["A", "B", "C", "D", "E"], "Valor": [25, 40, 15, 30, 55]}
        df1 = pd.DataFrame(data1)

        # 2. Crear el gráfico de barras con Plotly Express
        # Plotly Express facilita la creación de gráficos comunes
        fig1 = px.bar(
            df1,
            x="Categoría",
            y="Valor",
            labels={"Categoría": "Clasificación", "Valor": "Magnitud"},
            color_discrete_sequence=[
                "#d3d3d3",
                "#767676",
                "#4f4f4f",
                "#6aff67",
                "#ffffff",
            ],  # Opcional: para colorear por categoría
            color="Categoría",
        )

        # Opcional: Personalización adicional (e.g., actualizar el diseño)
        fig1.update_layout(
            xaxis_title="Categoría de Datos",
            yaxis_title="Valor Correspondiente",
            font=dict(size=14, color="White"),
            # Ajustar el ancho de las barras (0.8 es el valor por defecto)
            bargap=0,
            showlegend=False,
        )

        # 3. Mostrar el gráfico en Streamlit
        st.plotly_chart(fig1, use_container_width=True)

    with stylable_container(key="dataTable", css_styles=""):
        st.title("Tabla Interactiva con Opciones de Filtrado 🔎")

        # 1. Crear un DataFrame de ejemplo
        data = {
            "Producto": [
                "Aspiradora",
                "Licuadora",
                "Tostadora",
                "Cafetera",
                "Microondas",
                "Horno",
                "Nevera",
                "Lavadora",
            ],
            "Precio ($)": [150.99, 45.50, 25.00, 75.75, 200.00, 350.50, 800.00, 550.00],
            "Stock": [100, 50, 150, 75, 30, 10, 5, 20],
            "Fecha_Lanzamiento": pd.to_datetime(
                [
                    "2023-01-15",
                    "2023-03-20",
                    "2024-05-10",
                    "2022-11-01",
                    "2024-02-28",
                    "2023-08-12",
                    "2022-09-01",
                    "2024-01-01",
                ]
            ),
        }

        df = pd.DataFrame(data)

        # 2. Mostrar la tabla con st.dataframe()
        st.subheader("Tabla de Inventario (Solo Visualización)")
        st.write(
            "Usa el campo de **búsqueda** y haz clic en los **encabezados de las columnas** para ordenar."
        )

        st.dataframe(
            df,
            use_container_width=True,  # Hace que la tabla ocupe todo el ancho
            # Opciones de Filtrado/Búsqueda incluidas por defecto:
            # - Campo de búsqueda global (arriba a la derecha).
            # - Iconos de ordenamiento en los encabezados.
        )

        # st.data_editor() para Edición y Filtrado

        st.subheader("Tabla Editable con Opciones de Filtrado")

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",  # Permite al usuario añadir o eliminar filas
        )

        st.write("Fila(s) y valor(es) editados por el usuario:")
        st.dataframe(edited_df)
with tab2:
    st.header("diego Weko")
