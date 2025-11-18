import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

# from pos import procesar_venta  # módulo que ya construimos

DB_PATH = "inventario.db"


# =====================================================
# Cargar datos base
# =====================================================


def procesar_venta(items, vendedor_id=1, metodo_pago=1):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    try:
        total = 0

        # ============================
        # 1) Validar stock
        # ============================
        for item in items:
            pid = item["producto_id"]
            cant = item["cantidad"]

            cursor.execute(
                "SELECT stock_actual, precio_unitario FROM productos WHERE producto_id = ?",
                (pid,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"Producto {pid} no existe.")

            stock_actual, precio_unitario = row

            if stock_actual < cant:
                raise ValueError(
                    f"Stock insuficiente para producto {pid}: {stock_actual} disponibles."
                )

            total += precio_unitario * cant

        # ============================
        # 2) Insertar venta
        # ============================
        cursor.execute(
            "INSERT INTO ventas (vendedor_id, fecha, total) VALUES (?, ?, ?)",
            (vendedor_id, datetime.now(), total),
        )
        venta_id = cursor.lastrowid

        # ============================
        # 3) Insertar detalles, descontar inventario
        # ============================
        for item in items:
            pid = item["producto_id"]
            cant = item["cantidad"]

            cursor.execute(
                "SELECT precio_unitario FROM productos WHERE producto_id = ?", (pid,)
            )
            precio_unitario = cursor.fetchone()[0]

            # detalle
            cursor.execute(
                """INSERT INTO detalle_ventas
                (venta_id, producto_id, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)""",
                (venta_id, pid, cant, precio_unitario),
            )

            # actualizar inventario
            cursor.execute(
                "UPDATE productos SET stock_actual = stock_actual - ? WHERE producto_id = ?",
                (cant, pid),
            )

            # ============================
            # 3b) Registrar movimiento inventario
            # ============================
            cursor.execute(
                """INSERT INTO movimientos_inventario
                (producto_id, tipo, cantidad, fecha, referencia)
                VALUES (?, 'salida', ?, datetime('now'), ?)""",
                (pid, cant, f"Venta #{venta_id}"),
            )

        # ============================
        # 4) Registrar pago
        # ============================
        cursor.execute(
            """INSERT INTO pagos_ventas
            (venta_id, metodo_id, vendedor_id, monto, fecha)
            VALUES (?, ?, ?, ?, datetime('now'))""",
            (venta_id, metodo_pago, vendedor_id, total),
        )

        # ============================
        # 5) Registrar movimiento de caja
        # ============================
        cursor.execute(
            """INSERT INTO movimientos_caja
            (tipo, venta_id, monto, fecha, metodo_id, vendedor_id)
            VALUES ('ingreso', ?, ?, datetime('now'), ?, ?)""",
            (venta_id, total, metodo_pago, vendedor_id),
        )

        conn.commit()

        return {"status": "OK", "venta_id": venta_id, "total": total}

    except Exception as e:
        conn.rollback()
        return {"status": "ERROR", "mensaje": str(e)}

    finally:
        conn.close()


def obtener_productos():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT producto_id, nombre, precio_unitario, stock_actual FROM productos", conn
    )
    conn.close()
    return df


def obtener_vendedores():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT vendedor_id, nombre FROM vendedores", conn)
    conn.close()
    return df


def obtener_metodos_pago():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT metodo_id, nombre FROM metodos_pago", conn)
    conn.close()
    return df


# =====================================================
# Streamlit UI
# =====================================================
st.set_page_config(page_title="Punto de Venta", layout="wide")
st.title("🛒 Punto de Venta (POS)")


# =======================
# Cargar maestros
# =======================
productos = obtener_productos()
vendedores = obtener_vendedores()
metodos = obtener_metodos_pago()

if productos.empty:
    st.error("❌ No hay productos cargados en la base de datos.")
    st.stop()

if vendedores.empty:
    st.error("❌ No hay vendedores registrados.")
    st.stop()

if metodos.empty:
    st.error("❌ No hay métodos de pago registrados.")
    st.stop()


# =======================
# Selectores globales
# =======================
col_v, col_m = st.columns(2)

with col_v:
    vendedor_sel = st.selectbox(
        "👤 Vendedor:", vendedores["nombre"], key="vendedor_selector"
    )
    vendedor_id = int(
        vendedores.loc[vendedores["nombre"] == vendedor_sel, "vendedor_id"].iloc[0]
    )

with col_m:
    metodo_sel = st.selectbox(
        "💳 Método de pago:", metodos["nombre"], key="metodo_selector"
    )
    metodo_id = int(metodos.loc[metodos["nombre"] == metodo_sel, "metodo_id"].iloc[0])


# =====================================================
# Carrito
# =====================================================
if "carrito" not in st.session_state:
    st.session_state.carrito = []

st.subheader("🧺 Carrito de compra")


# =====================================================
# Añadir producto
# =====================================================
st.subheader("➕ Agregar producto al carrito")

col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    prod_sel = st.selectbox("Producto", productos["nombre"])

producto = productos.loc[productos["nombre"] == prod_sel].iloc[0]

with col2:
    cantidad = st.number_input(
        "Cantidad", min_value=1, max_value=int(producto["stock_actual"]), value=1
    )

with col3:
    if st.button("Agregar"):
        st.session_state.carrito.append(
            {
                "producto_id": int(producto["producto_id"]),
                "nombre": producto["nombre"],
                "cantidad": cantidad,
                "precio_unitario": float(producto["precio_unitario"]),
                "subtotal": cantidad * float(producto["precio_unitario"]),
            }
        )
        st.success(f"{cantidad} × {producto['nombre']} agregado.")


# =====================================================
# Mostrar carrito
# =====================================================
st.subheader("🛍 Detalle del carrito")

if len(st.session_state.carrito) == 0:
    st.info("El carrito está vacío.")
    st.stop()

df_carrito = pd.DataFrame(st.session_state.carrito)
total = df_carrito["subtotal"].sum()

st.table(df_carrito)

st.metric("TOTAL A PAGAR", f"${total:,.0f}")


# =====================================================
# Botones
# =====================================================
col_a, col_b = st.columns(2)

with col_a:
    if st.button("💳 Registrar Venta"):
        items = [
            {"producto_id": row["producto_id"], "cantidad": int(row["cantidad"])}
            for _, row in df_carrito.iterrows()
        ]

        resultado = procesar_venta(items, vendedor_id, metodo_id)

        if resultado["status"] == "OK":
            st.success(
                f"Venta registrada correctamente ✔\n"
                f"ID de venta: {resultado['venta_id']}\n"
                f"Total: ${resultado['total']:,.0f}"
            )
            st.session_state.carrito = []
        else:
            st.error(f"❌ Error: {resultado['mensaje']}")


with col_b:
    if st.button("🗑 Vaciar carrito"):
        st.session_state.carrito = []
        st.info("Carrito vaciado.")
