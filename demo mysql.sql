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
    estado BOOLEAN DEFAULT TRUE,
    -- Campos para modelos de inventario
    holding_cost DECIMAL(10,2) DEFAULT 0,
    service_level_target DECIMAL(5,2) DEFAULT 0, -- ej: 0.95
    reorder_point INT DEFAULT 0,
    order_quantity INT DEFAULT 0,
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
    ordering_cost DECIMAL(10,2) DEFAULT 0,
    average_lead_time_days INT DEFAULT 0,
    lead_time_variability DECIMAL(10,2) DEFAULT 0
);

-- =========================
-- TABLA: Compras
-- =========================
CREATE TABLE compras (
    compra_id INT AUTO_INCREMENT PRIMARY KEY,
    proveedor_id INT,
    vendedor_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    status VARCHAR(20) DEFAULT 'pendiente',
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(proveedor_id),
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
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
-- TABLA: Ventas
-- =========================
CREATE TABLE ventas (
    venta_id INT AUTO_INCREMENT PRIMARY KEY,
    vendedor_id INT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) DEFAULT 0,
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
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

CREATE TABLE pagos_ventas (
    pago_id INT AUTO_INCREMENT PRIMARY KEY,
    venta_id INT,
    metodo_id INT,
    vendedor_id INT,
    monto DECIMAL(12,2) NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venta_id) REFERENCES ventas(venta_id) ON DELETE CASCADE,
    FOREIGN KEY (metodo_id) REFERENCES metodos_pago(metodo_id),
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
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

-- =========================
-- TABLA: Vendedores
-- =========================
CREATE TABLE vendedores (
    vendedor_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    contacto VARCHAR(100)
);

-- =========================
-- TABLA: Métodos de Pago
-- =========================
CREATE TABLE metodos_pago (
    metodo_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL -- 'efectivo', 'tarjeta', 'transferencia', etc.
);

-- =========================
-- TABLA: Caja Movimientos
-- =========================
CREATE TABLE movimientos_caja (
    movimiento_id INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('ingreso','egreso','ajuste') NOT NULL,
    venta_id INT,
    monto DECIMAL(12,2) NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metodo_id INT,
    vendedor_id INT,
    FOREIGN KEY (venta_id) REFERENCES ventas(venta_id),
    FOREIGN KEY (metodo_id) REFERENCES metodos_pago(metodo_id),
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);

-- =========================
-- TABLA: Usuarios
-- =========================
CREATE TABLE usuarios (
    usuario_id INT AUTO_INCREMENT PRIMARY KEY,
    vendedor_id INT NULL, -- opcional: si el usuario está ligado a un vendedor
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- almacenar el hash, no el password plano
    rol ENUM('admin','vendedor','supervisor','consulta') NOT NULL DEFAULT 'vendedor',
    estado BOOLEAN DEFAULT TRUE, -- activo o inactivo
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendedor_id) REFERENCES vendedores(vendedor_id)
);
