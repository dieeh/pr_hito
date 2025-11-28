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
    WHERE stock_actual <= 15;
""",
    conn,
)["cant"][0]

poco_stock2 = pd.read_sql_query(
    """
    SELECT *
    FROM productos
    WHERE stock_actual <= 15;
""",
    conn,
)

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

mermas2 = pd.read_sql_query(
    """
    SELECT *
    FROM movimientos_inventario
    WHERE tipo = 'perdida';
""",
    conn,
)

fuera_stock = pd.read_sql_query(
    """
    SELECT COUNT(*) AS cant
    FROM productos
    WHERE stock_actual = 0;
""",
    conn,
)["cant"][0]

fuera_stock2 = pd.read_sql_query(
    """
    SELECT *
    FROM productos
    WHERE stock_actual = 0;
""",
    conn,
)


# --- popup: poco stock ---
@st.dialog("Productos con Poco Stock")
def popup_poco_stock():
    st.dataframe(poco_stock2[["nombre", "sku", "stock_actual"]])


# --- popup: fuera de stock ---
@st.dialog("Productos Fuera de Stock")
def popup_fuera_stock():
    st.dataframe(fuera_stock2[["nombre", "sku", "stock_actual"]])


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

    # Validación directa
    if any(x is None for x in [H, S, L]):
        return None

    return float(H), float(S), float(L)


def calcular_eoq(mu_D, H, S):
    if mu_D <= 0:
        return None, None

    D_anual = mu_D * 365  # demanda diaria → anual

    if H <= 0 or S <= 0:
        return None, D_anual

    EOQ = sqrt((2 * D_anual * S) / H)
    return EOQ, D_anual


def z_from_percent(percent):
    p = percent / 100
    return NormalDist().inv_cdf(p)


def calcular_rop(mu_D, sigma_D, L, SLT=0.95):
    if mu_D is None or L is None:
        return None

    if sigma_D is None:
        sigma_D = 0  # sin variabilidad

    z = z_from_percent(SLT * 100)
    R = mu_D * L + z * sigma_D * sqrt(L)
    return R


def reporte_mas_demandados():
    conn = get_connection()

    query = """
        SELECT p.nombre,
               dv.producto_id,
               SUM(dv.cantidad) AS total_vendido
        FROM detalle_ventas dv
        INNER JOIN productos p ON p.producto_id = dv.producto_id
        GROUP BY dv.producto_id
        ORDER BY total_vendido DESC;
    """

    df = pd.read_sql(query, conn)

    st.subheader("📈 Productos Más Demandados")
    st.dataframe(df)

    st.write("### Indicadores por producto")
    for _, row in df.iterrows():
        st.metric(
            label=row["nombre"],
            value=f"{int(row['total_vendido'])} uds",
            delta="Demanda total",
        )


def generar_reporte_stock_y_rop():
    conn = get_connection()

    productos = pd.read_sql(
        "SELECT producto_id, nombre, stock_actual FROM productos", conn
    )
    resultados = []

    for _, row in productos.iterrows():
        pid = row["producto_id"]
        nombre = row["nombre"]
        stock = row["stock_actual"]

        # Demanda histórica
        q = """
            SELECT cantidad
            FROM detalle_ventas
            WHERE producto_id = ?
        """
        d = pd.read_sql(q, conn, params=[pid])

        if d.empty:
            mu_D = 0
            sigma_D = 0
        else:
            mu_D = d["cantidad"].mean()
            sigma_D = d["cantidad"].std(ddof=1)
            if pd.isna(sigma_D):
                sigma_D = 0

        # Parámetros del inventario
        params = obtener_parametros_inventario(pid)
        if params:
            H, S, L = params
        else:
            H = S = L = None

        # Cálculo EOQ
        if H and S:
            eoq, _ = calcular_eoq(mu_D, H, S)
        else:
            eoq = None

        # Cálculo ROP
        rop = calcular_rop(mu_D, sigma_D, L) if L else None

        # Estado operativo
        if rop and stock <= rop:
            estado = "⚠️ Reposición urgente"
        elif rop and stock <= rop * 1.2:
            estado = "🔸 Cerca del ROP"
        else:
            estado = "✔ Stock OK"

        resultados.append(
            {
                "Producto": nombre,
                "Stock": stock,
                "Demanda diaria (μ)": round(mu_D, 2),
                "σ demanda": round(sigma_D, 2) if sigma_D else 0,
                "Lead Time": L,
                "ROP": round(rop, 2) if rop else None,
                "EOQ": round(eoq, 2) if eoq else None,
                "Estado": estado,
            }
        )

    return pd.DataFrame(resultados)


def reporte_stock_rop():
    st.subheader("📦 Niveles de Stock y Punto de Reorden")

    df = generar_reporte_stock_y_rop()
    st.dataframe(df)

    st.write("### Indicadores rápidos")
    for _, row in df.iterrows():
        st.metric(
            label=row["Producto"],
            value=f"Stock {row['Stock']}",
            delta=f"ROP {row['ROP']}",
        )


def reporte_rentabilidad():
    st.subheader("📈 Rentabilidad por Producto")
    conn = get_connection()

    # Traer ventas y compras
    ventas = pd.read_sql(
        """
        SELECT dv.producto_id,
               dv.cantidad,
               dv.precio_unitario AS precio_venta,
               v.fecha AS fecha_venta
        FROM detalle_ventas dv
        JOIN ventas v ON v.venta_id = dv.venta_id
    """,
        conn,
    )

    compras = pd.read_sql(
        """
        SELECT dc.producto_id,
               dc.cantidad,
               dc.precio_unitario AS precio_costo,
               c.fecha AS fecha_compra
        FROM detalle_compras dc
        JOIN compras c ON c.compra_id = dc.compra_id
    """,
        conn,
    )

    if ventas.empty:
        st.warning("No hay ventas registradas.")
        return

    # Función para calcular costo ponderado histórico de un producto hasta la fecha de venta
    def costo_ponderado(producto_id, fecha_venta):
        df = compras[
            (compras["producto_id"] == producto_id)
            & (compras["fecha_compra"] <= fecha_venta)
        ]
        if df.empty:
            return 0
        total_cantidad = df["cantidad"].sum()
        if total_cantidad == 0:
            return 0
        return (df["cantidad"] * df["precio_costo"]).sum() / total_cantidad

    # Aplicar costo ponderado a cada venta
    ventas["costo_unitario"] = ventas.apply(
        lambda row: costo_ponderado(row["producto_id"], row["fecha_venta"]), axis=1
    )

    # Calcular margen unitario y total
    ventas["margen_unitario"] = ventas["precio_venta"] - ventas["costo_unitario"]
    ventas["margen_total"] = ventas["margen_unitario"] * ventas["cantidad"]

    # Agrupar por producto
    resumen = (
        ventas.groupby("producto_id")
        .agg(
            uds_vendidas=pd.NamedAgg(column="cantidad", aggfunc="sum"),
            ingresos=pd.NamedAgg(
                column="precio_venta",
                aggfunc=lambda x: (x * ventas.loc[x.index, "cantidad"]).sum(),
            ),
            margen_total=pd.NamedAgg(column="margen_total", aggfunc="sum"),
            margen_unitario=pd.NamedAgg(column="margen_unitario", aggfunc="mean"),
        )
        .reset_index()
    )

    # Traer nombres de productos y unir
    productos_df = pd.read_sql("SELECT producto_id, nombre FROM productos", conn)
    resumen = resumen.merge(productos_df, on="producto_id", how="left")
    resumen = resumen.sort_values("margen_total", ascending=False)

    # Mostrar tabla
    st.dataframe(resumen)

    # Mini métricas TOP 5
    top5 = resumen.nlargest(5, "margen_total")
    for _, row in top5.iterrows():
        st.metric(
            label=f"{row['nombre']} (Uds: {int(row['uds_vendidas'])})",
            value=f"${row['margen_total']:,.0f}",
            delta=f"MU: ${row['margen_unitario']:,.2f}",
        )

    # Gráfico comparativo TOP 5
    st.subheader("Contribución relativa al margen total (TOP 5)")
    fig = px.pie(top5, values="margen_total", names="nombre", title="TOP 5 Productos")
    st.plotly_chart(fig, use_container_width=True)


with tab1:
    col1, col2, col3 = st.columns(3)

    with col1:
        # st.title("Hola, Nombre Apellido")
        st.title("Hola")
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
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Stock Total", int(stock_total))

                st.metric(
                    label="Poco Stock",
                    value=int(poco_stock),
                    help="Productos cuyo stock actual es menor a 15 unidades",
                )
                if st.button("Detalles de poco stock", key="btn_poco"):
                    popup_poco_stock()

            with col2:
                st.metric("Mermas", int(mermas))

                st.metric(
                    label="Fuera de Stock",
                    value=int(fuera_stock),
                    help="Productos con stock igual a 0",
                )
                if st.button("Detalles fuera de stock", key="btn_fuera"):
                    popup_fuera_stock()

            st.metric(
                label="Valor Total del Inventario",
                value="${:,.2f}".format(int(valor_inventario))
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
            )

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
            st.text("Más demandados del mes")
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

    # with stylable_container(key="dataTable", css_styles=""):
    #    pass

with tab2:
    st.title("Reportes del Sistema")

    opcion = st.selectbox(
        "Selecciona un reporte",
        [
            "Productos más demandados",
            "Stock y Punto de Reorden",
            "Rentabilidad por producto",
        ],
    )

    if opcion == "Productos más demandados":
        reporte_mas_demandados()

    elif opcion == "Stock y Punto de Reorden":
        reporte_stock_rop()

    elif opcion == "Rentabilidad por producto":
        reporte_rentabilidad()
