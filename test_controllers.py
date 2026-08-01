import unittest
from unittest.mock import patch
import sqlite3
from controllers.refugio_controller import RefugioController
from controllers.familia_controller import FamiliaController
from controllers.inventario_controller import InventarioController
from controllers.solicitud_controller import SolicitudController
from controllers.reporte_controller import ReporteController
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
        self.patcher_sol = patch('controllers.solicitud_controller.get_connection', return_value=self.wrapper_conn)
        self.patcher_rep = patch('controllers.reporte_controller.get_connection', return_value=self.wrapper_conn)
        self.patcher.start()
        self.patcher_fam.start()
        self.patcher_inv.start()
        self.patcher_sol.start()
        self.patcher_rep.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher_fam.stop()
        self.patcher_inv.stop()
        self.patcher_sol.stop()
        self.patcher_rep.stop()
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

    def test_gestion_semanas(self):
        # Crear semanas
        sem1_id = SolicitudController.crear_semana("Semana 1 - Agosto 2026", "2026-08-01", "2026-08-07")
        self.assertTrue(sem1_id > 0)

        sem2_id = SolicitudController.crear_semana("Semana 2 - Agosto 2026", "2026-08-08", "2026-08-14")
        self.assertTrue(sem2_id > 0)

        # Validar semanas creadas
        semanas = SolicitudController.obtener_todas_semanas()
        self.assertEqual(len(semanas), 2)
        # Se ordenan por id DESC
        self.assertEqual(semanas[0]["nombre_semana"], "Semana 2 - Agosto 2026")
        self.assertEqual(semanas[1]["nombre_semana"], "Semana 1 - Agosto 2026")

        # Validaciones de campos obligatorios
        with self.assertRaises(ValueError):
            SolicitudController.crear_semana("", "2026-08-01", "2026-08-07")
        with self.assertRaises(ValueError):
            SolicitudController.crear_semana("Semana 3", "", "2026-08-07")
        with self.assertRaises(ValueError):
            SolicitudController.crear_semana("Semana 3", "2026-08-01", " ")

    def test_crear_solicitud_con_inventario_descuento(self):
        # Setup refugio, familia, categoría, producto y semana
        ref_id = RefugioController.crear_refugio("Refugio Transaccional", "Dirección", "Encargado", 50)
        fam_id = FamiliaController.crear_familia(ref_id, "FAM-111", "Familia Solicitudes")
        cat_id = InventarioController.crear_categoria("Alimentos", "Comida")

        prod_id = InventarioController.crear_producto(
            categoria_id=cat_id,
            nombre="Harina PAN",
            empaque_unidad="Bulto",
            tamano_unidad_peso=20.0,
            unidad_medida="kg",
            stock_unidades=15.0,
            precio_unidad=15.00
        )

        sem_id = SolicitudController.crear_semana("Semana 1", "2026-08-01", "2026-08-07")

        # Crear solicitud con producto de inventario (descuenta automáticamente)
        items = [{
            "producto_id": prod_id,
            "nombre_producto_manual": None,
            "cantidad_solicitada": 3.0,
            "unidad_medida_solicitada": "kg",
            "en_inventario": True
        }]

        sol_id = SolicitudController.crear_solicitud_con_detalles(
            semana_id=sem_id,
            familia_id=fam_id,
            observaciones="Entrega inicial",
            items=items
        )
        self.assertTrue(sol_id > 0)

        # Verificar que el stock disminuyó (15.0 - 3.0 = 12.0)
        prods = InventarioController.obtener_todos_productos()
        self.assertEqual(prods[0]["stock_unidades"], 12.0)

        # Consultar directamente base de datos para verificar en_inventario y descontado_stock
        cursor = self.real_conn.cursor()
        cursor.execute("SELECT producto_id, nombre_producto_manual, cantidad_solicitada, en_inventario, descontado_stock FROM detalles_solicitud WHERE solicitud_id = ?", (sol_id,))
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], prod_id)
        self.assertIsNone(rows[0][1])
        self.assertEqual(rows[0][2], 3.0)
        self.assertEqual(rows[0][3], 1)  # en_inventario = True (1)
        self.assertEqual(rows[0][4], 1)  # descontado_stock = True (1)

    def test_crear_solicitud_manual(self):
        # Setup
        ref_id = RefugioController.crear_refugio("Refugio Manual", "Dirección", "Encargado", 50)
        fam_id = FamiliaController.crear_familia(ref_id, "FAM-222", "Familia Manual")
        sem_id = SolicitudController.crear_semana("Semana 1", "2026-08-01", "2026-08-07")

        # Crear solicitud con producto manual
        items = [{
            "producto_id": None,
            "nombre_producto_manual": "Agua Mineral Embotellada",
            "cantidad_solicitada": 5.0,
            "unidad_medida_solicitada": "litros",
            "en_inventario": False
        }]

        sol_id = SolicitudController.crear_solicitud_con_detalles(
            semana_id=sem_id,
            familia_id=fam_id,
            observaciones="Manual item test",
            items=items
        )
        self.assertTrue(sol_id > 0)

        # Verificar detalles de solicitud manual en la base de datos
        cursor = self.real_conn.cursor()
        cursor.execute("SELECT producto_id, nombre_producto_manual, cantidad_solicitada, en_inventario, descontado_stock FROM detalles_solicitud WHERE solicitud_id = ?", (sol_id,))
        rows = cursor.fetchall()
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0][0])
        self.assertEqual(rows[0][1], "Agua Mineral Embotellada")
        self.assertEqual(rows[0][2], 5.0)
        self.assertEqual(rows[0][3], 0)  # en_inventario = False (0)
        self.assertEqual(rows[0][4], 0)  # descontado_stock = False (0)

    def test_crear_solicitud_transaccional_rollback_por_stock_insuficiente(self):
        # Setup
        ref_id = RefugioController.crear_refugio("Refugio Rollback", "Dirección", "Encargado", 50)
        fam_id = FamiliaController.crear_familia(ref_id, "FAM-333", "Familia Rollback")
        cat_id = InventarioController.crear_categoria("Alimentos", "Comida")

        prod_id1 = InventarioController.crear_producto(
            categoria_id=cat_id,
            nombre="Arroz",
            empaque_unidad="Saco",
            tamano_unidad_peso=10.0,
            unidad_medida="kg",
            stock_unidades=10.0,
            precio_unidad=10.00
        )
        prod_id2 = InventarioController.crear_producto(
            categoria_id=cat_id,
            nombre="Lentejas",
            empaque_unidad="Saco",
            tamano_unidad_peso=10.0,
            unidad_medida="kg",
            stock_unidades=5.0,
            precio_unidad=10.00
        )

        sem_id = SolicitudController.crear_semana("Semana 1", "2026-08-01", "2026-08-07")

        # Intentar crear solicitud con 2 ítems:
        # Item 1: Válido (Arroz 2kg)
        # Item 2: Inválido (Lentejas 6kg, supera el stock disponible de 5.0)
        items = [
            {
                "producto_id": prod_id1,
                "nombre_producto_manual": None,
                "cantidad_solicitada": 2.0,
                "unidad_medida_solicitada": "kg",
                "en_inventario": True
            },
            {
                "producto_id": prod_id2,
                "nombre_producto_manual": None,
                "cantidad_solicitada": 6.0,
                "unidad_medida_solicitada": "kg",
                "en_inventario": True
            }
        ]

        # Debe lanzar un ValueError de stock insuficiente y ejecutar un rollback
        with self.assertRaises(ValueError) as context:
            SolicitudController.crear_solicitud_con_detalles(
                semana_id=sem_id,
                familia_id=fam_id,
                observaciones="Este pedido fallará",
                items=items
            )
        self.assertIn("Stock insuficiente", str(context.exception))

        # Verificar que NO se modificó el stock del primer producto (debe seguir en 10.0)
        prods = {p["id"]: p for p in InventarioController.obtener_todos_productos()}
        self.assertEqual(prods[prod_id1]["stock_unidades"], 10.0)
        self.assertEqual(prods[prod_id2]["stock_unidades"], 5.0)

        # Verificar que NO se guardó ninguna solicitud ni detalles
        cursor = self.real_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM solicitudes")
        self.assertEqual(cursor.fetchone()[0], 0)
        cursor.execute("SELECT COUNT(*) FROM detalles_solicitud")
        self.assertEqual(cursor.fetchone()[0], 0)

    def test_crear_solicitud_validaciones(self):
        ref_id = RefugioController.crear_refugio("Refugio Val", "Dirección", "Encargado", 50)
        fam_id = FamiliaController.crear_familia(ref_id, "FAM-444", "Familia Val")
        sem_id = SolicitudController.crear_semana("Semana 1", "2026-08-01", "2026-08-07")

        # Semana ID inválido
        with self.assertRaises(ValueError):
            SolicitudController.crear_solicitud_con_detalles(0, fam_id, "", [{"en_inventario": False, "nombre_producto_manual": "A", "cantidad_solicitada": 1.0, "unidad_medida_solicitada": "u"}])

        # Familia ID inválido
        with self.assertRaises(ValueError):
            SolicitudController.crear_solicitud_con_detalles(sem_id, 0, "", [{"en_inventario": False, "nombre_producto_manual": "A", "cantidad_solicitada": 1.0, "unidad_medida_solicitada": "u"}])

        # Lista de ítems vacía
        with self.assertRaises(ValueError):
            SolicitudController.crear_solicitud_con_detalles(sem_id, fam_id, "", [])

        # Cantidad inválida (negativa o cero)
        with self.assertRaises(ValueError):
            SolicitudController.crear_solicitud_con_detalles(sem_id, fam_id, "", [{"en_inventario": False, "nombre_producto_manual": "A", "cantidad_solicitada": 0, "unidad_medida_solicitada": "u"}])

        # Nombre manual vacío
        with self.assertRaises(ValueError):
            SolicitudController.crear_solicitud_con_detalles(sem_id, fam_id, "", [{"en_inventario": False, "nombre_producto_manual": "", "cantidad_solicitada": 1.0, "unidad_medida_solicitada": "u"}])

    def test_obtener_reporte_y_exportar_excel(self):
        # Setup refugio, familia, integrantes, categoría, producto y semana
        ref_id = RefugioController.crear_refugio("Refugio Reportes", "Dirección", "Encargado", 50)
        fam_id = FamiliaController.crear_familia(ref_id, "FAM-R01", "Familia Reportes")

        # Integrantes
        FamiliaController.agregar_integrante(fam_id, "Esteban", "Quito", 30, "M", "")

        cat_id = InventarioController.crear_categoria("Alimentos", "Comida")
        prod_id = InventarioController.crear_producto(
            categoria_id=cat_id,
            nombre="Harina PAN",
            empaque_unidad="Bulto",
            tamano_unidad_peso=20.0,
            unidad_medida="kg",
            stock_unidades=15.0,
            precio_unidad=15.00
        )
        sem_id = SolicitudController.crear_semana("Semana 1 - Agosto 2026", "2026-08-01", "2026-08-07")

        # Crear solicitud con producto de inventario
        items = [{
            "producto_id": prod_id,
            "nombre_producto_manual": None,
            "cantidad_solicitada": 3.0,
            "unidad_medida_solicitada": "kg",
            "en_inventario": True
        }]

        SolicitudController.crear_solicitud_con_detalles(
            semana_id=sem_id,
            familia_id=fam_id,
            observaciones="Entrega",
            items=items
        )

        # Importamos el nuevo controlador
        from controllers.reporte_controller import ReporteController

        # 1. Obtener datos de reporte para la semana
        datos = ReporteController.obtener_datos_reporte(semana_id=sem_id)
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["Semana"], "Semana 1 - Agosto 2026")
        self.assertEqual(datos[0]["Refugio"], "Refugio Reportes")
        self.assertEqual(datos[0]["Código Familia"], "FAM-R01")
        self.assertEqual(datos[0]["Familia"], "Familia Reportes")
        self.assertEqual(datos[0]["Total Integrantes"], 1)
        self.assertEqual(datos[0]["Resumen Demográfico"], "1M / 0F (1 Adulto)")
        self.assertEqual(datos[0]["Producto Solicitado"], "Harina PAN")
        self.assertEqual(datos[0]["Cantidad"], 3.0)
        self.assertEqual(datos[0]["Unidad"], "kg")
        self.assertEqual(datos[0]["Disponibilidad en Inventario (Sí / No)"], "Sí")

        # 2. Con filtro de refugio que existe
        datos_filtro_si = ReporteController.obtener_datos_reporte(semana_id=sem_id, refugio_id=ref_id)
        self.assertEqual(len(datos_filtro_si), 1)

        # 3. Con filtro de refugio que no existe (debe dar vacío)
        datos_filtro_no = ReporteController.obtener_datos_reporte(semana_id=sem_id, refugio_id=999)
        self.assertEqual(len(datos_filtro_no), 0)

        # 4. Probar exportación a Excel
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_excel_path = os.path.join(tmpdir, "reporte_test.xlsx")
            ReporteController.exportar_a_excel(semana_id=sem_id, refugio_id=None, filepath=temp_excel_path)

            # Verificar existencia y tamaño del archivo
            self.assertTrue(os.path.exists(temp_excel_path))
            self.assertTrue(os.path.getsize(temp_excel_path) > 0)

            # Cargar con pandas para verificar que tenga las columnas esperadas
            import pandas as pd
            df_loaded = pd.read_excel(temp_excel_path)
            self.assertEqual(len(df_loaded), 1)
            self.assertEqual(df_loaded.iloc[0]["Semana"], "Semana 1 - Agosto 2026")
            self.assertEqual(df_loaded.iloc[0]["Resumen Demográfico"], "1M / 0F (1 Adulto)")
            self.assertEqual(df_loaded.iloc[0]["Disponibilidad en Inventario (Sí / No)"], "Sí")

    def test_editar_y_eliminar_refugios_y_familias(self):
        # 1. Crear refugio
        ref_id = RefugioController.crear_refugio("Refugio Original", "Calle A", "Responsable A", 50)

        # 2. Actualizar refugio
        RefugioController.actualizar_refugio(ref_id, "Refugio Actualizado", "Calle B", "Responsable B", 60)
        todos_ref = RefugioController.obtener_todos()
        ref_actualizado = next(r for r in todos_ref if r["id"] == ref_id)
        self.assertEqual(ref_actualizado["nombre"], "Refugio Actualizado")
        self.assertEqual(ref_actualizado["capacidad_maxima"], 60)

        # 3. Crear familia
        fam_id = FamiliaController.crear_familia(ref_id, "FAM-XYZ", "Familia Original")

        # Intentar eliminar refugio con familia asociada (debe lanzar ValueError)
        with self.assertRaises(ValueError):
            RefugioController.eliminar_refugio(ref_id)

        # 4. Actualizar familia
        FamiliaController.actualizar_familia(fam_id, "FAM-XYZ-ACT", "Familia Actualizada")
        familias = FamiliaController.obtener_familias_por_refugio(ref_id)
        fam_act = next(f for f in familias if f["id"] == fam_id)
        self.assertEqual(fam_act["codigo_numero"], "FAM-XYZ-ACT")
        self.assertEqual(fam_act["nombre_representativo"], "Familia Actualizada")

        # 5. Integrante
        int_id = FamiliaController.agregar_integrante(fam_id, "Carlos", "Sanz", 25, "M", "")
        FamiliaController.actualizar_integrante(int_id, "Carlos Act", "Sanz Act", 26, "F", "Ninguna")
        ints = FamiliaController.obtener_integrantes_por_familia(fam_id)
        int_act = next(i for i in ints if i["id"] == int_id)
        self.assertEqual(int_act["nombres"], "Carlos Act")
        self.assertEqual(int_act["edad"], 26)
        self.assertEqual(int_act["sexo"], "F")

        # 6. Eliminar integrante
        FamiliaController.eliminar_integrante(int_id)
        self.assertEqual(len(FamiliaController.obtener_integrantes_por_familia(fam_id)), 0)

        # 7. Eliminar familia
        FamiliaController.eliminar_familia(fam_id)
        self.assertEqual(len(FamiliaController.obtener_familias_por_refugio(ref_id)), 0)

        # 8. Eliminar refugio (ahora sí debe dejar porque está vacío)
        RefugioController.eliminar_refugio(ref_id)
        self.assertEqual(len([r for r in RefugioController.obtener_todos() if r["id"] == ref_id]), 0)

    def test_eliminar_solicitud_con_reversion_stock(self):
        ref_id = RefugioController.crear_refugio("Refugio Stock", "Calle Stock", "Juan", 100)
        fam_id = FamiliaController.crear_familia(ref_id, "FAM-STK", "Familia Stock")
        cat_id = InventarioController.crear_categoria("Alimentos", "Comida")
        prod_id = InventarioController.crear_producto(
            categoria_id=cat_id,
            nombre="Aceite",
            empaque_unidad="Botella",
            tamano_unidad_peso=1.0,
            unidad_medida="litros",
            stock_unidades=10.0,
            precio_unidad=5.0
        )
        sem_id = SolicitudController.crear_semana("Semana Stock", "2026-08-01", "2026-08-07")

        items = [{
            "producto_id": prod_id,
            "nombre_producto_manual": None,
            "cantidad_solicitada": 4.0,
            "unidad_medida_solicitada": "litros",
            "en_inventario": True
        }]

        sol_id = SolicitudController.crear_solicitud_con_detalles(
            semana_id=sem_id,
            familia_id=fam_id,
            observaciones="Pedido de Aceite",
            items=items
        )

        # Verificar descuento inicial (10.0 - 4.0 = 6.0)
        prod = next(p for p in InventarioController.obtener_todos_productos() if p["id"] == prod_id)
        self.assertEqual(prod["stock_unidades"], 6.0)

        # Eliminar la solicitud
        SolicitudController.eliminar_solicitud(sol_id)

        # Verificar que el stock volvió a 10.0
        prod_rev = next(p for p in InventarioController.obtener_todos_productos() if p["id"] == prod_id)
        self.assertEqual(prod_rev["stock_unidades"], 10.0)

    def test_reporte_sin_producto_cartesiano_y_con_agrupamiento(self):
        ref_id = RefugioController.crear_refugio("Refugio Multimiembros", "Calle X", "Pedro", 100)
        fam_id = FamiliaController.crear_familia(ref_id, "FAM-MULTI", "Familia Multimiembros")

        # 3 integrantes
        # Edades: 30 (Adulto >= 12), 28 (Adulto >= 12), 5 (Niño < 12)
        FamiliaController.agregar_integrante(fam_id, "Juan", "Pérez", 30, "M", "")
        FamiliaController.agregar_integrante(fam_id, "María", "Pérez", 28, "F", "")
        FamiliaController.agregar_integrante(fam_id, "Pedro", "Pérez", 5, "M", "")

        cat_id = InventarioController.crear_categoria("Alimentos", "Comida")
        prod_id = InventarioController.crear_producto(
            categoria_id=cat_id,
            nombre="Leche",
            empaque_unidad="Caja",
            tamano_unidad_peso=1.0,
            unidad_medida="litros",
            stock_unidades=20.0,
            precio_unidad=1.5
        )
        sem_id = SolicitudController.crear_semana("Semana Reporte Multi", "2026-08-01", "2026-08-07")

        # Familia pide 1 litro de leche
        items = [{
            "producto_id": prod_id,
            "nombre_producto_manual": None,
            "cantidad_solicitada": 1.0,
            "unidad_medida_solicitada": "litros",
            "en_inventario": True
        }]

        SolicitudController.crear_solicitud_con_detalles(
            semana_id=sem_id,
            familia_id=fam_id,
            observaciones="Pedido Leche",
            items=items
        )

        # Obtener reporte: DEBE tener exactamente 1 fila (no 3!) y el Nombre Integrante debe ser la concatenación
        datos = ReporteController.obtener_datos_reporte(semana_id=sem_id)
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["Producto Solicitado"], "Leche")
        self.assertEqual(datos[0]["Cantidad"], 1.0)

        # Verificar formato de resumen demográfico solicitado
        # 2 machos, 1 hembra -> 2M / 1F
        # Edad: Pedro (5) -> < 12 (Niño), Juan y María -> 12-59 (Adultos)
        # Resumen demográfico: "2M / 1F (1 Niño, 2 Adultos)"
        self.assertEqual(datos[0]["Total Integrantes"], 3)
        self.assertEqual(datos[0]["Resumen Demográfico"], "2M / 1F (1 Niño, 2 Adultos)")


if __name__ == "__main__":
    unittest.main()
