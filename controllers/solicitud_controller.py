import sqlite3
from typing import List, Dict, Any, Optional
from database.schema import get_connection

class SolicitudController:
    """
    Controlador para gestionar la lógica de negocio y operaciones en la base de datos
    relacionadas con semanas, solicitudes y detalles de solicitud.
    """

    # ==========================================
    # GESTIÓN DE SEMANAS
    # ==========================================

    @staticmethod
    def obtener_todas_semanas() -> List[Dict[str, Any]]:
        """
        Retorna todas las semanas ordenadas por id descendentemente.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, nombre_semana, fecha_inicio, fecha_fin
                FROM semanas
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()
            semanas = []
            for row in rows:
                semanas.append({
                    "id": row[0],
                    "nombre_semana": row[1],
                    "fecha_inicio": row[2],
                    "fecha_fin": row[3]
                })
            return semanas
        except sqlite3.Error as e:
            print(f"Error al obtener semanas: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def obtener_solicitudes_por_semana(semana_id: int) -> List[Dict[str, Any]]:
        """
        Retorna todas las solicitudes registradas para una semana específica.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT s.id, f.codigo_numero, f.nombre_representativo, s.fecha_solicitud, s.observaciones
                FROM solicitudes s
                INNER JOIN familias f ON s.familia_id = f.id
                WHERE s.semana_id = ?
                ORDER BY s.id DESC
            """, (semana_id,))
            rows = cursor.fetchall()
            solicitudes = []
            for row in rows:
                solicitudes.append({
                    "id": row[0],
                    "codigo_familia": row[1],
                    "nombre_familia": row[2],
                    "fecha_solicitud": row[3],
                    "observaciones": row[4] or ""
                })
            return solicitudes
        except sqlite3.Error as e:
            print(f"Error al obtener solicitudes por semana: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def obtener_detalles_solicitud(solicitud_id: int) -> List[Dict[str, Any]]:
        """
        Retorna todos los detalles de una solicitud específica.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT ds.id, p.nombre, ds.nombre_producto_manual, ds.cantidad_solicitada, ds.unidad_medida_solicitada, ds.en_inventario
                FROM detalles_solicitud ds
                LEFT JOIN productos p ON ds.producto_id = p.id
                WHERE ds.solicitud_id = ?
                ORDER BY ds.id ASC
            """, (solicitud_id,))
            rows = cursor.fetchall()
            detalles = []
            for row in rows:
                detalles.append({
                    "id": row[0],
                    "nombre_producto": row[1] or row[2],
                    "cantidad": row[3],
                    "unidad": row[4],
                    "en_inventario": bool(row[5])
                })
            return detalles
        except sqlite3.Error as e:
            print(f"Error al obtener detalles de solicitud: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def eliminar_solicitud(solicitud_id: int) -> None:
        """
        Elimina una solicitud y todos sus detalles dentro de una sola transacción,
        devolviendo el stock de los productos que correspondan (en_inventario = 1, descontado_stock = 1).
        """
        conn = get_connection()
        # Desactivamos el autocommit para manejar la transacción manualmente
        conn.isolation_level = None
        cursor = conn.cursor()

        try:
            cursor.execute("BEGIN TRANSACTION;")

            # 1. Obtener todos los detalles que correspondan a productos de inventario con stock descontado
            cursor.execute("""
                SELECT producto_id, cantidad_solicitada
                FROM detalles_solicitud
                WHERE solicitud_id = ? AND en_inventario = 1 AND descontado_stock = 1 AND producto_id IS NOT NULL
            """, (solicitud_id,))
            detalles = cursor.fetchall()

            # 2. Devolver las cantidades al stock global
            for prod_id, cantidad in detalles:
                cursor.execute("""
                    UPDATE productos
                    SET stock_unidades = stock_unidades + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (cantidad, prod_id))

            # 3. Eliminar la solicitud (detalles_solicitud se elimina por ON DELETE CASCADE)
            cursor.execute("DELETE FROM solicitudes WHERE id = ?", (solicitud_id,))

            cursor.execute("COMMIT;")
        except Exception as e:
            try:
                cursor.execute("ROLLBACK;")
            except sqlite3.Error:
                pass
            print(f"Error en transacción al eliminar solicitud: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def crear_semana(nombre_semana: str, fecha_inicio: str, fecha_fin: str) -> int:
        """
        Crea una nueva semana de control.
        """
        if not nombre_semana.strip():
            raise ValueError("El nombre de la semana no puede estar vacío.")
        if not fecha_inicio.strip():
            raise ValueError("La fecha de inicio no puede estar vacía.")
        if not fecha_fin.strip():
            raise ValueError("La fecha de fin no puede estar vacía.")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO semanas (nombre_semana, fecha_inicio, fecha_fin)
                VALUES (?, ?, ?)
            """, (nombre_semana.strip(), fecha_inicio.strip(), fecha_fin.strip()))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al crear la semana: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    # ==========================================
    # GESTIÓN DE SOLICITUDES (TRANSACCIONAL)
    # ==========================================

    @staticmethod
    def crear_solicitud_con_detalles(
        semana_id: int,
        familia_id: int,
        observaciones: str,
        items: List[Dict[str, Any]]
    ) -> int:
        """
        Registra una nueva solicitud y sus detalles de forma transaccional.
        Controla el descuento automático de inventario para productos existentes y
        valida la disponibilidad de stock suficiente.

        Cada item en 'items' debe tener el siguiente formato:
        {
            "producto_id": int o None,
            "nombre_producto_manual": str o None,
            "cantidad_solicitada": float,
            "unidad_medida_solicitada": str,
            "en_inventario": bool (True/False)
        }
        """
        if not semana_id:
            raise ValueError("Debe seleccionar una semana válida.")
        if not familia_id:
            raise ValueError("Debe seleccionar una familia válida.")
        if not items:
            raise ValueError("La solicitud debe contener al menos un producto o ítem.")

        conn = get_connection()
        # Desactivamos el autocommit para manejar la transacción manualmente
        conn.isolation_level = None
        cursor = conn.cursor()

        try:
            # Iniciar la transacción de manera explícita
            cursor.execute("BEGIN TRANSACTION;")

            # 1. Validar que la semana y familia existan
            cursor.execute("SELECT id FROM semanas WHERE id = ?", (semana_id,))
            if not cursor.fetchone():
                raise ValueError("La semana de control seleccionada no existe.")

            cursor.execute("SELECT id FROM familias WHERE id = ?", (familia_id,))
            if not cursor.fetchone():
                raise ValueError("La familia seleccionada no existe.")

            # 2. Insertar cabecera de solicitud
            cursor.execute("""
                INSERT INTO solicitudes (semana_id, familia_id, observaciones)
                VALUES (?, ?, ?)
            """, (semana_id, familia_id, observaciones.strip() or None))
            solicitud_id = cursor.lastrowid

            # 3. Insertar cada detalle de solicitud
            for item in items:
                prod_id = item.get("producto_id")
                nombre_manual = item.get("nombre_producto_manual")
                cantidad = item.get("cantidad_solicitada")
                unidad = item.get("unidad_medida_solicitada")
                en_inventario = item.get("en_inventario", True)

                if cantidad <= 0:
                    raise ValueError("La cantidad solicitada debe ser mayor que cero.")
                if not unidad.strip():
                    raise ValueError("La unidad de medida del producto solicitado es obligatoria.")

                descontado = 0

                if en_inventario:
                    if not prod_id:
                        raise ValueError("Los productos de inventario deben tener un ID válido.")

                    # Consultar stock actual del producto con bloqueo de fila o lectura directa
                    cursor.execute("""
                        SELECT nombre, stock_unidades FROM productos WHERE id = ?
                    """, (prod_id,))
                    row = cursor.fetchone()
                    if not row:
                        raise ValueError(f"El producto con ID {prod_id} no existe en el inventario.")

                    nombre_prod, stock_actual = row

                    if stock_actual < cantidad:
                        raise ValueError(
                            f"Stock insuficiente para '{nombre_prod}'. "
                            f"Disponible: {stock_actual:.2f}, Solicitado: {cantidad:.2f}"
                        )

                    # Descontar del inventario
                    nuevo_stock = stock_actual - cantidad
                    cursor.execute("""
                        UPDATE productos
                        SET stock_unidades = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (nuevo_stock, prod_id))

                    descontado = 1
                    # Asegurar que se guarda con en_inventario = 1
                    en_inventario_val = 1
                else:
                    # Producto manual/libre
                    if not nombre_manual or not nombre_manual.strip():
                        raise ValueError("El nombre del producto manual es obligatorio.")
                    prod_id = None
                    en_inventario_val = 0

                # Insertar el detalle
                cursor.execute("""
                    INSERT INTO detalles_solicitud (
                        solicitud_id, producto_id, nombre_producto_manual,
                        cantidad_solicitada, unidad_medida_solicitada,
                        en_inventario, descontado_stock
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    solicitud_id, prod_id,
                    nombre_manual.strip() if nombre_manual else None,
                    cantidad, unidad.strip(),
                    en_inventario_val, descontado
                ))

            # Confirmar transacción
            cursor.execute("COMMIT;")
            return solicitud_id

        except Exception as e:
            try:
                cursor.execute("ROLLBACK;")
            except sqlite3.Error:
                pass
            print(f"Error en transacción de guardado de solicitud: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
