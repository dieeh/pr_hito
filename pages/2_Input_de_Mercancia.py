import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

textColor = "#FFFFFF"
primaryColor = "#6aff67"
backgroundColor = "#0d0d0d"
secondaryBackgroundColor = "#1d1d1d"


st.set_page_config(
    page_title="Mi App de Análisis de Datos",
    page_icon="📈",  # Un emoji o ruta a un archivo .ico
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


tab1, tab2 = st.tabs(["Ingreso por CSV", "Ingreso manual"])  # NOTE MENU DE NAVEGACION

conn = sqlite3.connect("./data/inventario.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")

with tab1:
    st.title("Ingreso de lote de inventario por archivo CSV")

    # --- Selección o creación de proveedor ---
    st.subheader("Proveedor")

    colC, colD = st.columns([1, 2])

    with colC:
        opt_prov = st.radio(
            label="Seleccionar proveedor:", options=["Existente", "Nuevo"], key=1
        )

    with colD:
        proveedor_id = None

        if opt_prov == "Existente":
            proveedores = cursor.execute(
                "SELECT proveedor_id, nombre FROM proveedores"
            ).fetchall()

            dict_prov = {p[1]: p[0] for p in proveedores}

            prov_sel = st.selectbox("Proveedor existente:", list(dict_prov.keys()))
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

    vend_sel = st.selectbox(
        label="Vendedor responsable:", options=list(dict_vend.keys()), key=3
    )
    vendedor_id = dict_vend[vend_sel]

    # --- Subida de archivo CSV ---
    uploaded_file = st.file_uploader("Selecciona un CSV", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Vista previa del CSV original:")
        st.dataframe(df.head(10))

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

        st.markdown(
            "### Mapea las columnas del CSV a las columnas de la tabla productos"
        )

        col_map = {}

        csv_cols = list(df.columns)
        opciones = ["-"] + csv_cols

        for i, col in enumerate(tabla_cols):
            # Mapeo automático: si la columna i existe en el CSV, usarla como default
            default_value = csv_cols[i] if i < len(csv_cols) else "-"
            default_index = opciones.index(default_value)

            col_map[col] = st.selectbox(
                f"Columna para '{col}'",
                opciones,
                index=default_index,
            )

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
with tab2:
    st.title("Ingreso manual de lote de inventario")
    st.subheader("Proveedor")

    colA, colB = st.columns([1, 2])

    with colA:
        opt_prov2 = st.radio(
            label="Seleccionar proveedor:", options=["Existente", "Nuevo"], key=2
        )

    with colB:
        proveedor_id = None

        if opt_prov2 == "Existente":
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
    st.subheader("Vendedor")

    vendedores = cursor.execute("SELECT vendedor_id, nombre FROM vendedores").fetchall()

    dict_vend = {v[1]: v[0] for v in vendedores}
    vend_sel = st.selectbox("Vendedor responsable:", list(dict_vend.keys()))
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
                    elif col in [
                        "precio_unitario",
                        "holding_cost",
                        "service_level_target",
                    ]:
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
