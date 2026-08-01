import sys
import sqlite3
from pathlib import Path
from typing import Optional

def get_db_path() -> str:
    """
    Obtiene la ruta absoluta de la base de datos.
    Detecta si la app se ejecuta como .exe o como script de Python.
    """
    if getattr(sys, 'frozen', False):
        # Si se ejecuta como .exe, guarda la BD junto al ejecutable
        base_dir = Path(sys.executable).parent
    else:
        # Si se ejecuta como script, guarda en la raíz del proyecto
        base_dir = Path(__file__).resolve().parent.parent

    db_dir = base_dir / "database"
    db_dir.mkdir(parents=True, exist_ok=True)  # Crea la carpeta si no existe

    return str(db_dir / "refugios.db")

def get_connection(db_path: str = None) -> sqlite3.Connection:
    if db_path is None:
        db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_tables(conn: sqlite3.Connection) -> None:
    """
    Crea todas las tablas definidas en la Sección 3 de REQUIREMENTS.md.
    """
    cursor = conn.cursor()
    try:
        # Tabla: refugios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS refugios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT,
            responsable TEXT,
            capacidad_maxima INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Tabla: familias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS familias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            refugio_id INTEGER NOT NULL,
            codigo_numero TEXT NOT NULL,
            nombre_representativo TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (refugio_id) REFERENCES refugios (id) ON DELETE CASCADE
        );
        """)

        # Tabla: integrantes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS integrantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            familia_id INTEGER NOT NULL,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            edad INTEGER NOT NULL,
            sexo TEXT CHECK(sexo IN ('M', 'F')) NOT NULL,
            condicion_especial TEXT,
            FOREIGN KEY (familia_id) REFERENCES familias (id) ON DELETE CASCADE
        );
        """)

        # Tabla: categorias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT
        );
        """)

        # Tabla: productos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            empaque_unidad TEXT NOT NULL,
            tamano_unidad_peso REAL NOT NULL,
            unidad_medida TEXT NOT NULL,
            stock_unidades REAL NOT NULL DEFAULT 0.0,
            precio_unidad REAL NOT NULL DEFAULT 0.0,
            precio_kilo_litro REAL NOT NULL DEFAULT 0.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE CASCADE
        );
        """)

        # Tabla: semanas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS semanas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_semana TEXT NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL
        );
        """)

        # Tabla: solicitudes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semana_id INTEGER NOT NULL,
            familia_id INTEGER NOT NULL,
            fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observaciones TEXT,
            FOREIGN KEY (semana_id) REFERENCES semanas (id) ON DELETE CASCADE,
            FOREIGN KEY (familia_id) REFERENCES familias (id) ON DELETE CASCADE
        );
        """)

        # Tabla: detalles_solicitud
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalles_solicitud (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solicitud_id INTEGER NOT NULL,
            producto_id INTEGER,
            nombre_producto_manual TEXT,
            cantidad_solicitada REAL NOT NULL,
            unidad_medida_solicitada TEXT NOT NULL,
            en_inventario INTEGER NOT NULL DEFAULT 1, -- Usamos INTEGER para representar BOOLEAN (0 o 1)
            descontado_stock INTEGER NOT NULL DEFAULT 0, -- Usamos INTEGER para representar BOOLEAN (0 o 1)
            FOREIGN KEY (solicitud_id) REFERENCES solicitudes (id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos (id) ON DELETE SET NULL
        );
        """)

        conn.commit()
        print("Todas las tablas han sido creadas exitosamente.")
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error al crear las tablas de la base de datos: {e}")
        raise
    finally:
        cursor.close()

def init_db(db_path: str = None) -> None:
    """
    Inicializa la base de datos y crea las tablas.
    """
    try:
        if db_path is None:
            db_path = get_db_path()
        conn = get_connection(db_path)
        create_tables(conn)
        conn.close()
    except sqlite3.Error as e:
        print(f"Error durante la inicialización de la base de datos: {e}")
        raise

if __name__ == "__main__":
    init_db()
