# Sistema de gestión y análisis de inventario

Aplicación de gestión de inventario desarrollada con Python, Streamlit y SQLite. Permite registrar productos, proveedores, compras y ventas, mantener el stock actualizado y consultar indicadores para apoyar decisiones de reposición.

## Funcionalidades

- Registro y administración de productos y categorías.
- Gestión de proveedores y vendedores.
- Ingreso de mercadería mediante compras y detalle de productos.
- Registro de ventas mediante un flujo de punto de venta (POS).
- Actualización de existencias y registro de movimientos de inventario.
- Registro de pagos y movimientos de caja asociados a las ventas.
- Paneles y análisis de demanda, niveles de stock y rentabilidad.

## Análisis de inventario

El proyecto contempla métricas y modelos clásicos de gestión de inventario, entre ellos:

**Punto de reorden (ROP)**

\[
ROP = \mu_D L + z\sigma_D\sqrt{L}
\]

Estima el nivel de inventario en el que se debe emitir una reposición, considerando demanda promedio, variabilidad de la demanda y plazo de entrega.

**Cantidad económica de pedido (EOQ)**

\[
EOQ = \sqrt{\frac{2DS}{H}}
\]

Estima el tamaño de pedido que minimiza los costos relevantes de ordenar y mantener inventario, bajo los supuestos del modelo.

## Tecnologías

- Python
- Streamlit
- SQLite
- Pandas
- Plotly

## Estructura del repositorio

- `Analisis_de_Datos.py`: interfaz y análisis de datos.
- `pages/`: vistas de ingreso de mercadería y registro de ventas.
- `db.py`: conexión y acceso a la base de datos.
- `data/`: bases de datos, esquemas SQL y archivos de datos de prueba.
- `src/`: utilidades compartidas.
- `style.css` y `.streamlit/`: estilos y configuración de la aplicación.
- `requirements.txt`: archivo destinado a las dependencias del proyecto.

## Ejecución

1. Clona el repositorio:

   ```bash
   git clone https://github.com/dieeh/pr_hito.git
   cd pr_hito
   ```

2. Crea y activa un entorno virtual:

   ```bash
   python -m venv .venv
   ```

   En Windows:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   En Linux/macOS:

   ```bash
   source .venv/bin/activate
   ```

3. Instala las dependencias necesarias. El archivo `requirements.txt` está vacío en la versión actual, por lo que deben instalarse manualmente:

   ```bash
   pip install streamlit pandas plotly
   ```

4. Ejecuta la aplicación principal:

   ```bash
   streamlit run Analisis_de_Datos.py
   ```

   Algunas vistas del proyecto pueden ejecutarse directamente desde la carpeta `pages/` según el flujo que se quiera probar.

## Datos

El repositorio incluye bases de datos y esquemas SQL de prueba en `data/`. Revisa la configuración de conexión en `db.py` para confirmar qué archivo SQLite utiliza la aplicación antes de iniciar.

## Estado

Proyecto académico orientado a integrar operaciones de inventario con análisis cuantitativo para apoyar decisiones de abastecimiento y control de existencias.
