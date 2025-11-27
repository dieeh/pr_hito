import random
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "inventario.db"


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------


def generar_rut(i):
    num = 10000000 + i
    cuerpo = str(num)
    factores = [2, 3, 4, 5, 6, 7]
    suma, f = 0, 0

    for d in reversed(cuerpo):
        suma += int(d) * factores[f]
        f = (f + 1) % len(factores)

    resto = 11 - (suma % 11)
    dv = "0" if resto == 11 else "K" if resto == 10 else str(resto)
    return f"{cuerpo}-{dv}"


# ---------------------------------------------------
# Inserts base
# ---------------------------------------------------


def insertar_proveedores(conn, n=6):
    rows = []
    for i in range(n):
        rows.append(
            (
                f"Proveedor {i + 1}",
                generar_rut(i + 1),
                f"contacto{i + 1}@mail.com",
                f"+56 9 777{i + 1}",
                "Av. Siempre Viva 742",
                round(random.uniform(10, 50), 2),
                random.randint(2, 7),
                round(random.uniform(0.5, 2.0), 2),
            )
        )

    conn.executemany(
        """
        INSERT INTO proveedores(nombre, rut, contacto, telefono, direccion,
            ordering_cost, average_lead_time_days, lead_time_variability)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        rows,
    )

    return list(range(1, n + 1))


def insertar_categorias(conn, n=4):
    rows = [(f"Categoría {i + 1}", f"Descripción {i + 1}") for i in range(n)]
    conn.executemany("INSERT INTO categorias(nombre, descripcion) VALUES (?,?)", rows)
    return list(range(1, n + 1))


def insertar_productos(conn, categorias, n=25):
    rows = []
    for i in range(n):
        rows.append(
            (
                f"Producto {i + 1}",
                f"SKU{i + 1000}",
                "Producto de prueba",
                random.choice(categorias),
                round(random.uniform(500, 5000), 0),
                0,  # stock será actualizado luego
                "unid",
                1,
                round(random.uniform(20, 120), 2),
                0.95,
            )
        )

    conn.executemany(
        """
        INSERT INTO productos(nombre, sku, descripcion, categoria_id,
            precio_unitario, stock_actual, unidad_medida, estado,
            holding_cost, service_level_target)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        rows,
    )

    c = conn.execute("SELECT producto_id FROM productos").fetchall()
    return [x[0] for x in c]


# ---------------------------------------------------
# Compras con impacto en inventario
# ---------------------------------------------------


def generar_compras(conn, productos, proveedores, n=40):
    compras_ids = []

    for _ in range(n):
        producto = random.choice(productos)
        proveedor = random.choice(proveedores)

        fecha_compra = datetime.now() - timedelta(days=random.randint(40, 300))
        lead = random.randint(2, 10)
        fecha_entrega = fecha_compra + timedelta(days=lead)

        total = random.randint(15000, 80000)

        # Compra
        conn.execute(
            """
            INSERT INTO compras(proveedor_id, vendedor_id, fecha, total,
              expected_delivery_date, actual_delivery_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                proveedor,
                1,  # admin
                fecha_compra.isoformat(),
                total,
                fecha_entrega.isoformat(),
                fecha_entrega.isoformat(),
                "recibida",
            ),
        )

        compra_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        compras_ids.append(compra_id)

        # Item
        cantidad = random.randint(10, 80)
        precio_u = random.randint(200, 1000)

        conn.execute(
            """
            INSERT INTO detalle_compras(compra_id, producto_id, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
        """,
            (compra_id, producto, cantidad, precio_u),
        )

        # Movimiento inventario (entrada)
        conn.execute(
            """
            INSERT INTO movimientos_inventario(producto_id, tipo, cantidad, fecha, referencia)
            VALUES (?, 'entrada', ?, ?, ?)
        """,
            (producto, cantidad, fecha_entrega.isoformat(), f"COMPRA #{compra_id}"),
        )

        # Sumar al stock
        conn.execute(
            """
            UPDATE productos SET stock_actual = stock_actual + ? WHERE producto_id = ?
        """,
            (cantidad, producto),
        )

    return compras_ids


# ---------------------------------------------------
# Ventas con salida de inventario
# ---------------------------------------------------


def generar_ventas(conn, productos, dias=200):
    ventas_ids = []
    today = datetime.now()
    start = today - timedelta(days=dias)

    for day in range(dias):
        fecha = start + timedelta(days=day)
        ventas_dia = random.randint(0, 5)

        for _ in range(ventas_dia):
            conn.execute(
                """
                INSERT INTO ventas(vendedor_id, fecha, total)
                VALUES (?, ?, ?)
            """,
                (1, fecha.isoformat(), 0),
            )

            venta_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            ventas_ids.append(venta_id)

            # Se venden 1–3 items distintos
            items = random.sample(productos, k=random.randint(1, 3))
            total_venta = 0

            for p in items:
                cantidad = random.randint(1, 6)
                precio_venta = conn.execute(
                    """
                    SELECT precio_unitario FROM productos WHERE producto_id=?
                """,
                    (p,),
                ).fetchone()[0]

                total_venta += cantidad * precio_venta

                # Insert detalle
                conn.execute(
                    """
                    INSERT INTO detalle_ventas(venta_id, producto_id, cantidad, precio_unitario)
                    VALUES (?, ?, ?, ?)
                """,
                    (venta_id, p, cantidad, precio_venta),
                )

                # Movimiento inventario (salida)
                conn.execute(
                    """
                    INSERT INTO movimientos_inventario(producto_id, tipo, cantidad, fecha, referencia)
                    VALUES (?, 'salida', ?, ?, ?)
                """,
                    (p, cantidad, fecha.isoformat(), f"VENTA #{venta_id}"),
                )

                # Rebajar stock
                conn.execute(
                    """
                    UPDATE productos SET stock_actual = stock_actual - ? WHERE producto_id = ?
                """,
                    (cantidad, p),
                )

            # Actualizar total venta
            conn.execute(
                "UPDATE ventas SET total=? WHERE venta_id=?", (total_venta, venta_id)
            )

            # Generar pago (caja)
            metodo = random.choice([1, 2])
            conn.execute(
                """
                INSERT INTO pagos_ventas(venta_id, metodo_id, vendedor_id, monto)
                VALUES (?, ?, ?, ?)
            """,
                (venta_id, metodo, 1, total_venta),
            )

            conn.execute(
                """
                INSERT INTO movimientos_caja(tipo, venta_id, monto, fecha, metodo_id, vendedor_id)
                VALUES ('ingreso', ?, ?, ?, ?, ?)
            """,
                (venta_id, total_venta, fecha.isoformat(), metodo, 1),
            )

    return ventas_ids


# ---------------------------------------------------
# Main
# ---------------------------------------------------

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    print("Generando datos...")

    proveedores = insertar_proveedores(conn)
    categorias = insertar_categorias(conn)
    productos = insertar_productos(conn, categorias)

    generar_compras(conn, productos, proveedores, n=50)
    generar_ventas(conn, productos, dias=250)

    conn.commit()
    conn.close()
    print("\n✔ Datos de prueba generados con coherencia total.\n")
