from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QMessageBox, QGroupBox, QSpinBox
)
from PyQt6.QtCore import Qt
from controllers.refugio_controller import RefugioController

class RefugiosView(QWidget):
    """
    Vista para visualizar y registrar refugios.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Layout principal horizontal para dividir en formulario (izquierda) y tabla (derecha)
        main_layout = QHBoxLayout(self)

        # ------------------ SECCIÓN IZQUIERDA: FORMULARIO ------------------
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)

        group_box = QGroupBox("Registrar Nuevo Refugio")
        group_layout = QFormLayout(group_box)

        # Campos del formulario
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej. Refugio San José")

        self.txt_direccion = QLineEdit()
        self.txt_direccion.setPlaceholderText("Ej. Calle Principal Nro 45")

        self.txt_responsable = QLineEdit()
        self.txt_responsable.setPlaceholderText("Ej. Juan Pérez")

        self.spin_capacidad = QSpinBox()
        self.spin_capacidad.setRange(1, 10000)
        self.spin_capacidad.setValue(100)

        group_layout.addRow("Nombre *:", self.txt_nombre)
        group_layout.addRow("Dirección:", self.txt_direccion)
        group_layout.addRow("Responsable:", self.txt_responsable)
        group_layout.addRow("Capacidad Máxima *:", self.spin_capacidad)

        self.btn_guardar = QPushButton("Guardar Refugio")
        self.btn_guardar.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 6px;")
        self.btn_guardar.clicked.connect(self.guardar_refugio)

        form_layout.addWidget(group_box)
        form_layout.addWidget(self.btn_guardar)
        form_layout.addStretch()

        # ------------------ SECCIÓN DERECHA: TABLA ------------------
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)

        lbl_titulo_tabla = QLabel("Refugios Registrados")
        lbl_titulo_tabla.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        table_layout.addWidget(lbl_titulo_tabla)

        self.table_refugios = QTableWidget()
        self.table_refugios.setColumnCount(5)
        self.table_refugios.setHorizontalHeaderLabels([
            "ID", "Nombre", "Dirección", "Responsable", "Capacidad"
        ])
        self.table_refugios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_refugios.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_refugios.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        table_layout.addWidget(self.table_refugios)

        # Añadir al layout principal
        main_layout.addWidget(form_container, stretch=1)
        main_layout.addWidget(table_container, stretch=2)

        # Cargar datos iniciales
        self.cargar_refugios()

    def cargar_refugios(self):
        """
        Carga la lista de refugios desde la base de datos en la tabla.
        """
        self.table_refugios.setRowCount(0)
        try:
            refugios = RefugioController.obtener_todos()
            for r in refugios:
                row_idx = self.table_refugios.rowCount()
                self.table_refugios.insertRow(row_idx)

                self.table_refugios.setItem(row_idx, 0, QTableWidgetItem(str(r["id"])))
                self.table_refugios.setItem(row_idx, 1, QTableWidgetItem(r["nombre"]))
                self.table_refugios.setItem(row_idx, 2, QTableWidgetItem(r["direccion"]))
                self.table_refugios.setItem(row_idx, 3, QTableWidgetItem(r["responsable"]))
                self.table_refugios.setItem(row_idx, 4, QTableWidgetItem(str(r["capacidad_maxima"])))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar refugios: {e}")

    def guardar_refugio(self):
        """
        Guarda un nuevo refugio tras realizar validaciones básicas.
        """
        nombre = self.txt_nombre.text().strip()
        direccion = self.txt_direccion.text().strip()
        responsable = self.txt_responsable.text().strip()
        capacidad = self.spin_capacidad.value()

        if not nombre:
            QMessageBox.warning(self, "Campo Requerido", "El campo 'Nombre' es obligatorio.")
            self.txt_nombre.setFocus()
            return

        try:
            RefugioController.crear_refugio(nombre, direccion, responsable, capacidad)
            QMessageBox.information(self, "Éxito", "El refugio ha sido registrado correctamente.")

            # Limpiar campos
            self.txt_nombre.clear()
            self.txt_direccion.clear()
            self.txt_responsable.clear()
            self.spin_capacidad.setValue(100)

            # Recargar tabla
            self.cargar_refugios()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el refugio: {e}")
