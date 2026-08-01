import unittest
from unittest.mock import patch
import sqlite3
from controllers.refugio_controller import RefugioController
from controllers.familia_controller import FamiliaController
from controllers.inventario_controller import InventarioController
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
        self.patcher_inv = patch('controllers.inventario_controller.get_connection', return_value=self.wrapper_conn)
        self.patcher.start()
        self.patcher_fam.start()
        self.patcher_inv.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher_fam.stop()
        self.patcher_inv.stop()
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

    def test_gestion_categorias(self):
        # Crear categorías
        cat1_id = InventarioController.crear_categoria("Alimentos", "Comida")
        self.assertTrue(cat1_id > 0)

        cat2_id = InventarioController.crear_categoria("Higiene", "Aseo")
        self.assertTrue(cat2_id > 0)

        # Evitar duplicados
        with self.assertRaises(ValueError):
            InventarioController.crear_categoria("Alimentos", "Otra descripción")

        # Nombre vacío
        with self.assertRaises(ValueError):
            InventarioController.crear_categoria("", "")

        # Listar y verificar
        cats = InventarioController.obtener_todas_categorias()
        self.assertEqual(len(cats), 2)
        self.assertEqual(cats[0]["nombre"], "Alimentos")
        self.assertEqual(cats[1]["nombre"], "Higiene")

    def test_gestion_productos(self):
        # Crear categoría requerida
        cat_id = InventarioController.crear_categoria("Alimentos", "Comida")

        # Crear producto
        prod1_id = InventarioController.crear_producto(
            categoria_id=cat_id,
            nombre="Arroz",
            empaque_unidad="Saco",
            tamano_unidad_peso=24.0,
            unidad_medida="kg",
            stock_unidades=10.0,
            precio_unidad=24.00
        )
        self.assertTrue(prod1_id > 0)

        # Validar cálculo automático de precio por kg/litro (24.00 / 24.0 = 1.00)
        productos = InventarioController.obtener_todos_productos()
        self.assertEqual(len(productos), 1)
        self.assertEqual(productos[0]["nombre"], "Arroz")
        self.assertEqual(productos[0]["precio_kilo_litro"], 1.00)

        # Actualizar producto
        InventarioController.actualizar_producto(
            producto_id=prod1_id,
            categoria_id=cat_id,
            nombre="Arroz Extra",
            empaque_unidad="Saco",
            tamano_unidad_peso=20.0,
            unidad_medida="kg",
            stock_unidades=8.0,
            precio_unidad=30.00
        )

        # Validar actualización y nuevo precio por kg (30.00 / 20.0 = 1.50)
        productos_act = InventarioController.obtener_todos_productos()
        self.assertEqual(len(productos_act), 1)
        self.assertEqual(productos_act[0]["nombre"], "Arroz Extra")
        self.assertEqual(productos_act[0]["stock_unidades"], 8.0)
        self.assertEqual(productos_act[0]["precio_kilo_litro"], 1.50)

    def test_validaciones_productos(self):
        cat_id = InventarioController.crear_categoria("Higiene", "Aseo")

        # Categoría no existe o no es válida
        with self.assertRaises(ValueError):
            InventarioController.crear_producto(0, "A", "B", 1.0, "kg", 1.0, 1.0)

        # Nombre vacío
        with self.assertRaises(ValueError):
            InventarioController.crear_producto(cat_id, "", "B", 1.0, "kg", 1.0, 1.0)

        # Empaque vacío
        with self.assertRaises(ValueError):
            InventarioController.crear_producto(cat_id, "A", "", 1.0, "kg", 1.0, 1.0)

        # Tamaño unidad <= 0
        with self.assertRaises(ValueError):
            InventarioController.crear_producto(cat_id, "A", "B", 0.0, "kg", 1.0, 1.0)

        # Stock < 0
        with self.assertRaises(ValueError):
            InventarioController.crear_producto(cat_id, "A", "B", 1.0, "kg", -1.0, 1.0)

        # Precio < 0
        with self.assertRaises(ValueError):
            InventarioController.crear_producto(cat_id, "A", "B", 1.0, "kg", 1.0, -1.0)

if __name__ == "__main__":
    unittest.main()
