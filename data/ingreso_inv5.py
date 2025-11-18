import sqlite3

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ingreso manual de productos", layout="wide")

st.title("Ingreso manual de productos — Versión Mejorada")

# ===== CONEXIÓN A BD =====
conn = sqlite3.connect("inventario.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

# ============================================================
#   1. Selección o registro de proveedor
# ============================================================
st.header("Proveedor")

colA, colB = st.columns([1, 2])

with colA:
    opt_prov = st.radio("Modo:", ["Existente", "Nuevo"])

with colB:
    proveedor_id = None

    if opt_prov == "Existente":
        proveedores = cursor.execute(
            "SELECT proveedor_id, nombre FROM proveedores ORDER BY nombre"
        ).fetchall()

        dict_prov = {p[1]: p[0] for p in proveedores}

        prov_sel = st.selectbox("Proveedor existente:", list(dict_prov.keys()))
        proveedor_id = dict_prov[prov_sel]

    else:
        st.subheader("Agregar proveedor nuevo")

        nuevo_nombre = st.text_input("Nombre proveedor:")
        nuevo_contacto = st.text_input("Contacto:")
        nuevo_tel = st.text_input("Teléfono:")
        nueva_dir = st.text_input("Dirección:")

        if st.button("Guardar proveedor nuevo"):
            if not nuevo_nombre.strip():
                st.error("El nombre no puede estar vacío.")
            else:
                cursor.execute(
                    """
                    INSERT INTO proveedores (nombre, contacto, telefono, direccion)
                    VALUES (?, ?, ?, ?)
                    """,
                    (nuevo_nombre, nuevo_contacto, nuevo_tel, nueva_dir),
                )
                conn.commit()

                proveedor_id = cursor.execute(
                    """
                    SELECT proveedor_id FROM proveedores
                    WHERE nombre = ? ORDER BY proveedor_id DESC LIMIT 1
                    """,
                    (nuevo_nombre,),
                ).fetchone()[0]

                st.success("Proveedor agregado correctamente.")

if proveedor_id is None:
    st.stop()

# ============================================================
#   2. Selección de vendedor
# ============================================================
st.header("Vendedor responsable")

vendedores = cursor.execute(
    "SELECT vendedor_id, nombre FROM vendedores ORDER BY nombre"
).fetchall()

dict_vend = {v[1]: v[0] for v in vendedores}
vend_sel = st.selectbox("Vendedor:", list(dict_vend.keys()))
vendedor_id = dict_vend[vend_sel]

# ============================================================
#   3. Productos dinámicos con buen UI
# ============================================================

st.header("Productos de la compra")

tabla_cols = [
    "nombre",
    "descripcion",
    "categoria_id",
    "precio_unitario",
    "stock_actual",
    "unidad_medida",
    "estado",
    "holding_cost",
    "service_level_target",
    "reorder_point",
    "order_quantity",
]

# Estado persistente
if "productos" not in st.session_state:
    st.session_state.productos = []

# Botón para agregar producto
if st.button("➕ Agregar producto"):
    st.session_state.productos.append({col: "" for col in tabla_cols})

# Renderizar cada producto como tarjeta plegable
for i, producto in enumerate(st.session_state.productos):
    with st.expander(f"Producto #{i + 1}", expanded=True):
        cols = st.columns(3)

        for idx, col in enumerate(tabla_cols):
            col_container = cols[idx % 3]

            with col_container:
                if col in [
                    "categoria_id",
                    "stock_actual",
                    "reorder_point",
                    "order_quantity",
                ]:
                    producto[col] = st.number_input(
                        col, min_value=0, step=1, key=f"{col}_{i}"
                    )
                elif col in ["precio_unitario", "holding_cost", "service_level_target"]:
                    producto[col] = st.number_input(
                        col, min_value=0.0, step=0.1, key=f"{col}_{i}"
                    )
                else:
                    producto[col] = st.text_input(
                        col, value=producto[col], key=f"{col}_{i}"
                    )

        # Botón eliminar producto
        if st.button(f"🗑️ Eliminar producto #{i + 1}", key=f"del_{i}"):
            st.session_state.productos.pop(i)
            st.rerun()

# ============================================================
#   PREVISUALIZACIÓN DE LOS PRODUCTOS ANTES DE INSERTAR
# ============================================================

st.subheader("Previsualización de los productos a registrar")

if len(st.session_state.productos) > 0:
    preview_df = pd.DataFrame(st.session_state.productos)
    st.dataframe(preview_df, use_container_width=True)
else:
    st.info("Aún no has agregado productos.")


# ============================================================
#   4. Guardar compra
# ============================================================

if st.button("💾 Registrar compra completa"):
    if len(st.session_state.productos) == 0:
        st.error("Debes agregar al menos un producto.")
        st.stop()

    # Crear compra
    cursor.execute(
        "INSERT INTO compras (proveedor_id, vendedor_id, status) VALUES (?, ?, ?)",
        (proveedor_id, vendedor_id, "completada"),
    )
    compra_id = cursor.lastrowid

    # Insertar productos
    for row in st.session_state.productos:
        cursor.execute(
            f"""
            INSERT INTO productos ({", ".join(tabla_cols)})
            VALUES ({", ".join(["?"] * len(tabla_cols))})
            """,
            tuple(row[col] for col in tabla_cols),
        )
        producto_id = cursor.lastrowid

        # Movimiento inventario
        cantidad = row["stock_actual"] or 0
        cursor.execute(
            """
            INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, referencia)
            VALUES (?, ?, ?, ?)
            """,
            (producto_id, "entrada", cantidad, f"Compra ID {compra_id}"),
        )

        # Detalle compra
        precio = row["precio_unitario"] or 0
        cursor.execute(
            """
            INSERT INTO detalle_compras (compra_id, producto_id, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
            """,
            (compra_id, producto_id, cantidad, precio),
        )

    conn.commit()
    st.success(f"Compra registrada correctamente (ID {compra_id}).")
    st.balloons()
