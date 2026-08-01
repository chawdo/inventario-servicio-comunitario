# Documento de Requerimientos: Sistema de Gestión de Refugios e Inventario

## 1. Visión General del Proyecto
Aplicación de escritorio para la gestión logística de refugios humanitarios, control de familias censadas, registro de solicitudes semanales de insumos, administración de inventario y exportación de reportes detallados a Excel.

---

## 2. Módulos y Reglas de Negocio

### 2.1. Módulo de Refugios, Familias e Integrantes
* **Refugios (Grupos):**
  * Permite registrar, editar y listar refugios/centros de acopio.
  * Campos: Nombre del refugio, Dirección, Responsable, Capacidad máxima.
* **Familias:**
  * Pertenecen a un refugio específico.
  * Campos: Código/Número de la familia (Ej: `FAM-001`), Nombre representativo (Ej: `Familia Pérez`).
* **Integrantes:**
  * Pertenecen a una familia.
  * Campos: Nombres, Apellidos, Edad, Sexo (`M`/`F`), Condición o necesidad especial (opcional).
  * **Regla:** El sistema debe calcular automáticamente el número de integrantes por familia y clasificarlos por rango etario (Niños, Adultos, Adultos Mayores).

### 2.2. Módulo de Inventario y Categorización
* **Categorías:**
  * Personalizables por el usuario (Ej: Alimentos, Higiene, Medicinas, Indumentaria).
* **Productos / Ítems:**
  * Campos: Nombre del producto, Categoría, Presentación/Empaque (Ej: "Saco de 24 kg"), Tamaño o peso por unidad, Unidad de medida (`kg`, `litros`, `unidades`), Stock de unidades disponibles, Precio por unidad entera, Precio por kilogramo/litro (calculado o ingresado).
* **Regla de Desglose/Conversión:**
  * El sistema debe permitir descontar del inventario tanto unidades completas (sacos/cajas) como fracciones (kilogramos o litros individuales).

### 2.3. Módulo de Solicitudes Semanales y Conexión Híbrida (Soft-Match)
* **Semanas de Control:**
  * Identificación del período (Ej: `Semana 1 - Agosto 2026`).
* **Solicitudes por Familia:**
  * Se asigna una semana y una familia. Se listan los productos requeridos con sus cantidades entregadas.
* **Lógica Híbrida de Inventario (REGLA CRÍTICA):**
  * **Caso A (Producto EXISTE en Inventario):**
    * Muestra stock actual. Al confirmar la entrega, se resta automáticamente la cantidad solicitada del stock global.
    * Se marca el registro con `en_inventario = TRUE`.
  * **Caso B (Producto NO EXISTE en Inventario):**
    * El sistema **NO bloquea la solicitud**. Permite ingresar el producto como texto libre.
    * En la interfaz se muestra la etiqueta `[No registrado en Inventario]`.
    * Se marca el registro con `en_inventario = FALSE`.

### 2.4. Módulo de Exportación a Excel
* Permite exportar un reporte filtrado por **Semana** específica y/o **Refugio**.
* **Columnas obligatorias en la hoja de Excel:**
  1. `Semana`
  2. `Refugio`
  3. `Código/Número de Familia`
  4. `Nombre de Familia`
  5. `Integrante` (Nombre y Apellido)
  6. `Edad`
  7. `Sexo`
  8. `Producto Solicitado`
  9. `Cantidad Entregada`
  10. `Unidad de Medida`
  11. `Disponibilidad en Inventario` (**Sí** / **No** según el estado de `en_inventario`).

---

## 3. Esquema de Base de Datos (SQLite)

### Tabla: `refugios`
* `id` (INTEGER, PK, Autoincrement)
* `nombre` (TEXT, NOT NULL)
* `direccion` (TEXT)
* `responsable` (TEXT)
* `capacidad_maxima` (INTEGER)
* `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

### Tabla: `familias`
* `id` (INTEGER, PK, Autoincrement)
* `refugio_id` (INTEGER, FK -> `refugios.id`, NOT NULL)
* `codigo_numero` (TEXT, NOT NULL)
* `nombre_representativo` (TEXT, NOT NULL)
* `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

