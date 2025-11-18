import sqlite3
from math import sqrt
from statistics import NormalDist

# import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "inventario.db"

# =====================================================
# --- FUNCIONES DE BASE DE DATOS
# =====================================================


def obtener_productos():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT producto_id, nombre FROM productos", conn)
    conn.close()
    return df


def obtener_demanda_diaria(producto_id):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT v.fecha, dv.cantidad
        FROM detalle_ventas dv
        JOIN ventas v ON v.venta_id = dv.venta_id
        WHERE dv.producto_id = ?
        ORDER BY v.fecha;
    """
    df = pd.read_sql(query, conn, params=[producto_id])
    conn.close()

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
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()

    if df.empty:
        return None

    H, S, L = df.loc[0, ["H", "S", "L"]]

    if H is None or S is None or L is None:
        return None

    return float(H), float(S), float(L)


# =====================================================
# --- CALCULOS EOQ Y PUNTO DE REORDEN
# =====================================================


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


# =====================================================
# --- STREAMLIT DASHBOARD
# =====================================================

st.set_page_config(page_title="Dashboard de Inventario", layout="wide")

st.title("📦 Dashboard Inteligente de Inventario")

productos = obtener_productos()

if productos.empty:
    st.error("No hay productos en la base de datos.")
    st.stop()

producto_seleccionado = st.selectbox(
    "Selecciona un producto:",
    productos["nombre"],
)

producto_id = int(
    productos.loc[productos["nombre"] == producto_seleccionado, "producto_id"].iloc[0]
)

st.subheader(f"📊 Analizando: **{producto_seleccionado}**")

# ---------------------------------------------------------
# Datos de demanda
# ---------------------------------------------------------
df_demand = obtener_demanda_diaria(producto_id)

if df_demand is None:
    st.warning("Este producto no tiene historial de ventas.")
    st.stop()

mu_D = float(df_demand["cantidad"].mean())
sigma_D = float(df_demand["cantidad"].std(ddof=1))

# ---------------------------------------------------------
# Parámetros del inventario
# ---------------------------------------------------------
params = obtener_parametros_inventario(producto_id)
if params is None:
    st.error("Este producto no tiene parámetros H, S o L definidos.")
    st.stop()

H, S, L = params

# ---------------------------------------------------------
# Cálculos
# ---------------------------------------------------------
EOQ, D_anual = calcular_eoq(mu_D, H, S)
ROP = calcular_rop(mu_D, sigma_D, L)

# ---------------------------------------------------------
# Métricas en tarjetas
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# Gráfico: Histograma de demanda diaria
# ---------------------------------------------------------
st.subheader("📈 Distribución de Demanda Diaria")

fig_hist = px.histogram(
    df_demand,
    x="cantidad",
    nbins=20,
    title="Histograma de demanda diaria",
    labels={"cantidad": "Unidades vendidas por día"},
    opacity=0.75,
)

st.plotly_chart(fig_hist, use_container_width=True)

# ---------------------------------------------------------
# Serie temporal de ventas
# ---------------------------------------------------------
st.subheader("📉 Serie temporal de ventas diarias")

fig_ts = px.line(
    df_demand,
    x="fecha",
    y="cantidad",
    title="Evolución de la demanda en el tiempo",
    markers=True,
)

st.plotly_chart(fig_ts, use_container_width=True)

# ---------------------------------------------------------
# Tabla de datos crudos
# ---------------------------------------------------------
st.subheader("📄 Datos de demanda (crudo)")

st.dataframe(df_demand, height=300)
