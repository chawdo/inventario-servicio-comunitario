from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QStackedWidget, QLabel, QFrame, QListWidgetItem
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon
from views.refugios_view import RefugiosView
from views.familias_view import FamiliasView
from views.inventario_view import InventarioView
from views.solicitudes_view import SolicitudesView
from views.reportes_view import ReportesView

class PlaceholderView(QWidget):
    """
    Vista temporal para mostrar módulos aún no implementados (fases futuras).
    """
    def __init__(self, titulo: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(titulo)
        lbl.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #78909C;")

        desc = QLabel("Módulo en construcción para próximas fases.")
        desc.setFont(QFont("Arial", 12))
        desc.setStyleSheet("color: #90A4AE;")

        layout.addWidget(lbl)
        layout.addWidget(desc)


class MainWindow(QMainWindow):
    """
    Ventana principal que gestiona el menú de navegación lateral
    y el intercambio de vistas de los diferentes módulos.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión de Refugios e Inventario")
        self.resize(1100, 700)
        self.init_ui()

    def init_ui(self):
        # Widget central y layout horizontal principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ------------------ MENÚ LATERAL ------------------
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #263238;
                color: #ECEFF1;
                border: none;
                padding-top: 10px;
            }
            QListWidget::item {
                padding: 12px 15px;
                font-size: 13px;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #37474F;
                color: #FFFFFF;
            }
            QListWidget::item:selected {
                background-color: #00897B;
                color: #FFFFFF;
                border-left: 5px solid #00E676;
            }
        """)

        # Añadir elementos de menú con un diseño agradable
        menu_items = [
            ("Refugios", "Fase 2: Gestión de Refugios"),
            ("Familias e Integrantes", "Fase 2: Familias y Censos"),
            ("Inventario y Categorías", "Fase 3: Control de Productos"),
            ("Solicitudes Semanales", "Fase 3: Registro de Insumos"),
            ("Reportes Excel", "Fase 4: Exportación de Datos")
        ]

        for item_text, tool_tip in menu_items:
            list_item = QListWidgetItem(item_text)
            list_item.setToolTip(tool_tip)
            self.sidebar.addItem(list_item)

        self.sidebar.currentRowChanged.connect(self.cambiar_modulo)

        # ------------------ CONTENEDOR MULTIVISTA ------------------
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #F5F7F8;")

        # Instanciar las vistas de la Fase 2
        self.refugios_view = RefugiosView()
        self.familias_view = FamiliasView()

        # Instanciar la vista de la Fase 3
        self.inventario_view = InventarioView()

        # Instanciar la vista de la Fase 4
        self.solicitudes_view = SolicitudesView()

        # Instanciar la vista de la Fase 5 (Reportes)
        self.reportes_view = ReportesView()

        # Añadir al stacked widget
        self.stacked_widget.addWidget(self.refugios_view)
        self.stacked_widget.addWidget(self.familias_view)
        self.stacked_widget.addWidget(self.inventario_view)
        self.stacked_widget.addWidget(self.solicitudes_view)
        self.stacked_widget.addWidget(self.reportes_view)

        # Añadir componentes al layout principal
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)

        # Seleccionar el primer módulo por defecto
        self.sidebar.setCurrentRow(0)

    def cambiar_modulo(self, index):
        """
        Intercambia el widget activo en el QStackedWidget al cambiar la selección del menú lateral.
        """
        self.stacked_widget.setCurrentIndex(index)

        # Si se cambia a la vista de familias, refrescar el selector de refugios
        # por si se acaba de registrar un refugio nuevo.
        if index == 1:
            self.familias_view.cargar_combo_refugios()
        # Si se cambia a la vista de inventario, refrescar categorías e inventario
        elif index == 2:
            self.inventario_view.cargar_categorias_combo()
            self.inventario_view.cargar_inventario()
        # Si se cambia a la vista de solicitudes, refrescar semanas, refugios y productos
        elif index == 3:
            self.solicitudes_view.cargar_semanas()
            self.solicitudes_view.cargar_refugios()
            self.solicitudes_view.cargar_productos_inventario()
        # Si se cambia a la vista de reportes, refrescar semanas, refugios y vista previa
        elif index == 4:
            self.reportes_view.cargar_semanas()
            self.reportes_view.cargar_refugios()
            self.reportes_view.cargar_vista_previa()