### Tabla: `integrantes`
* `id` (INTEGER, PK, Autoincrement)
* `familia_id` (INTEGER, FK -> `familias.id`, NOT NULL)
* `nombres` (TEXT, NOT NULL)
* `apellidos` (TEXT, NOT NULL)
* `edad` (INTEGER, NOT NULL)
* `sexo` (TEXT CHECK(sexo IN ('M', 'F')), NOT NULL)
* `condicion_especial` (TEXT)

### Tabla: `categorias`
* `id` (INTEGER, PK, Autoincrement)
* `nombre` (TEXT, NOT NULL, UNIQUE)
* `descripcion` (TEXT)

### Tabla: `productos`
* `id` (INTEGER, PK, Autoincrement)
* `categoria_id` (INTEGER, FK -> `categorias.id`, NOT NULL)
* `nombre` (TEXT, NOT NULL)
* `empaque_unidad` (TEXT, NOT NULL) -- Ej: "Saco"
* `tamano_unidad_peso` (REAL, NOT NULL) -- Ej: 24.0
* `unidad_medida` (TEXT, NOT NULL) -- Ej: "kg"
* `stock_unidades` (REAL, NOT NULL DEFAULT 0.0)
* `precio_unidad` (REAL, NOT NULL DEFAULT 0.0)
* `precio_kilo_litro` (REAL, NOT NULL DEFAULT 0.0)
* `updated_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

### Tabla: `semanas`
* `id` (INTEGER, PK, Autoincrement)
* `nombre_semana` (TEXT, NOT NULL) -- Ej: "Semana 1"
* `fecha_inicio` (DATE, NOT NULL)
* `fecha_fin` (DATE, NOT NULL)

### Tabla: `solicitudes`
* `id` (INTEGER, PK, Autoincrement)
* `semana_id` (INTEGER, FK -> `semanas.id`, NOT NULL)
* `familia_id` (INTEGER, FK -> `familias.id`, NOT NULL)
* `fecha_solicitud` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
* `observaciones` (TEXT)

### Tabla: `detalles_solicitud`
* `id` (INTEGER, PK, Autoincrement)
* `solicitud_id` (INTEGER, FK -> `solicitudes.id`, NOT NULL)
* `producto_id` (INTEGER, FK -> `productos.id`, NULLABLE) -- NULL si no está en inventario
* `nombre_producto_manual` (TEXT, NULLABLE) -- Usado si producto_id es NULL
* `cantidad_solicitada` (REAL, NOT NULL)
* `unidad_medida_solicitada` (TEXT, NOT NULL)
* `en_inventario` (BOOLEAN, NOT NULL DEFAULT 1) -- 1 = Sí, 0 = No
* `descontado_stock` (BOOLEAN, NOT NULL DEFAULT 0)

---

## 4. Consulta SQL para la Exportación a Excel

```sql
SELECT 
    s.nombre_semana AS "Semana",
    r.nombre AS "Refugio",
    f.codigo_numero AS "Código Familia",
    f.nombre_representativo AS "Familia",
    (i.nombres || ' ' || i.apellidos) AS "Integrante",
    i.edad AS "Edad",
    i.sexo AS "Sexo",
    COALESCE(p.nombre, ds.nombre_producto_manual) AS "Producto Solicitado",
    ds.cantidad_solicitada AS "Cantidad",
    ds.unidad_medida_solicitada AS "Unidad",
    CASE 
        WHEN ds.en_inventario = 1 THEN 'Sí'
        ELSE 'No'
    END AS "Disponibilidad en Inventario"
FROM solicitudes sol
INNER JOIN semanas s ON sol.semana_id = s.id
INNER JOIN familias f ON sol.familia_id = f.id
INNER JOIN refugios r ON f.refugio_id = r.id
LEFT JOIN integrantes i ON i.familia_id = f.id
INNER JOIN detalles_solicitud ds ON ds.solicitud_id = sol.id
LEFT JOIN productos p ON ds.producto_id = p.id
WHERE s.id = :semana_id
ORDER BY f.codigo_numero, i.apellidos;
