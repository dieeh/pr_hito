import random
import sqlite3
from datetime import datetime, timedelta

# import pandas as pd

DB_PATH = "inventario.db"


def insertar_proveedores(conn, n=5):
    proveedores = []
    for i in range(n):
        proveedores.append(
            (
                f"Proveedor {i + 1}",
                f"contacto{i + 1}@mail.com",
                f"+56 9 555{i + 1}",
                "Calle falsa 123",
                round(random.uniform(20, 80), 2),  # ordering_cost
                random.randint(3, 10),  # average lead time
                round(random.uniform(0.5, 2.5), 2),  # lead time variability
            )
        )

    conn.executemany(
        """
        INSERT INTO proveedores(nombre, contacto, telefono, direccion, ordering_cost,
            average_lead_time_days, lead_time_variability)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        proveedores,
    )

    print(f"✔ {n} proveedores insertados.")
    return list(range(1, n + 1))


def insertar_categorias(conn, n=3):
    categorias = []
    for i in range(n):
        categorias.append((f"Categoría {i + 1}", f"Descripción cat {i + 1}"))

    conn.executemany(
        "INSERT INTO categorias(nombre, descripcion) VALUES (?, ?)", categorias
    )

    print(f"✔ {n} categorías insertadas.")
    return list(range(1, n + 1))


def insertar_productos(conn, proveedores, n=10):
    productos = []
    for i in range(n):
        productos.append(
            (
                f"Producto {i + 1}",
                "Descripción de prueba",
                random.randint(1, 5),  # categoría
                round(random.uniform(1000, 6000), 1),  # precio unitario
                random.randint(20, 100),  # stock inicial
                "unid",
                1,
                round(random.uniform(50, 150), 2),  # holding cost
                0.95,  # service level target
                0,
                0,
            )
        )

    conn.executemany(
        """
        INSERT INTO productos(nombre, descripcion, categoria_id, precio_unitario, stock_actual,
            unidad_medida, estado, holding_cost, service_level_target, reorder_point, order_quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        productos,
    )

    print(f"✔ {n} productos insertados.")
    return list(range(1, n + 1))


def generar_ventas(conn, productos, dias=365):
    today = datetime.now()
    start = today - timedelta(days=dias)

    ventas_ids = []

    for product_id in productos:
        fecha = start
        for _ in range(dias):
            cantidad = max(0, int(random.gauss(5, 2)))  # demanda diaria random
            if cantidad == 0:
                fecha += timedelta(days=1)
                continue

            conn.execute(
                "INSERT INTO ventas(vendedor_id, fecha, total) VALUES (?, ?, ?)",
                (None, fecha.isoformat(), cantidad * 100),
            )

            venta_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            ventas_ids.append(venta_id)

            conn.execute(
                """
                INSERT INTO detalle_ventas(venta_id, producto_id, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            """,
                (venta_id, product_id, cantidad, 100),
            )

            fecha += timedelta(days=1)

    print("✔ Ventas generadas por 1 año.")
    return ventas_ids


def generar_compras(conn, productos, proveedores, n=30):
    compras_ids = []

    for _ in range(n):
        producto = random.choice(productos)
        proveedor = random.choice(proveedores)

        fecha_ord = datetime.now() - timedelta(days=random.randint(1, 300))
        lead = random.randint(3, 12)
        fecha_entrega = fecha_ord + timedelta(days=lead)

        conn.execute(
            """
            INSERT INTO compras(proveedor_id, vendedor_id, fecha, total,
                expected_delivery_date, actual_delivery_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                proveedor,
                None,
                fecha_ord.isoformat(),
                random.randint(20000, 80000),
                fecha_entrega.isoformat(),
                fecha_entrega.isoformat(),
                "recibida",
            ),
        )

        compra_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        compras_ids.append(compra_id)

        cantidad = random.randint(20, 80)

        conn.execute(
            """
            INSERT INTO detalle_compras(compra_id, producto_id, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
        """,
            (compra_id, producto, cantidad, random.randint(50, 200)),
        )

    print("✔ Compras de prueba generadas.")
    return compras_ids


# ========================
# SCRIPT PRINCIPAL
# ========================

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    proveedores = insertar_proveedores(conn, 10)
    categorias = insertar_categorias(conn, 5)
    productos = insertar_productos(conn, proveedores, 30)
    generar_ventas(conn, productos)
    generar_compras(conn, productos, proveedores, 60)

    conn.commit()
    conn.close()

    print("\n🎉 Datos fake generados correctamente.\n")
