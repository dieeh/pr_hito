PRAGMA foreign_keys = ON;

-- =========================
-- TABLA: Categorías
-- =========================
CREATE TABLE categorias (
    categoria_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT
);

-- =========================
-- TABLA: Productos
-- =========================
CREATE TABLE productos (
    producto_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    categoria_id INTEGER,
    precio_unitario REAL NOT NULL,
    stock_actual INTEGER DEFAULT 0,
    unidad_medida TEXT,
    estado INTEGER DEFAULT 1,
    holding_cost REAL DEFAULT 0,
    service_level_target REAL DEFAULT 0,
    reorder_point INTEGER DEFAULT 0,
    order_quantity INTEGER DEFAULT 0,
    FOREIGN KEY (categoria_id) REFERENCES categorias(categoria_id)
);

-- =========================
-- TABLA: Proveedores
-- =========================
CREATE TABLE proveedores (
    proveedor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    contacto TEXT,
    telefono TEXT,
    direccion TEXT,
    ordering_cost REAL DEFAULT 0,
    average_lead_time_days INTEGER DEFAULT 0,
    lead_time_variability REAL DEFAULT 0
);

-- =========================
-- TABLA: Vendedores
-- =========================
CREATE TABLE vendedores (
    vendedor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    contacto TEXT
);

-- =========================
-- TABLA: Compras
-- =========================
CREATE TABLE compras (
    compra_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_id INTEGER,
    vendedor_id INTEGER,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    total REAL DEFAULT 0,
    expected_delivery_date TEXT,
    actual_delivery_date TEXT,
    status TEXT DEFAULT 'pendiente',
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(proveedor_id),
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);

CREATE TABLE detalle_compras (
    detalle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    compra_id INTEGER,
    producto_id INTEGER,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    FOREIGN KEY (compra_id) REFERENCES compras(compra_id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
);

-- =========================
-- TABLA: Ventas
-- =========================
CREATE TABLE ventas (
    venta_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendedor_id INTEGER,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    total REAL DEFAULT 0,
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);

CREATE TABLE detalle_ventas (
    detalle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER,
    producto_id INTEGER,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(venta_id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
);

CREATE TABLE pagos_ventas (
    pago_id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER,
    metodo_id INTEGER,
    vendedor_id INTEGER,
    monto REAL NOT NULL,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venta_id) REFERENCES ventas(venta_id) ON DELETE CASCADE,
    FOREIGN KEY (metodo_id) REFERENCES metodos_pago(metodo_id),
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);

-- =========================
-- TABLA: Métodos de Pago
-- =========================
CREATE TABLE metodos_pago (
    metodo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
);

-- =========================
-- TABLA: Movimientos de Inventario
-- =========================
CREATE TABLE movimientos_inventario (
    movimiento_id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER,
    tipo TEXT CHECK(tipo IN ('entrada','salida','ajuste','perdida')) NOT NULL,
    cantidad INTEGER NOT NULL,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    referencia TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
);

-- =========================
-- TABLA: Movimientos de Caja
-- =========================
CREATE TABLE movimientos_caja (
    movimiento_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT CHECK(tipo IN ('ingreso','egreso','ajuste')) NOT NULL,
    venta_id INTEGER,
    monto REAL NOT NULL,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    metodo_id INTEGER,
    vendedor_id INTEGER,
    FOREIGN KEY (venta_id) REFERENCES ventas(venta_id),
    FOREIGN KEY (metodo_id) REFERENCES metodos_pago(metodo_id),
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);

-- =========================
-- TABLA: Usuarios
-- =========================
CREATE TABLE usuarios (
    usuario_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendedor_id INTEGER,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('admin','vendedor','supervisor','consulta')) DEFAULT 'vendedor',
    estado INTEGER DEFAULT 1,
    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);
