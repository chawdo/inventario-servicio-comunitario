import sys
import os

# Asegurar que el directorio raíz está en el PATH de búsqueda de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from database.schema import init_db
from views.main_window import MainWindow

def main():
    """
    Punto de entrada principal para la aplicación de Gestión de Refugios.
    """
    # 1. Inicializar la base de datos y crear tablas si no existen
    init_db()

    # 2. Iniciar la aplicación Qt
    app = QApplication(sys.argv)

    # 3. Mostrar la Ventana Principal
    window = MainWindow()
    window.show()

    # 4. Iniciar el bucle de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
