import sqlite3
from math import sqrt

import numpy as np
import pandas as pd


# ============================================================
#    Demanda diaria (media y desviación estándar)
# ============================================================
def obtener_demanda_diaria(conn: sqlite3.Connection, producto_id: int):
    query = """
    SELECT dv.cantidad, v.fecha
    FROM detalle_ventas dv
    JOIN ventas v ON v.venta_id = dv.venta_id
    WHERE dv.producto_id = ?
    ORDER BY v.fecha;
    """

    # Pyright-friendly: usar read_sql
    df = pd.read_sql(query, conn, params=[producto_id])

    if df.empty:
        return None

    df["fecha"] = pd.to_datetime(df["fecha"])

    df = df.groupby(df["fecha"].dt.date)["cantidad"].sum().reset_index()
    df["fecha"] = pd.to_datetime(df["fecha"])

    idx = pd.date_range(df["fecha"].min(), df["fecha"].max(), freq="D")
    df = (
        df.set_index("fecha")
        .reindex(idx, fill_value=0)
        .rename_axis("fecha")
        .reset_index()
    )

    mu_D = float(df["cantidad"].mean())
    sigma_D = float(df["cantidad"].std(ddof=0))

    return mu_D, sigma_D


# ============================================================
#    Obtener parámetros del producto (H, S, L)
# ============================================================
def obtener_parametros_inventario(conn: sqlite3.Connection, producto_id: int):
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

    H = df.loc[0, "H"]
    S = df.loc[0, "S"]
    L = df.loc[0, "L"]

    if H is None or S is None or L is None:
        return None

    return float(H), float(S), float(L)


# ============================================================
#    Función EOQ
# ============================================================
def calcular_eoq(conn: sqlite3.Connection, producto_id: int):
    params = obtener_parametros_inventario(conn, producto_id)
    if params is None:
        return None

    H, S, L = params

    demanda = obtener_demanda_diaria(conn, producto_id)
    if demanda is None:
        return None

    mu_D, _ = demanda
    D = mu_D * 365  # demanda anual

    EOQ = sqrt((2 * D * S) / H)

    return {"producto_id": producto_id, "D_anual": D, "S": S, "H": H, "EOQ": EOQ}


# ============================================================
#    Función ROP
# ============================================================
def calcular_rop(conn: sqlite3.Connection, producto_id: int, z_beta: float = 1.645):
    params = obtener_parametros_inventario(conn, producto_id)
    if params is None:
        return None

    H, S, L = params

    demanda = obtener_demanda_diaria(conn, producto_id)
    if demanda is None:
        return None

    mu_D, sigma_D = demanda

    R = mu_D * L + z_beta * sigma_D * sqrt(L)

    return {
        "producto_id": producto_id,
        "mu_D": mu_D,
        "sigma_D": sigma_D,
        "L": L,
        "z_beta": z_beta,
        "ROP": R,
    }
