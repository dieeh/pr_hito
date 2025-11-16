import sqlite3

SCHEMA_PATH = "schema_db.sql"  # tu archivo SQL convertido
DB_PATH = "inventario.db"  # se creará o sobreescribirá


def crear_bd():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql_script = f.read()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(sql_script)
    conn.close()

    print("✔ Base de datos creada correctamente:", DB_PATH)


if __name__ == "__main__":
    crear_bd()
