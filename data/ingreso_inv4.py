import sqlite3

import pandas as pd
import streamlit as st

st.title("Ingreso manual de múltiples productos a la base de datos")

# Conexión a SQLite
conn = sqlite3.connect("inventario.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

# ============================================================
#   Selección o creación de proveedor
# ============================================================
st.subheader("Proveedor")

proveedor_id = None
opt_prov = st.radio("Seleccionar proveedor:", ["Existente", "Nuevo"])

if opt_prov == "Existente":
    proveedores = cursor.execute(
        "SELECT proveedor_id, nombre FROM proveedores"
    ).fetchall()
    dict_prov = {p[1]: p[0] for p in proveedores}
    prov_sel = st.selectbox("Proveedor:", list(dict_prov.keys()))
    proveedor_id = dict_prov[prov_sel]

else:
    nuevo_nombre = st.text_input("Nombre proveedor nuevo:")
    nuevo_contacto = st.text_input("Contacto:")
    nuevo_tel = st.text_input("Teléfono:")
    nueva_dir = st.text_input("Dirección:")

    if st.button("Guardar proveedor nuevo"):
        if nuevo_nombre.strip() == "":
            st.error("El nombre no puede estar vacío.")
        else:
            cursor.execute(
                """
                INSERT INTO proveedores (nombre, contacto, telefono, direccion)
                VALUES (?, ?, ?, ?)
                """,
                (nuevo_nombre.strip(), nuevo_contacto, nuevo_tel, nueva_dir),
            )
            conn.commit()

            proveedor_id = cursor.execute(
                "SELECT proveedor_id FROM proveedores WHERE nombre = ? ORDER BY proveedor_id DESC LIMIT 1",
                (nuevo_nombre.strip(),),
            ).fetchone()[0]

            st.success("Proveedor agregado.")

if proveedor_id is None:
    st.warning("Selecciona o crea un proveedor antes de continuar.")
    st.stop()

# ============================================================
#   Selección de vendedor
# ============================================================
st.subheader("Vendedor")
vendedores = cursor.execute(
    "SELECT vendedor_id, nombre FROM vendedores ORDER BY nombre"
).fetchall()
dict_vend = {v[1]: v[0] for v in vendedores}
vend_sel = st.selectbox("Vendedor responsable:", list(dict_vend.keys()))
vendedor_id = dict_vend[vend_sel]

# ============================================================
#   Formulario dinámico de N productos
# ============================================================

st.subheader("Productos de la compra")

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

# Control de la cantidad de productos a ingresar
num_productos = st.number_input(
    "¿Cuántos productos deseas ingresar?", min_value=1, max_value=50, value=1
)

productos_data = []

st.markdown("### Completa los datos de cada producto")

for i in range(num_productos):
    st.markdown(f"#### Producto #{i + 1}")
    with st.container():
        data = {}
        for col in tabla_cols:
            if col in [
                "categoria_id",
                "stock_actual",
                "reorder_point",
                "order_quantity",
            ]:
                data[col] = st.number_input(
                    f"{col}:", min_value=0, step=1, key=f"{col}_{i}"
                )
            elif col in ["precio_unitario", "holding_cost", "service_level_target"]:
                data[col] = st.number_input(
                    f"{col}:", min_value=0.0, step=0.1, key=f"{col}_{i}"
                )
            else:
                data[col] = st.text_input(f"{col}:", key=f"{col}_{i}")
        productos_data.append(data)

# ============================================================
#   Confirmación e inserción en la BD
# ============================================================

if st.button("Registrar compra con productos"):
    # Crear compra
    cursor.execute(
        "INSERT INTO compras (proveedor_id, vendedor_id, status) VALUES (?, ?, ?)",
        (proveedor_id, vendedor_id, "completada"),
    )
    compra_id = cursor.lastrowid

    for row in productos_data:
        # Insertar producto
        cursor.execute(
            f"""
            INSERT INTO productos ({", ".join(tabla_cols)})
            VALUES ({", ".join(["?"] * len(tabla_cols))})
            """,
            tuple(row.values()),
        )
        producto_id = cursor.lastrowid

        # Movimiento inventario
        cantidad = row["stock_actual"] if row["stock_actual"] is not None else 0

        cursor.execute(
            """
            INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, referencia)
            VALUES (?, ?, ?, ?)
            """,
            (producto_id, "entrada", cantidad, f"Compra ID {compra_id}"),
        )

        # Detalle compra
        precio_unitario = (
            row["precio_unitario"] if row["precio_unitario"] is not None else 0
        )

        cursor.execute(
            """
            INSERT INTO detalle_compras (compra_id, producto_id, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
            """,
            (compra_id, producto_id, cantidad, precio_unitario),
        )

    conn.commit()
    st.success(f"Compra registrada con éxito. ID compra: {compra_id}")
