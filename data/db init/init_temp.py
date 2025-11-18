import sqlite3

DB_PATH = "inventario.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

# ===========================
# 1) Crear vendedor base
# ===========================
cursor.execute("""
INSERT INTO vendedores (nombre, contacto)
SELECT 'Administrador', 'admin@local'
WHERE NOT EXISTS (
    SELECT 1 FROM vendedores WHERE nombre = 'Administrador'
);
""")

# ===========================
# 2) Crear métodos de pago base
# ===========================
cursor.execute("""
INSERT INTO metodos_pago (nombre)
SELECT 'Efectivo'
WHERE NOT EXISTS (
    SELECT 1 FROM metodos_pago WHERE nombre = 'Efectivo'
);
""")

cursor.execute("""
INSERT INTO metodos_pago (nombre)
SELECT 'Tarjeta'
WHERE NOT EXISTS (
    SELECT 1 FROM metodos_pago WHERE nombre = 'Tarjeta'
);
""")

conn.commit()
conn.close()

print("¡Listo! Vendedor y métodos de pago creados (si no existían).")
