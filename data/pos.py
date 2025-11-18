import sqlite3
from datetime import datetime

DB_PATH = "inventario.db"


# -------------------------------------------------------
#   Función principal: registrar una venta
# -------------------------------------------------------
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
