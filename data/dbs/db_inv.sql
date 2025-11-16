-- =========================
-- TABLA: Categorías
-- =========================
CREATE TABLE categorias (
    categoria_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT
);

-- =========================
-- TABLA: Productos
-- =========================
CREATE TABLE productos (
    producto_id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    categoria_id INT REFERENCES categorias(categoria_id),
    precio_unitario NUMERIC(10,2) NOT NULL,
    stock_actual INT DEFAULT 0,
    unidad_medida VARCHAR(20),
    estado BOOLEAN DEFAULT TRUE,
    -- Campos para modelos de inventario
    holding_cost NUMERIC(10,2) DEFAULT 0,
    service_level_target NUMERIC(5,2) DEFAULT 0, -- ej: 0.95
    reorder_point INT DEFAULT 0,
    order_quantity INT DEFAULT 0
);

-- =========================
-- TABLA: Proveedores
-- =========================
CREATE TABLE proveedores (
    proveedor_id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    contacto VARCHAR(100),
    telefono VARCHAR(50),
    direccion TEXT,
    ordering_cost NUMERIC(10,2) DEFAULT 0,
    average_lead_time_days INT DEFAULT 0,
    lead_time_variability NUMERIC(10,2) DEFAULT 0
);

-- =========================
-- TABLA: Compras
-- =========================
CREATE TABLE compras (
    compra_id SERIAL PRIMARY KEY,
    proveedor_id INT REFERENCES proveedores(proveedor_id),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(12,2) DEFAULT 0,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    status VARCHAR(20) DEFAULT 'pendiente' -- pendiente, recibido, cancelado
);

CREATE TABLE detalle_compras (
    detalle_id SERIAL PRIMARY KEY,
    compra_id INT REFERENCES compras(compra_id) ON DELETE CASCADE,
    producto_id INT REFERENCES productos(producto_id),
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL
);

-- =========================
-- TABLA: Ventas
-- =========================
CREATE TABLE ventas (
    venta_id SERIAL PRIMARY KEY,
    cliente_id INT, -- opcional
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(12,2) DEFAULT 0
);

CREATE TABLE detalle_ventas (
    detalle_id SERIAL PRIMARY KEY,
    venta_id INT REFERENCES ventas(venta_id) ON DELETE CASCADE,
    producto_id INT REFERENCES productos(producto_id),
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL
);

-- =========================
-- TABLA: Movimientos de Inventario
-- =========================
CREATE TABLE movimientos_inventario (
    movimiento_id SERIAL PRIMARY KEY,
    producto_id INT REFERENCES productos(producto_id),
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('entrada','salida','ajuste','perdida')),
    cantidad INT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    referencia VARCHAR(150)
);
