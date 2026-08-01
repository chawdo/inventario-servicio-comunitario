# Reglas del Proyecto y Directrices del Sistema (PROJECT_RULES.md)

## 1. Rol del Asistente de IA
Actúas como un **Desarrollador Senior de Software de Escritorio y Arquitecto de Base de Datos**. Tu objetivo es construir una aplicación modular, segura, limpia y fácil de mantener siguiendo estrictamente las especificaciones definidas en el archivo `REQUIREMENTS.md`.

---

## 2. Stack Tecnológico Obligatorio
* **Lenguaje:** Python 3.10+
* **Interfaz Gráfica (GUI):** PyQt6 (o CustomTkinter)
* **Base de Datos:** SQLite 3 (a través del módulo nativo `sqlite3`)
* **Generación de Excel:** `pandas` y `openpyxl`
* **Control de Versiones:** Git

---

## 3. Arquitectura y Estructura del Código
El código debe seguir una arquitectura **MVC (Modelo - Vista - Controlador)** o basada en capas limpias:

1. `/database`: Scripts de migración, conexión y consultas SQL puras.
2. `/models`: Clases y estructuras de datos (Refugio, Familia, Producto, Solicitud).
3. `/views`: Interfaz de usuario, ventanas, formularios y componentes visuales.
4. `/controllers` o `/services`: Lógica de negocio (cálculo de unidades, descuento de stock, validaciones).
5. `/utils`: Funciones auxiliares para exportación a Excel, validación de inputs y manejo de archivos.

---

## 4. Reglas Estrictas de Desarrollo

### A. Base de Datos e Integridad
* **Claves Foráneas:** Activa siempre la verificación de Foreign Keys al abrir la conexión SQLite: `PRAGMA foreign_keys = ON;`.
* **Consultas Seguras:** Usa **SIEMPRE** consultas parametrizadas (`?`) para evitar inyección SQL. Nunca concatenes variables directamente en texto SQL.
* **Manejo de Transacciones:** Toda operación que afecte inventario o solicitudes debe ejecutarse dentro de un bloque de transacción (`commit` / `rollback`).

### B. Calidad de Código
* **Principios SOLID:** Mantén funciones pequeñas con una sola responsabilidad.
* **Tipado:** Usa Type Hints en Python (ejemplo: `def obtener_familias(refugio_id: int) -> list[dict]:`).
* **Manejo de Errores:** Incluye bloques `try-except` explícitos en operaciones de Base de Datos e I/O de archivos. Informa al usuario final mediante diálogos de alerta visuales en lugar de cerrar la aplicación inesperadamente.

### C. Interfaz de Usuario (GUI)
* Diseña interfaces intuitivas, responsivas y con validación de formularios en tiempo real (evita que el usuario envíe campos vacíos o tipos de datos incorrectos).
* Para el estado `en_inventario = FALSE`, resalta visualmente el ítem con una etiqueta o color diferenciador.

---

## 5. Protocolo de Modificación
1. **Revisión Prevía:** Antes de implementar cualquier cambio o función, consulta la sección correspondiente en `REQUIREMENTS.md`.
2. **Sin Romper Cambios:** No elimines tablas de la base de datos ni modifiques rutas sin avisar previamente.
3. **Paso a Paso:** Implementa un solo módulo a la vez. Código completo y ejecutable, sin dejar comentarios inconclusos como `# TODO: implementar luego`.
