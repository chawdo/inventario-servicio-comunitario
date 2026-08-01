import sqlite3
from typing import List, Dict, Any, Optional
from database.schema import get_connection

class RefugioController:
    """
    Controlador para gestionar la lógica de negocio y las operaciones
    en la base de datos relacionadas con los refugios.
    """

    @staticmethod
    def obtener_todos() -> List[Dict[str, Any]]:
        """
        Obtiene todos los refugios de la base de datos.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, nombre, direccion, responsable, capacidad_maxima
                FROM refugios
                ORDER BY nombre ASC
            """)
            rows = cursor.fetchall()
            refugios = []
            for row in rows:
                refugios.append({
                    "id": row[0],
                    "nombre": row[1],
                    "direccion": row[2] or "",
                    "responsable": row[3] or "",
                    "capacidad_maxima": row[4] or 0
                })
            return refugios
        except sqlite3.Error as e:
            print(f"Error al obtener refugios: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def crear_refugio(nombre: str, direccion: str, responsable: str, capacidad_maxima: int) -> int:
        """
        Inserta un nuevo refugio en la base de datos tras validar los campos.
        """
        # Validaciones de negocio/datos
        if not nombre.strip():
            raise ValueError("El nombre del refugio no puede estar vacío.")
        if capacidad_maxima <= 0:
            raise ValueError("La capacidad máxima debe ser un número entero mayor que cero.")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO refugios (nombre, direccion, responsable, capacidad_maxima)
                VALUES (?, ?, ?, ?)
            """, (nombre.strip(), direccion.strip() or None, responsable.strip() or None, capacidad_maxima))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al registrar el refugio: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
