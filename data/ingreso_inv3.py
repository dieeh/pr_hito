import sqlite3

import pandas as pd
import streamlit as st

st.title("Cargar CSV de productos a la base de datos con previsualización")

# Conexión a SQLite
conn = sqlite3.connect("inventario.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

# --- Selección o creación de proveedor ---
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

# --- Selección de vendedor ---
st.subheader("Vendedor")

vendedores = cursor.execute(
    "SELECT vendedor_id, nombre FROM vendedores ORDER BY nombre"
).fetchall()

dict_vend = {v[1]: v[0] for v in vendedores}

vend_sel = st.selectbox("Vendedor responsable:", list(dict_vend.keys()))
vendedor_id = dict_vend[vend_sel]

# --- Subida de archivo CSV ---
uploaded_file = st.file_uploader("Selecciona un CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Vista previa del CSV original:")
    st.dataframe(df)

    # Columnas de la tabla productos (excepto producto_id)
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

    st.markdown("### Mapea las columnas del CSV a las columnas de la tabla productos")
    col_map = {}
    for col in tabla_cols:
        col_map[col] = st.selectbox(f"Columna para '{col}'", ["-"] + list(df.columns))

    # Crear DataFrame de previsualización
    pre_df = pd.DataFrame()
    for col in tabla_cols:
        csv_col = col_map[col]
        if csv_col == "-":
            pre_df[col] = None
        else:
            pre_df[col] = df[csv_col]

    st.markdown("### Previsualización de los datos que se insertarán")
    st.dataframe(pre_df)

    if st.button("Confirmar inserción"):
        # Crear compra
        cursor.execute(
            "INSERT INTO compras (proveedor_id, vendedor_id, status) VALUES (?, ?, ?)",
            (proveedor_id, vendedor_id, "completada"),
        )
        compra_id = cursor.lastrowid

        for _, row in pre_df.iterrows():
            # Insertar producto
            cursor.execute(
                f"""
                INSERT INTO productos ({", ".join(tabla_cols)})
                VALUES ({", ".join(["?"] * len(tabla_cols))})
            """,
                tuple(row),
            )
            producto_id = cursor.lastrowid

            # Registrar movimiento de inventario (entrada)
            cantidad = row["stock_actual"] if row["stock_actual"] is not None else 0
            cursor.execute(
                """
                INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, referencia)
                VALUES (?, ?, ?, ?)
            """,
                (producto_id, "entrada", cantidad, f"Compra ID {compra_id}"),
            )

            # Registrar detalle de compra
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
        conn.close()
        st.success(
            f"Productos insertados correctamente con compra ID {compra_id} registrada."
        )
