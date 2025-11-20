from datetime import datetime, timedelta
from math import sqrt
from statistics import NormalDist

import pandas as pd
import plotly.express as px
import streamlit as st

# from numpy.random import default_rng as rng
from streamlit_extras.stylable_container import stylable_container

from db import get_connection

textColor = "#FFFFFF"
primaryColor = "#6aff67"
backgroundColor = "#0d0d0d"
secondaryBackgroundColor = "#1d1d1d"


st.set_page_config(
    page_title="Manejo de inventario",
    page_icon="📦",  # Un emoji o ruta a un archivo .ico
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

conn = get_connection()
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")


stock_total = pd.read_sql_query(
    """
    SELECT SUM(stock_actual) AS total
    FROM productos;
""",
    conn,
)["total"][0]

poco_stock = pd.read_sql_query(
    """
    SELECT COUNT(*) AS cant
    FROM productos
    WHERE stock_actual <= 10;
""",
    conn,
)["cant"][0]

mermas = pd.read_sql_query(
    """
    SELECT ABS(SUM(cantidad)) AS perdidas
    FROM movimientos_inventario
    WHERE tipo = 'perdida';
""",
    conn,
)["perdidas"][0]
if mermas is None:
    mermas = 0

fuera_stock = pd.read_sql_query(
    """
    SELECT COUNT(*) AS cant
    FROM productos
    WHERE stock_actual = 0;
""",
    conn,
)["cant"][0]

valor_inventario = pd.read_sql_query(
    """
    SELECT SUM(stock_actual * precio_unitario) AS valor
    FROM productos;
""",
    conn,
)["valor"][0]

df_q = pd.read_sql_query(
    """
    SELECT
        strftime('%Y', v.fecha) AS anio,
        'Q' || ((CAST(strftime('%m', v.fecha) AS INTEGER) - 1) / 3 + 1) AS trimestre,
        SUM(dv.cantidad * dv.precio_unitario) AS total_ventas
    FROM ventas v
    JOIN detalle_ventas dv ON dv.venta_id = v.venta_id
    GROUP BY anio, trimestre
    ORDER BY anio, trimestre;
""",
    conn,
)

# Convertir a numérico limpio
df_q["total_ventas"] = df_q["total_ventas"].astype(float)


hoy = datetime.today()
inicio_mes = hoy.replace(day=1)
inicio_mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)

# Ventas del mes actual
ventas_mes = pd.read_sql_query(
    """
    SELECT p.nombre AS producto,
           SUM(dv.cantidad) AS total,
           DATE(v.fecha) AS dia
    FROM detalle_ventas dv
    JOIN ventas v ON v.venta_id = dv.venta_id
    JOIN productos p ON p.producto_id = dv.producto_id
    WHERE DATE(v.fecha) >= DATE(?)
    GROUP BY producto, dia
    ORDER BY total DESC;
""",
    conn,
    params=[inicio_mes],
)

# Ventas del mes anterior
ventas_mes_anterior = pd.read_sql_query(
    """
    SELECT p.nombre AS producto,
           SUM(dv.cantidad) AS total
    FROM detalle_ventas dv
    JOIN ventas v ON v.venta_id = dv.venta_id
    JOIN productos p ON p.producto_id = dv.producto_id
    WHERE DATE(v.fecha) BETWEEN DATE(?) AND DATE(?)
    GROUP BY producto;
""",
    conn,
    params=[inicio_mes_anterior, inicio_mes - timedelta(days=1)],
)

