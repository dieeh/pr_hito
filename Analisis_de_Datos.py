import streamlit as st

file_name = "style.css"

# DEBE ser la primera llamada de Streamlit en el script
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

# --- FUNCIÓN PARA INYECTAR CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    local_css("style.css") 
except FileNotFoundError:
    st.error("Archivo style.css no encontrado. Crea un archivo en la raíz del proyecto.")

tab1, tab2 = st.tabs(["tab1", "tab2"])

with tab1:
    st.header('Tab 1')

with tab2:
    st.header('diego Weko')