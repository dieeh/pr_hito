CREATE TABLE `categorias`(
    `categoria_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(100) NOT NULL,
    `descripcion` TEXT NULL
);
CREATE TABLE `productos`(
    `producto_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(150) NOT NULL,
    `descripcion` TEXT NULL,
    `categoria_id` INT NULL,
    `precio_unitario` DECIMAL(10, 2) NOT NULL,
    `stock_actual` INT NULL,
    `unidad_medida` VARCHAR(20) NULL,
    `estado` BOOLEAN NULL DEFAULT 'DEFAULT TRUE',
    `holding_cost` DECIMAL(10, 2) NULL,
    `service_level_target` DECIMAL(5, 2) NULL,
    `reorder_point` INT NULL,
    `order_quantity` INT NULL
);
CREATE TABLE `proveedores`(
    `proveedor_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(150) NOT NULL,
    `contacto` VARCHAR(100) NULL,
    `telefono` VARCHAR(50) NULL,
    `direccion` TEXT NULL,
    `ordering_cost` DECIMAL(10, 2) NULL,
    `average_lead_time_days` INT NULL,
    `lead_time_variability` DECIMAL(10, 2) NULL
);
CREATE TABLE `compras`(
    `compra_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `proveedor_id` INT NULL,
    `vendedor_id` INT NULL,
    `fecha` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(), `total` DECIMAL(12, 2) NULL, `expected_delivery_date` DATE NULL, `actual_delivery_date` DATE NULL, `status` VARCHAR(20) NULL DEFAULT 'pendiente');
CREATE TABLE `detalle_compras`(
    `detalle_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `compra_id` INT NULL,
    `producto_id` INT NULL,
    `cantidad` INT NOT NULL,
    `precio_unitario` DECIMAL(10, 2) NOT NULL
);
CREATE TABLE `ventas`(
    `venta_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `vendedor_id` INT NULL,
    `fecha` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(), `total` DECIMAL(12, 2) NULL);
CREATE TABLE `detalle_ventas`(
    `detalle_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `venta_id` INT NULL,
    `producto_id` INT NULL,
    `cantidad` INT NOT NULL,
    `precio_unitario` DECIMAL(10, 2) NOT NULL
);
CREATE TABLE `pagos_ventas`(
    `pago_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `venta_id` INT NULL,
    `metodo_id` INT NULL,
    `vendedor_id` INT NULL,
    `monto` DECIMAL(12, 2) NOT NULL,
    `fecha` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP());
CREATE TABLE `movimientos_inventario`(
    `movimiento_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `producto_id` INT NULL,
    `tipo` ENUM(
        'entrada',
        'salida',
        'ajuste',
        'perdida'
    ) NOT NULL,
    `cantidad` INT NOT NULL,
    `fecha` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(), `referencia` VARCHAR(150) NULL);
CREATE TABLE `vendedores`(
    `vendedor_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(100) NOT NULL,
    `contacto` VARCHAR(100) NULL
);
CREATE TABLE `metodos_pago`(
    `metodo_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(50) NOT NULL
);
CREATE TABLE `movimientos_caja`(
    `movimiento_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `tipo` ENUM('ingreso', 'egreso', 'ajuste') NOT NULL,
    `venta_id` INT NULL,
    `monto` DECIMAL(12, 2) NOT NULL,
    `fecha` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP(), `metodo_id` INT NULL, `vendedor_id` INT NULL);
CREATE TABLE `usuarios`(
    `usuario_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `vendedor_id` INT NULL,
    `username` VARCHAR(50) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `rol` ENUM(
        'admin',
        'vendedor',
        'supervisor',
        'consulta'
    ) NOT NULL DEFAULT 'vendedor',
    `estado` BOOLEAN NULL DEFAULT 'DEFAULT TRUE',
    `fecha_creacion` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP());
ALTER TABLE
    `usuarios` ADD UNIQUE `usuarios_username_unique`(`username`);
ALTER TABLE
    `usuarios` ADD CONSTRAINT `usuarios_vendedor_id_foreign` FOREIGN KEY(`vendedor_id`) REFERENCES `vendedores`(`vendedor_id`);
ALTER TABLE
    `pagos_ventas` ADD CONSTRAINT `pagos_ventas_venta_id_foreign` FOREIGN KEY(`venta_id`) REFERENCES `ventas`(`venta_id`);
ALTER TABLE
    `pagos_ventas` ADD CONSTRAINT `pagos_ventas_vendedor_id_foreign` FOREIGN KEY(`vendedor_id`) REFERENCES `vendedores`(`vendedor_id`);
ALTER TABLE
    `detalle_compras` ADD CONSTRAINT `detalle_compras_producto_id_foreign` FOREIGN KEY(`producto_id`) REFERENCES `productos`(`producto_id`);
ALTER TABLE
    `detalle_ventas` ADD CONSTRAINT `detalle_ventas_producto_id_foreign` FOREIGN KEY(`producto_id`) REFERENCES `productos`(`producto_id`);
ALTER TABLE
    `detalle_ventas` ADD CONSTRAINT `detalle_ventas_venta_id_foreign` FOREIGN KEY(`venta_id`) REFERENCES `ventas`(`venta_id`);
ALTER TABLE
    `compras` ADD CONSTRAINT `compras_proveedor_id_foreign` FOREIGN KEY(`proveedor_id`) REFERENCES `proveedores`(`proveedor_id`);
ALTER TABLE
    `movimientos_inventario` ADD CONSTRAINT `movimientos_inventario_producto_id_foreign` FOREIGN KEY(`producto_id`) REFERENCES `productos`(`producto_id`);
ALTER TABLE
    `movimientos_caja` ADD CONSTRAINT `movimientos_caja_vendedor_id_foreign` FOREIGN KEY(`vendedor_id`) REFERENCES `vendedores`(`vendedor_id`);
ALTER TABLE
    `ventas` ADD CONSTRAINT `ventas_vendedor_id_foreign` FOREIGN KEY(`vendedor_id`) REFERENCES `vendedores`(`vendedor_id`);
ALTER TABLE
    `detalle_compras` ADD CONSTRAINT `detalle_compras_compra_id_foreign` FOREIGN KEY(`compra_id`) REFERENCES `compras`(`compra_id`);
ALTER TABLE
    `pagos_ventas` ADD CONSTRAINT `pagos_ventas_metodo_id_foreign` FOREIGN KEY(`metodo_id`) REFERENCES `metodos_pago`(`metodo_id`);
ALTER TABLE
    `movimientos_caja` ADD CONSTRAINT `movimientos_caja_venta_id_foreign` FOREIGN KEY(`venta_id`) REFERENCES `ventas`(`venta_id`);
ALTER TABLE
    `movimientos_caja` ADD CONSTRAINT `movimientos_caja_metodo_id_foreign` FOREIGN KEY(`metodo_id`) REFERENCES `metodos_pago`(`metodo_id`);
ALTER TABLE
    `productos` ADD CONSTRAINT `productos_categoria_id_foreign` FOREIGN KEY(`categoria_id`) REFERENCES `categorias`(`categoria_id`);
ALTER TABLE
    `compras` ADD CONSTRAINT `compras_vendedor_id_foreign` FOREIGN KEY(`vendedor_id`) REFERENCES `vendedores`(`vendedor_id`);