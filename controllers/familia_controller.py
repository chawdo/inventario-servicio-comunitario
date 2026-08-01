import sqlite3
from typing import List, Dict, Any
from database.schema import get_connection

class FamiliaController:
    """
    Controlador para gestionar la lógica de negocio y las operaciones
    en la base de datos relacionadas con familias y sus integrantes.
    """

    @staticmethod
    def obtener_familias_por_refugio(refugio_id: int) -> List[Dict[str, Any]]:
        """
        Retorna las familias que pertenecen a un refugio específico.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, refugio_id, codigo_numero, nombre_representativo
                FROM familias
                WHERE refugio_id = ?
                ORDER BY codigo_numero ASC
            """, (refugio_id,))
            rows = cursor.fetchall()
            familias = []
            for row in rows:
                familias.append({
                    "id": row[0],
                    "refugio_id": row[1],
                    "codigo_numero": row[2],
                    "nombre_representativo": row[3]
                })
            return familias
        except sqlite3.Error as e:
            print(f"Error al obtener familias por refugio: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def actualizar_integrante(integrante_id: int, nombres: str, apellidos: str, edad: int, sexo: str, condicion_especial: str) -> None:
        """
        Actualiza los datos de un integrante existente.
        """
        if not nombres.strip():
            raise ValueError("Los nombres del integrante no pueden estar vacíos.")
        if not apellidos.strip():
            raise ValueError("Los apellidos del integrante no pueden estar vacíos.")
        if edad < 0:
            raise ValueError("La edad debe ser un número entero no negativo.")
        if sexo not in ('M', 'F'):
            raise ValueError("El sexo debe ser 'M' (Masculino) o 'F' (Femenino).")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE integrantes
                SET nombres = ?, apellidos = ?, edad = ?, sexo = ?, condicion_especial = ?
                WHERE id = ?
            """, (nombres.strip(), apellidos.strip(), edad, sexo, condicion_especial.strip() or None, integrante_id))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al actualizar integrante: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def eliminar_integrante(integrante_id: int) -> None:
        """
        Elimina un integrante de la familia.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM integrantes WHERE id = ?", (integrante_id,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al eliminar integrante: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def actualizar_familia(familia_id: int, codigo_numero: str, nombre_representativo: str) -> None:
        """
        Actualiza los datos de una familia existente.
        """
        if not codigo_numero.strip():
            raise ValueError("El código de la familia no puede estar vacío.")
        if not nombre_representativo.strip():
            raise ValueError("El nombre representativo de la familia no puede estar vacío.")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Validar unicidad de código_numero en el sistema excluyendo la familia actual
            cursor.execute("SELECT id FROM familias WHERE codigo_numero = ? AND id != ?", (codigo_numero.strip(), familia_id))
            if cursor.fetchone():
                raise ValueError(f"Ya existe otra familia registrada con el código '{codigo_numero}'.")

            cursor.execute("""
                UPDATE familias
                SET codigo_numero = ?, nombre_representativo = ?
                WHERE id = ?
            """, (codigo_numero.strip(), nombre_representativo.strip(), familia_id))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al actualizar familia: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def eliminar_familia(familia_id: int) -> None:
        """
        Elimina una familia y cascada sus integrantes y solicitudes asociadas.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM familias WHERE id = ?", (familia_id,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al eliminar familia: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def crear_familia(refugio_id: int, codigo_numero: str, nombre_representativo: str) -> int:
        """
        Registra una nueva familia bajo un refugio específico.
        """
        if not codigo_numero.strip():
            raise ValueError("El código de la familia no puede estar vacío.")
        if not nombre_representativo.strip():
            raise ValueError("El nombre representativo de la familia no puede estar vacío.")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Validar unicidad de código_numero en el sistema
            cursor.execute("SELECT id FROM familias WHERE codigo_numero = ?", (codigo_numero.strip(),))
            if cursor.fetchone():
                raise ValueError(f"Ya existe una familia registrada con el código '{codigo_numero}'.")

            cursor.execute("""
                INSERT INTO familias (refugio_id, codigo_numero, nombre_representativo)
                VALUES (?, ?, ?)
            """, (refugio_id, codigo_numero.strip(), nombre_representativo.strip()))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al registrar familia: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def obtener_integrantes_por_familia(familia_id: int) -> List[Dict[str, Any]]:
        """
        Retorna todos los integrantes de una familia dada.
        """
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, familia_id, nombres, apellidos, edad, sexo, condicion_especial
                FROM integrantes
                WHERE familia_id = ?
                ORDER BY id ASC
            """, (familia_id,))
            rows = cursor.fetchall()
            integrantes = []
            for row in rows:
                integrantes.append({
                    "id": row[0],
                    "familia_id": row[1],
                    "nombres": row[2],
                    "apellidos": row[3],
                    "edad": row[4],
                    "sexo": row[5],
                    "condicion_especial": row[6] or ""
                })
            return integrantes
        except sqlite3.Error as e:
            print(f"Error al obtener integrantes: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def agregar_integrante(familia_id: int, nombres: str, apellidos: str, edad: int, sexo: str, condicion_especial: str) -> int:
        """
        Registra un nuevo integrante en una familia.
        """
        if not nombres.strip():
            raise ValueError("Los nombres del integrante no pueden estar vacíos.")
        if not apellidos.strip():
            raise ValueError("Los apellidos del integrante no pueden estar vacíos.")
        if edad < 0:
            raise ValueError("La edad debe ser un número entero no negativo.")
        if sexo not in ('M', 'F'):
            raise ValueError("El sexo debe ser 'M' (Masculino) o 'F' (Femenino).")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO integrantes (familia_id, nombres, apellidos, edad, sexo, condicion_especial)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (familia_id, nombres.strip(), apellidos.strip(), edad, sexo, condicion_especial.strip() or None))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Error al agregar integrante: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def calcular_resumen_edad(integrantes: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calcula un resumen con el total de integrantes de la familia seleccionada
        y el desglose automático por rango etario:
        - Niños: edad < 18
        - Adultos: 18 <= edad < 60
        - Adultos Mayores: edad >= 60
        """
        resumen = {
            "total": len(integrantes),
            "ninos": 0,
            "adultos": 0,
            "adultos_mayores": 0
        }
        for i in integrantes:
            edad = i["edad"]
            if edad < 18:
                resumen["ninos"] += 1
            elif edad < 60:
                resumen["adultos"] += 1
            else:
                resumen["adultos_mayores"] += 1
        return resumen
