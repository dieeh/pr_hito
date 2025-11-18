import sqlite3

import pandas as pd
import streamlit as st

st.title("Cargar CSV de productos a la base de datos con previsualización")

# Conexión a SQLite
conn = sqlite3.connect("inventario.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

# --- Selección o creación de proveedor ---
cursor.execute("SELECT proveedor_id, nombre FROM proveedores")
proveedores = cursor.fetchall()
proveedor_dict = {f"{p[1]} (ID {p[0]})": p[0] for p in proveedores}
proveedor_dict["Nuevo proveedor"] = "nuevo"

proveedor_seleccionado = st.selectbox(
    "Selecciona un proveedor o crea uno nuevo", list(proveedor_dict.keys())
)

if proveedor_dict[proveedor_seleccionado] == "nuevo":
    nuevo_nombre = st.text_input("Nombre del nuevo proveedor")
    nuevo_contacto = st.text_input("Contacto")
    nuevo_telefono = st.text_input("Teléfono")
    nuevo_direccion = st.text_input("Dirección")
    if st.button("Crear proveedor"):
        cursor.execute(
            """
            INSERT INTO proveedores (nombre, contacto, telefono, direccion)
            VALUES (?, ?, ?, ?)
        """,
            (nuevo_nombre, nuevo_contacto, nuevo_telefono, nuevo_direccion),
        )
        conn.commit()
        proveedor_id = cursor.lastrowid
        st.success(f"Proveedor '{nuevo_nombre}' creado con ID {proveedor_id}")
else:
    proveedor_id = proveedor_dict[proveedor_seleccionado]

# --- Selección de vendedor ---
cursor.execute("SELECT vendedor_id, nombre FROM vendedores")
vendedores = cursor.fetchall()
vendedor_dict = {f"{v[1]} (ID {v[0]})": v[0] for v in vendedores}

vendedor_seleccionado = st.selectbox(
    "Selecciona un vendedor", list(vendedor_dict.keys())
)
vendedor_id = vendedor_dict[vendedor_seleccionado]

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
