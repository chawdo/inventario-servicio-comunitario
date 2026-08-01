import sqlite3
import os
import sys

# Permitir la ejecución tanto desde la raíz del proyecto como desde el propio directorio 'database/'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schema import get_connection, create_tables

def seed() -> None:
    """
    Inserta datos de prueba en la base de datos para comprobar su correcto funcionamiento:
    - 1 refugio
    - 2 familias con integrantes
    - 1 categoría
    - 3 productos de inventario
    - 1 semana
    """
    conn = get_connection()
    try:
        # Asegurarse de que las tablas existan
        create_tables(conn)

        cursor = conn.cursor()

        # --- 1. Insertar Refugio ---
        cursor.execute("""
            INSERT INTO refugios (nombre, direccion, responsable, capacidad_maxima)
            VALUES (?, ?, ?, ?)
        """, ("Refugio Esperanza", "Av. Principal Nro 123", "María López", 50))
        refugio_id = cursor.lastrowid
        print(f"Refugio insertado exitosamente con ID: {refugio_id}")

        # --- 2. Insertar Familias ---
        # Familia 1
        cursor.execute("""
            INSERT INTO familias (refugio_id, codigo_numero, nombre_representativo)
            VALUES (?, ?, ?)
        """, (refugio_id, "FAM-001", "Familia Pérez"))
        familia_1_id = cursor.lastrowid
        print(f"Familia 1 (Pérez) insertada con ID: {familia_1_id}")

        # Familia 2
        cursor.execute("""
            INSERT INTO familias (refugio_id, codigo_numero, nombre_representativo)
            VALUES (?, ?, ?)
        """, (refugio_id, "FAM-002", "Familia Gómez"))
        familia_2_id = cursor.lastrowid
        print(f"Familia 2 (Gómez) insertada con ID: {familia_2_id}")

        # --- 3. Insertar Integrantes ---
        # Integrantes Familia Pérez
        integrantes_perez = [
            (familia_1_id, "Juan", "Pérez", 45, "M", "Ninguna"),
            (familia_1_id, "Ana", "Pérez", 42, "F", "Ninguna"),
            (familia_1_id, "Luisito", "Pérez", 8, "M", "Alergia alimentaria")
        ]
        cursor.executemany("""
            INSERT INTO integrantes (familia_id, nombres, apellidos, edad, sexo, condicion_especial)
            VALUES (?, ?, ?, ?, ?, ?)
        """, integrantes_perez)
        print("Integrantes de la Familia Pérez insertados correctamente.")

        # Integrantes Familia Gómez
        integrantes_gomez = [
            (familia_2_id, "Carlos", "Gómez", 68, "M", "Hipertensión"),
            (familia_2_id, "Marta", "Gómez", 65, "F", "Movilidad reducida")
        ]
        cursor.executemany("""
            INSERT INTO integrantes (familia_id, nombres, apellidos, edad, sexo, condicion_especial)
            VALUES (?, ?, ?, ?, ?, ?)
        """, integrantes_gomez)
        print("Integrantes de la Familia Gómez insertados correctamente.")

        # --- 4. Insertar Categoría de Productos ---
        cursor.execute("""
            INSERT OR IGNORE INTO categorias (nombre, descripcion)
            VALUES (?, ?)
        """, ("Alimentos", "Insumos alimenticios básicos para las familias"))
        # Si ya existe, podemos obtener su id
        cursor.execute("SELECT id FROM categorias WHERE nombre = ?", ("Alimentos",))
        categoria_id = cursor.fetchone()[0]
        print(f"Categoría 'Alimentos' seleccionada/insertada con ID: {categoria_id}")

        # --- 5. Insertar 3 Productos de Inventario ---
        # Producto 1: Arroz
        # Producto 2: Harina de Maíz
        # Producto 3: Aceite Vegetal
        productos = [
            (categoria_id, "Arroz Premium", "Saco de 24 kg", 24.0, "kg", 10.0, 24.00, 1.00),
            (categoria_id, "Harina de Maíz Precocida", "Bulto de 20 kg", 20.0, "kg", 15.0, 18.00, 0.90),
            (categoria_id, "Aceite Vegetal", "Caja de 12 litros", 12.0, "litros", 8.0, 30.00, 2.50)
        ]

        cursor.executemany("""
            INSERT INTO productos (categoria_id, nombre, empaque_unidad, tamano_unidad_peso, unidad_medida, stock_unidades, precio_unidad, precio_kilo_litro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, productos)
        print("3 Productos de prueba insertados en inventario correctamente.")

        # --- 6. Insertar Semana de Control ---
        cursor.execute("""
            INSERT INTO semanas (nombre_semana, fecha_inicio, fecha_fin)
            VALUES (?, ?, ?)
        """, ("Semana 1 - Agosto 2026", "2026-08-01", "2026-08-07"))
        semana_id = cursor.lastrowid
        print(f"Semana 1 insertada con ID: {semana_id}")

        # Confirmar transacción
        conn.commit()
        print("Transacción confirmada de forma exitosa. Seeding completado.")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error durante el proceso de seeding, se realizó rollback: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    seed()
