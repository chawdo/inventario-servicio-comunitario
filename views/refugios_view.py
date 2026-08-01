from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QMessageBox, QGroupBox, QSpinBox, QDialog
)
from PyQt6.QtCore import Qt
from controllers.refugio_controller import RefugioController

class EditarRefugioDialog(QDialog):
    """
    Modal para editar un refugio existente.
    """
    def __init__(self, refugio, parent=None):
        super().__init__(parent)
        self.refugio = refugio
        self.setWindowTitle("Editar Refugio")
        self.resize(350, 250)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_group = QGroupBox("Datos del Refugio")
        form_layout = QFormLayout(form_group)

        self.txt_nombre = QLineEdit(self.refugio["nombre"])
        self.txt_direccion = QLineEdit(self.refugio["direccion"])
        self.txt_responsable = QLineEdit(self.refugio["responsable"])
        self.spin_capacidad = QSpinBox()
        self.spin_capacidad.setRange(1, 10000)
        self.spin_capacidad.setValue(self.refugio["capacidad_maxima"])

        form_layout.addRow("Nombre *:", self.txt_nombre)
        form_layout.addRow("Dirección:", self.txt_direccion)
        form_layout.addRow("Responsable:", self.txt_responsable)
        form_layout.addRow("Capacidad Máxima *:", self.spin_capacidad)

        layout.addWidget(form_group)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 6px;")
        self.btn_guardar.clicked.connect(self.guardar_cambios)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("background-color: #90A4AE; color: white; font-weight: bold; padding: 6px;")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

    def guardar_cambios(self):
        nombre = self.txt_nombre.text().strip()
        direccion = self.txt_direccion.text().strip()
        responsable = self.txt_responsable.text().strip()
        capacidad = self.spin_capacidad.value()

        if not nombre:
            QMessageBox.warning(self, "Campo Requerido", "El campo 'Nombre' es obligatorio.")
            self.txt_nombre.setFocus()
            return

        try:
            RefugioController.actualizar_refugio(self.refugio["id"], nombre, direccion, responsable, capacidad)
            QMessageBox.information(self, "Éxito", "El refugio ha sido actualizado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el refugio: {e}")


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
        self.table_refugios.setColumnCount(6)
        self.table_refugios.setHorizontalHeaderLabels([
            "ID", "Nombre", "Dirección", "Responsable", "Capacidad", "Acciones"
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

                # Botones de Acción: Editar y Eliminar
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                btn_layout.setSpacing(4)

                btn_editar = QPushButton("Editar")
                btn_editar.setStyleSheet("background-color: #F57C00; color: white; padding: 2px 6px; font-weight: bold;")
                btn_editar.clicked.connect(lambda checked, r=r: self.editar_refugio_modal(r))

                btn_eliminar = QPushButton("Eliminar")
                btn_eliminar.setStyleSheet("background-color: #D32F2F; color: white; padding: 2px 6px; font-weight: bold;")
                btn_eliminar.clicked.connect(lambda checked, r_id=r["id"]: self.eliminar_refugio(r_id))

                btn_layout.addWidget(btn_editar)
                btn_layout.addWidget(btn_eliminar)
                self.table_refugios.setCellWidget(row_idx, 5, btn_container)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar refugios: {e}")

    def editar_refugio_modal(self, refugio):
        """
        Abre el modal para editar el refugio.
        """
        dialog = EditarRefugioDialog(refugio, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.cargar_refugios()

    def eliminar_refugio(self, refugio_id):
        """
        Muestra confirmación y elimina un refugio si es seguro.
        """
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            "¿Está seguro de que desea eliminar este refugio?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                RefugioController.eliminar_refugio(refugio_id)
                QMessageBox.information(self, "Éxito", "El refugio ha sido eliminado correctamente.")
                self.cargar_refugios()
            except ValueError as ve:
                QMessageBox.warning(self, "No se puede eliminar", str(ve))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el refugio: {e}")

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
