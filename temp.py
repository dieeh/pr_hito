import sqlite3

import pandas as pd

conn = sqlite3.connect("mi_base.db")
cursor = conn.cursor()

cursor.execute("SELECT id, nombre FROM usuarios")
filas = cursor.fetchall()

for fila in filas:
    print(fila)

conn.close()

mu_D = 100
LeadT = 5
sigma_D = 10
z_beta = 2


def reorderPoint(
    meanDemand: int, leadTime: int, stdDeviationDemand: int, safetyFactor: int
):
    pass