top3 = (
    ventas_mes.groupby("producto")["total"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)


def obtener_productos():
    conn = get_connection()
    df = pd.read_sql("SELECT producto_id, nombre FROM productos", conn)
    return df


def obtener_demanda_diaria(producto_id):
    conn = get_connection()
    query = """
        SELECT v.fecha, dv.cantidad
        FROM detalle_ventas dv
        JOIN ventas v ON v.venta_id = dv.venta_id
        WHERE dv.producto_id = ?
        ORDER BY v.fecha;
    """
    df = pd.read_sql(query, conn, params=[producto_id])

    if df.empty:
        return None

    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.groupby(df["fecha"].dt.date)["cantidad"].sum().reset_index()
    df["fecha"] = pd.to_datetime(df["fecha"])

    # completamos días sin ventas
    idx = pd.date_range(df["fecha"].min(), df["fecha"].max(), freq="D")
    df = (
        df.set_index("fecha")
        .reindex(idx, fill_value=0)
        .rename_axis("fecha")
        .reset_index()
    )

    return df


def obtener_parametros_inventario(producto_id):
    conn = get_connection()
    query = """
        SELECT
            p.holding_cost AS H,
            pr.ordering_cost AS S,
            pr.average_lead_time_days AS L
        FROM productos p
        LEFT JOIN detalle_compras dc ON dc.producto_id = p.producto_id
        LEFT JOIN compras c ON c.compra_id = dc.compra_id
        LEFT JOIN proveedores pr ON pr.proveedor_id = c.proveedor_id
        WHERE p.producto_id = ?
        LIMIT 1;
    """
    df = pd.read_sql(query, conn, params=[producto_id])

    if df.empty:
        return None

    H, S, L = df.loc[0, ["H", "S", "L"]]

    if H is None or S is None or L is None:
        return None

    return float(H), float(S), float(L)


def calcular_eoq(mu_D, H, S):
    D_anual = mu_D * 365
    EOQ = sqrt((2 * D_anual * S) / H)
    return EOQ, D_anual


def z_from_percent(percent):
    p = percent / 100
    return NormalDist().inv_cdf(p)


def calcular_rop(mu_D, sigma_D, L, SLT=95):
    R = mu_D * L + z_from_percent(SLT) * sigma_D * sqrt(L)
    return R


with tab1:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.title("Hola, Nombre Apellido")
        st.text("Hoy es Lunes, 17 del noviembre de 2025")
    with col2:
        with stylable_container(key="ventasxcategoria", css_styles=""):
            st.text("Ventas por Categoria")

            query = """
            SELECT c.nombre AS categoria,
                   SUM(dv.cantidad) AS total_ventas
            FROM categorias c
            JOIN productos p ON p.categoria_id = c.categoria_id
            JOIN detalle_ventas dv ON dv.producto_id = p.producto_id
            GROUP BY c.categoria_id
            ORDER BY total_ventas DESC;
            """
            df = pd.read_sql_query(query, conn)

            # df = pd.DataFrame(datos)
            fig = px.pie(
                df,
                values="total_ventas",
                names="categoria",
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

            st.plotly_chart(fig, width="stretch")
        pass

    with col3:
        with stylable_container(key="globalmetrics", css_styles=""):
            column1, column2 = st.columns(2)
            with column1:
                st.metric(label="Stock Total", value=int(stock_total))
                st.metric(label="Poco Stock", value=int(poco_stock))
            with column2:
                st.metric(label="Mermas", value=int(mermas))
                st.metric(label="Fuera de Stock", value=int(fuera_stock))
            st.metric(
                label="Valor Total del Inventario",
                value="${:,.2f}".format(int(valor_inventario))
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
            )
            pass

    col11, col12 = st.columns([2, 1])
    with col11:
        data1 = {"Categoría": ["A", "B", "C", "D", "E"], "Valor": [25, 40, 15, 30, 55]}
        df1 = pd.DataFrame(data1)

        # 2. Crear el gráfico de barras con Plotly Express
        # Plotly Express facilita la creación de gráficos comunes
        fig1 = px.bar(
            df_q,
            x="trimestre",
            y="total_ventas",
            color="trimestre",
            labels={"trimestre": "Trimestre", "total_ventas": "Ventas ($)"},
            color_discrete_sequence=[
                "#d3d3d3",
                "#767676",
                "#4f4f4f",
                "#6aff67",
                "#ffffff",
            ],
        )

        # Opcional: Personalización adicional (e.g., actualizar el diseño)
        fig1.update_layout(
            title="Volumen de Ventas por Trimestre",
            xaxis_title="Trimestre",
            yaxis_title="Total Ventas ($)",
            font=dict(size=14, color="White"),
            # Ajustar el ancho de las barras (0.8 es el valor por defecto)
            bargap=0,
            showlegend=False,
        )

        # 3. Mostrar el gráfico en Streamlit
        st.plotly_chart(fig1, width="stretch")
    with col12:
        with stylable_container(key="WrapperDemandaProductos", css_styles=""):
            st.text("Productos mas demandados")
            with stylable_container(key="demandaProductos", css_styles=""):
                for i, prod in enumerate(top3):
                    # with cols[i]:

                    serie = ventas_mes[ventas_mes["producto"] == prod].sort_values(
                        "dia"
                    )
                    y = serie["total"].tolist()

                    total_mes = sum(y)

                    prev = ventas_mes_anterior.loc[
                        ventas_mes_anterior["producto"] == prod, "total"
                    ]
                    total_prev = int(prev.iloc[0]) if len(prev) else 0

                    if total_prev == 0:
                        delta = 100.0 if total_mes > 0 else 0
                    else:
                        delta = ((total_mes - total_prev) / total_prev) * 100

                    st.metric(
                        label=prod,
                        chart_data=serie.set_index("dia")["total"],
                        chart_type="area",
                        value=int(total_mes),
                        delta=f"{delta:.1f}%",
                        delta_color="inverse",
                        border=True,
                    )

                    # st.line_chart(serie.set_index("dia")["total"], height=80)

    with stylable_container(key="dataTable", css_styles=""):
        pass

with tab2:
    st.title("Reporte de Inventario")
    productos = obtener_productos()

    if productos.empty:
        st.error("No hay productos en la base de datos.")
        st.stop()

    producto_seleccionado = st.selectbox(
        "Selecciona un producto:",
        productos["nombre"],
    )

    producto_id = int(
        productos.loc[productos["nombre"] == producto_seleccionado, "producto_id"].iloc[
            0
        ]
    )

    st.subheader(f"Analizando: **{producto_seleccionado}**")

    df_demand = obtener_demanda_diaria(producto_id)

    if df_demand is None:
        st.warning("Este producto no tiene historial de ventas.")
        st.stop()

    mu_D = float(df_demand["cantidad"].mean())
    sigma_D = float(df_demand["cantidad"].std(ddof=1))

    params = obtener_parametros_inventario(producto_id)
    if params is None:
        st.error("Este producto no tiene parámetros H, S o L definidos.")
        st.stop()

    H, S, L = params

    EOQ, D_anual = calcular_eoq(mu_D, H, S)
    ROP = calcular_rop(mu_D, sigma_D, L)

    left, mid, right = st.columns(3)

    with left:
        st.metric("Demanda diaria media", f"{mu_D:.2f} unid/día")
        st.metric("Desviación estándar", f"{sigma_D:.2f}")

    with mid:
        st.metric("Lead Time (L)", f"{L} días")
        st.metric("Demanda anual (estimada)", f"{D_anual:.0f} unidades")

    with right:
        st.metric("EOQ óptimo", f"{EOQ:.0f} unidades")
        st.metric("Punto de reorden (ROP)", f"{ROP:.0f} unidades")

    st.subheader("Distribución de Demanda Diaria")

    fig_hist = px.histogram(
        df_demand,
        x="cantidad",
        nbins=20,
        title="Histograma de demanda diaria",
        labels={"cantidad": "Unidades vendidas por día"},
        opacity=0.75,
    )

    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("Serie temporal de ventas diarias")

    fig_ts = px.line(
        df_demand,
        x="fecha",
        y="cantidad",
        title="Evolución de la demanda en el tiempo",
        markers=True,
    )

    st.plotly_chart(fig_ts, use_container_width=True)

    st.subheader("Datos de demanda (crudo)")

    st.dataframe(df_demand, height=300)
