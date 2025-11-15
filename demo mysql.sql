PRAGMA foreign_keys = ON;

CREATE TABLE categorias (
    categoria_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT
);

CREATE TABLE productos (
    producto_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    categoria_id INTEGER,
    precio_unitario REAL NOT NULL,
    stock_actual INTEGER,
    unidad_medida TEXT,
    estado INTEGER DEFAULT 1, -- 1 = true, 0 = false
    holding_cost REAL,
    service_level_target REAL,
    reorder_point INTEGER,
    order_quantity INTEGER,
    FOREIGN KEY (categoria_id) REFERENCES categorias(categoria_id)
);

CREATE TABLE proveedores (
    proveedor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    contacto TEXT,
    telefono TEXT,
    direccion TEXT,
    ordering_cost REAL,
    average_lead_time_days INTEGER,
    lead_time_variability REAL
);

CREATE TABLE compras (
    compra_id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_id INTEGER,
    vendedor_id INTEGER,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    total REAL,
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
    FOREIGN KEY (compra_id) REFERENCES compras(compra_id),
    FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
);

CREATE TABLE ventas (
    venta_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendedor_id INTEGER,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    total REAL,
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);

CREATE TABLE detalle_ventas (
    detalle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER,
    producto_id INTEGER,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(venta_id),
    FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
);

CREATE TABLE pagos_ventas (
    pago_id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER,
    metodo_id INTEGER,
    vendedor_id INTEGER,
    monto REAL NOT NULL,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venta_id) REFERENCES ventas(venta_id),
    FOREIGN KEY (metodo_id) REFERENCES metodos_pago(metodo_id),
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);

CREATE TABLE movimientos_inventario (
    movimiento_id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER,
    tipo TEXT CHECK(tipo IN ('entrada','salida','ajuste','perdida')) NOT NULL,
    cantidad INTEGER NOT NULL,
    fecha TEXT DEFAULT CURRENT_TIMESTAMP,
    referencia TEXT,
    FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
);

CREATE TABLE vendedores (
    vendedor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    contacto TEXT
);

CREATE TABLE metodos_pago (
    metodo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
);

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

CREATE TABLE usuarios (
    usuario_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendedor_id INTEGER,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('admin','vendedor','supervisor','consulta')) NOT NULL DEFAULT 'vendedor',
    estado INTEGER DEFAULT 1,
    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);
