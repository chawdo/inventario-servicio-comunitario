import unittest
from unittest.mock import patch
import sqlite3
from controllers.refugio_controller import RefugioController
from controllers.familia_controller import FamiliaController
from database.schema import create_tables

class CustomConnection:
    """
    Un envoltorio para sqlite3.Connection que previene que close() cierre realmente la conexión
    durante el transcurso de una sola prueba de unidad.
    """
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        # No-op para mantener la conexión viva entre llamadas en el test
        pass


class TestControllers(unittest.TestCase):
    def setUp(self):
        # Base de datos en memoria
        self.real_conn = sqlite3.connect(":memory:")
        self.real_conn.execute("PRAGMA foreign_keys = ON;")
        create_tables(self.real_conn)

        self.wrapper_conn = CustomConnection(self.real_conn)

        self.patcher = patch('controllers.refugio_controller.get_connection', return_value=self.wrapper_conn)
        self.patcher_fam = patch('controllers.familia_controller.get_connection', return_value=self.wrapper_conn)
        self.patcher.start()
        self.patcher_fam.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher_fam.stop()
        self.real_conn.close()

    def test_crear_y_obtener_refugio(self):
        # Registrar un refugio válido
        ref_id = RefugioController.crear_refugio("Refugio Test", "Calle Falsa 123", "Admin", 100)
        self.assertTrue(ref_id > 0)

        # Verificar la inserción
        todos = RefugioController.obtener_todos()
        self.assertEqual(len(todos), 1)
        self.assertEqual(todos[0]["nombre"], "Refugio Test")
        self.assertEqual(todos[0]["capacidad_maxima"], 100)

    def test_crear_refugio_validaciones(self):
        # Nombre vacío
        with self.assertRaises(ValueError):
            RefugioController.crear_refugio("", "Calle Falsa 123", "Admin", 100)

        # Capacidad <= 0
        with self.assertRaises(ValueError):
            RefugioController.crear_refugio("Refugio Válido", "Calle Falsa 123", "Admin", 0)

    def test_crear_y_obtener_familia_e_integrantes(self):
        # Creamos un refugio primero
        ref_id = RefugioController.crear_refugio("Refugio Test", "Calle Falsa 123", "Admin", 100)

        # Registramos una familia
        fam_id = FamiliaController.crear_familia(ref_id, "FAM-100", "Familia de Prueba")
        self.assertTrue(fam_id > 0)

        # Obtenemos familias del refugio
        familias = FamiliaController.obtener_familias_por_refugio(ref_id)
        self.assertEqual(len(familias), 1)
        self.assertEqual(familias[0]["codigo_numero"], "FAM-100")

        # Agregamos integrantes
        int_id1 = FamiliaController.agregar_integrante(fam_id, "Pedro", "Gómez", 40, "M", "")
        int_id2 = FamiliaController.agregar_integrante(fam_id, "María", "Gómez", 12, "F", "Alergia")
        int_id3 = FamiliaController.agregar_integrante(fam_id, "Abuelo", "Gómez", 75, "M", "")

        self.assertTrue(int_id1 > 0)
        self.assertTrue(int_id2 > 0)
        self.assertTrue(int_id3 > 0)

        # Obtenemos integrantes
        integrantes = FamiliaController.obtener_integrantes_por_familia(fam_id)
        self.assertEqual(len(integrantes), 3)

        # Calculamos resumen de edades
        resumen = FamiliaController.calcular_resumen_edad(integrantes)
        self.assertEqual(resumen["total"], 3)
        self.assertEqual(resumen["ninos"], 1) # María (12)
        self.assertEqual(resumen["adultos"], 1) # Pedro (40)
        self.assertEqual(resumen["adultos_mayores"], 1) # Abuelo (75)

if __name__ == "__main__":
    unittest.main()
