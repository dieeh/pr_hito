-- =========================
-- TABLA: Categorías
-- =========================
CREATE TABLE categorias (
    categoria_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT
);

-- =========================
-- TABLA: Productos
-- =========================
CREATE TABLE productos (
    producto_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    categoria_id INT,
    precio_unitario DECIMAL(10,2) NOT NULL,
    stock_actual INT DEFAULT 0,
    unidad_medida VARCHAR(20),
    estado TINYINT(1) DEFAULT 1,
    -- Campos para modelos de inventario
    holding_cost DECIMAL(10,2) DEFAULT 0,       -- costo de mantener inventario por unidad
    service_level_target DECIMAL(5,2) DEFAULT 0, -- nivel de servicio deseado (ej: 0.95)
    reorder_point INT DEFAULT 0,                 -- punto de reorden R
    order_quantity INT DEFAULT 0,                -- cantidad fija Q
    FOREIGN KEY (categoria_id) REFERENCES categorias(categoria_id)
);

-- =========================
-- TABLA: Proveedores
-- =========================
CREATE TABLE proveedores (
    proveedor_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    contacto VARCHAR(100),
    telefono VARCHAR(50),
    direccion TEXT,
    ordering_cost DECIMAL(10,2) DEFAULT 0,        -- costo de emitir pedido
    average_lead_time_days INT DEFAULT 0,         -- lead time promedio
    lead_time_variability DECIMAL(10,2) DEFAULT 0 -- desviación estándar del lead time
);

-- =========================
-- TABLA: Compras (órdenes a proveedores)
-- =========================
CREATE TABLE compras (
    compra_id INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0,
    expected_delivery_date DATE,   -- fecha esperada
    actual_delivery_date DATE,     -- fecha real
    status ENUM('pendiente','recibido','cancelado') DEFAULT 'pendiente',
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(proveedor_id)
);

CREATE TABLE detalle_compras (
    detalle_id INT AUTO_INCREMENT PRIMARY KEY,
    compra_id INT,
    producto_id INT,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (compra_id) REFERENCES compras(compra_id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
);

-- =========================
-- TABLA: Ventas (demanda real)
-- =========================
CREATE TABLE ventas (
    venta_id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT, -- opcional
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0
);

CREATE TABLE detalle_ventas (
    detalle_id INT AUTO_INCREMENT PRIMARY KEY,
    venta_id INT,
    producto_id INT,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(venta_id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
);

-- =========================
-- TABLA: Movimientos de Inventario
-- =========================
CREATE TABLE movimientos_inventario (
    movimiento_id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT,
    tipo ENUM('entrada','salida','ajuste','perdida') NOT NULL,
    cantidad INT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    referencia VARCHAR(150),
    FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
);
