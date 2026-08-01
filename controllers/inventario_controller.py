import sqlite3
from typing import List, Dict, Any, Optional
from database.schema import get_connection

class InventarioController:
    """
    Controlador para gestionar la lógica de negocio y operaciones
    en la base de datos relacionadas con categorías y productos del inventario.
    """

    # ==========================================
    # GESTIÓN DE CATEGORÍAS
    # ==========================================

    @staticmethod
    def obtener_todas_categorias() -> List[Dict[str, Any]]:
        """
        Retorna todas las categorías ordenadas alfabéticamente por nombre.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, nombre, descripcion
                FROM categorias
                ORDER BY nombre ASC
            """)
            rows = cursor.fetchall()
            categorias = []
            for row in rows:
                categorias.append({
                    "id": row[0],
                    "nombre": row[1],
                    "descripcion": row[2] or ""
                })
            return categorias
        except sqlite3.Error as e:
            print(f"Error al obtener categorías: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def crear_categoria(nombre: str, descripcion: str) -> int:
        """
        Crea una nueva categoría de productos.
        """
        if not nombre.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío.")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Validar unicidad de nombre de categoría
            cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (nombre.strip(),))
            if cursor.fetchone():
                raise ValueError(f"Ya existe una categoría con el nombre '{nombre.strip()}'.")

            cursor.execute("""
                INSERT INTO categorias (nombre, descripcion)
                VALUES (?, ?)
            """, (nombre.strip(), descripcion.strip() or None))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al registrar la categoría: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    # ==========================================
    # GESTIÓN DE PRODUCTOS
    # ==========================================

    @staticmethod
    def obtener_todos_productos() -> List[Dict[str, Any]]:
        """
        Retorna todos los productos del inventario global con el nombre de su categoría.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT p.id, p.categoria_id, c.nombre AS categoria_nombre, p.nombre,
                       p.empaque_unidad, p.tamano_unidad_peso, p.unidad_medida,
                       p.stock_unidades, p.precio_unidad, p.precio_kilo_litro
                FROM productos p
                INNER JOIN categorias c ON p.categoria_id = c.id
                ORDER BY c.nombre ASC, p.nombre ASC
            """)
            rows = cursor.fetchall()
            productos = []
            for row in rows:
                productos.append({
                    "id": row[0],
                    "categoria_id": row[1],
                    "categoria_nombre": row[2],
                    "nombre": row[3],
                    "empaque_unidad": row[4],
                    "tamano_unidad_peso": row[5],
                    "unidad_medida": row[6],
                    "stock_unidades": row[7],
                    "precio_unidad": row[8],
                    "precio_kilo_litro": row[9]
                })
            return productos
        except sqlite3.Error as e:
            print(f"Error al obtener productos: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def crear_producto(categoria_id: int, nombre: str, empaque_unidad: str,
                        tamano_unidad_peso: float, unidad_medida: str,
                        stock_unidades: float, precio_unidad: float) -> int:
        """
        Registra un nuevo producto en el inventario global.
        Calcula automáticamente precio_kilo_litro dividiendo precio_unidad entre tamano_unidad_peso.
        """
        # Validaciones de negocio
        if not categoria_id:
            raise ValueError("Debe seleccionar una categoría válida.")
        if not nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío.")
        if not empaque_unidad.strip():
            raise ValueError("La presentación/empaque del producto no puede estar vacía.")
        if tamano_unidad_peso <= 0:
            raise ValueError("El tamaño o peso por unidad debe ser un número mayor que cero.")
        if not unidad_medida.strip():
            raise ValueError("La unidad de medida no puede estar vacía.")
        if stock_unidades < 0:
            raise ValueError("El stock de unidades disponibles no puede ser negativo.")
        if precio_unidad < 0:
            raise ValueError("El precio por unidad no puede ser negativo.")

        # Cálculo automático de precio_kilo_litro
        precio_kilo_litro = precio_unidad / tamano_unidad_peso

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Validar que la categoría exista
            cursor.execute("SELECT id FROM categorias WHERE id = ?", (categoria_id,))
            if not cursor.fetchone():
                raise ValueError("La categoría seleccionada no existe.")

            cursor.execute("""
                INSERT INTO productos (categoria_id, nombre, empaque_unidad, tamano_unidad_peso,
                                       unidad_medida, stock_unidades, precio_unidad, precio_kilo_litro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (categoria_id, nombre.strip(), empaque_unidad.strip(), tamano_unidad_peso,
                  unidad_medida.strip(), stock_unidades, precio_unidad, precio_kilo_litro))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al registrar el producto: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def actualizar_producto(producto_id: int, categoria_id: int, nombre: str, empaque_unidad: str,
                             tamano_unidad_peso: float, unidad_medida: str,
                             stock_unidades: float, precio_unidad: float) -> None:
        """
        Actualiza un producto existente en el inventario.
        Calcula automáticamente precio_kilo_litro.
        """
        # Validaciones de negocio
        if not producto_id:
            raise ValueError("ID de producto inválido.")
        if not categoria_id:
            raise ValueError("Debe seleccionar una categoría válida.")
        if not nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío.")
        if not empaque_unidad.strip():
            raise ValueError("La presentación/empaque del producto no puede estar vacía.")
        if tamano_unidad_peso <= 0:
            raise ValueError("El tamaño o peso por unidad debe ser un número mayor que cero.")
        if not unidad_medida.strip():
            raise ValueError("La unidad de medida no puede estar vacía.")
        if stock_unidades < 0:
            raise ValueError("El stock de unidades disponibles no puede ser negativo.")
        if precio_unidad < 0:
            raise ValueError("El precio por unidad no puede ser negativo.")

        # Cálculo automático de precio_kilo_litro
        precio_kilo_litro = precio_unidad / tamano_unidad_peso

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Validar que el producto exista
            cursor.execute("SELECT id FROM productos WHERE id = ?", (producto_id,))
            if not cursor.fetchone():
                raise ValueError("El producto a actualizar no existe.")

            # Validar que la categoría exista
            cursor.execute("SELECT id FROM categorias WHERE id = ?", (categoria_id,))
            if not cursor.fetchone():
                raise ValueError("La categoría seleccionada no existe.")

            cursor.execute("""
                UPDATE productos
                SET categoria_id = ?, nombre = ?, empaque_unidad = ?, tamano_unidad_peso = ?,
                    unidad_medida = ?, stock_unidades = ?, precio_unidad = ?, precio_kilo_litro = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (categoria_id, nombre.strip(), empaque_unidad.strip(), tamano_unidad_peso,
                  unidad_medida.strip(), stock_unidades, precio_unidad, precio_kilo_litro, producto_id))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al actualizar el producto: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
