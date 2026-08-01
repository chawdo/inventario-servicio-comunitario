from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QMessageBox, QGroupBox, QComboBox, QSpinBox,
    QRadioButton, QButtonGroup, QSplitter, QDialog
)
from PyQt6.QtCore import Qt
from controllers.refugio_controller import RefugioController
from controllers.familia_controller import FamiliaController

class EditarFamiliaDialog(QDialog):
    """
    Modal para editar una familia existente.
    """
    def __init__(self, familia, parent=None):
        super().__init__(parent)
        self.familia = familia
        self.setWindowTitle("Editar Familia")
        self.resize(350, 180)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_group = QGroupBox("Datos de la Familia")
        form_layout = QFormLayout(form_group)

        self.txt_codigo = QLineEdit(self.familia["codigo_numero"])
        self.txt_nombre = QLineEdit(self.familia["nombre_representativo"])

        form_layout.addRow("Código / Número *:", self.txt_codigo)
        form_layout.addRow("Nombre Representativo *:", self.txt_nombre)

        layout.addWidget(form_group)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setStyleSheet("background-color: #0288D1; color: white; font-weight: bold; padding: 6px;")
        self.btn_guardar.clicked.connect(self.guardar_cambios)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("background-color: #90A4AE; color: white; font-weight: bold; padding: 6px;")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

    def guardar_cambios(self):
        codigo = self.txt_codigo.text().strip()
        nombre = self.txt_nombre.text().strip()

        if not codigo or not nombre:
            QMessageBox.warning(self, "Campos Requeridos", "Todos los campos con (*) son obligatorios.")
            return

        try:
            FamiliaController.actualizar_familia(self.familia["id"], codigo, nombre)
            QMessageBox.information(self, "Éxito", "La familia ha sido actualizada correctamente.")
            self.accept()
        except ValueError as ve:
            QMessageBox.warning(self, "Validación", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar la familia: {e}")


class EditarIntegranteDialog(QDialog):
    """
    Modal para editar un integrante existente.
    """
    def __init__(self, integrante, parent=None):
        super().__init__(parent)
        self.integrante = integrante
        self.setWindowTitle("Editar Integrante")
        self.resize(400, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_group = QGroupBox("Datos del Integrante")
        form_layout = QFormLayout(form_group)

        self.txt_nombres = QLineEdit(self.integrante["nombres"])
        self.txt_apellidos = QLineEdit(self.integrante["apellidos"])

        self.spin_edad = QSpinBox()
        self.spin_edad.setRange(0, 120)
        self.spin_edad.setValue(self.integrante["edad"])

        # Sexo (Radio Buttons)
        sexo_container = QWidget()
        sexo_layout = QHBoxLayout(sexo_container)
        sexo_layout.setContentsMargins(0, 0, 0, 0)
        self.radio_m = QRadioButton("M")
        self.radio_f = QRadioButton("F")
        if self.integrante["sexo"] == "M":
            self.radio_m.setChecked(True)
        else:
            self.radio_f.setChecked(True)
        sexo_layout.addWidget(self.radio_m)
        sexo_layout.addWidget(self.radio_f)
        sexo_layout.addStretch()

        self.button_group_sexo = QButtonGroup(self)
        self.button_group_sexo.addButton(self.radio_m)
        self.button_group_sexo.addButton(self.radio_f)

        self.txt_condicion = QLineEdit(self.integrante["condicion_especial"])

        form_layout.addRow("Nombres *:", self.txt_nombres)
        form_layout.addRow("Apellidos *:", self.txt_apellidos)
        form_layout.addRow("Edad *:", self.spin_edad)
        form_layout.addRow("Sexo *:", sexo_container)
        form_layout.addRow("Condición Especial:", self.txt_condicion)

        layout.addWidget(form_group)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar Cambios")
        self.btn_guardar.setStyleSheet("background-color: #E64A19; color: white; font-weight: bold; padding: 6px;")
        self.btn_guardar.clicked.connect(self.guardar_cambios)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("background-color: #90A4AE; color: white; font-weight: bold; padding: 6px;")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

    def guardar_cambios(self):
        nombres = self.txt_nombres.text().strip()
        apellidos = self.txt_apellidos.text().strip()
        edad = self.spin_edad.value()
        sexo = "M" if self.radio_m.isChecked() else "F"
        condicion = self.txt_condicion.text().strip()

        if not nombres or not apellidos:
            QMessageBox.warning(self, "Campos Requeridos", "Los nombres y apellidos son obligatorios.")
            return

        try:
            FamiliaController.actualizar_integrante(self.integrante["id"], nombres, apellidos, edad, sexo, condicion)
            QMessageBox.information(self, "Éxito", "El integrante ha sido actualizado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el integrante: {e}")


class FamiliasView(QWidget):
    """
    Vista para gestionar Familias y sus Integrantes pertenecientes a un Refugio seleccionado.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Usamos un layout vertical principal
        main_layout = QVBoxLayout(self)

        # ------------------ TOP PANEL: SELECTOR DE REFUGIO ------------------
        selector_layout = QHBoxLayout()
        lbl_selector = QLabel("Seleccione un Refugio:")
        lbl_selector.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.combo_refugios = QComboBox()
        self.combo_refugios.setMinimumWidth(250)
        self.combo_refugios.currentIndexChanged.connect(self.al_seleccionar_refugio)

        self.btn_actualizar_combo = QPushButton("Actualizar Lista")
        self.btn_actualizar_combo.clicked.connect(self.cargar_combo_refugios)

        selector_layout.addWidget(lbl_selector)
        selector_layout.addWidget(self.combo_refugios)
        selector_layout.addWidget(self.btn_actualizar_combo)
        selector_layout.addStretch()
        main_layout.addLayout(selector_layout)

        # ------------------ SPLITTER PRINCIPAL: FAMILIAS (IZQ) E INTEGRANTES (DER) ------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # =============== SUB-SECCIÓN IZQUIERDA: FAMILIAS ===============
        widget_familias = QWidget()
        layout_familias = QVBoxLayout(widget_familias)

        # Formulario registrar familia
        group_registro_fam = QGroupBox("Registrar Nueva Familia")
        form_fam_layout = QFormLayout(group_registro_fam)

        self.txt_codigo_fam = QLineEdit()
        self.txt_codigo_fam.setPlaceholderText("Ej. FAM-001")
        self.txt_nombre_fam = QLineEdit()
        self.txt_nombre_fam.setPlaceholderText("Ej. Familia Pérez")

        form_fam_layout.addRow("Código / Número *:", self.txt_codigo_fam)
        form_fam_layout.addRow("Nombre Representativo *:", self.txt_nombre_fam)

        self.btn_guardar_fam = QPushButton("Guardar Familia")
        self.btn_guardar_fam.setStyleSheet("background-color: #0288D1; color: white; font-weight: bold;")
        self.btn_guardar_fam.clicked.connect(self.guardar_familia)
        form_fam_layout.addRow("", self.btn_guardar_fam)

        layout_familias.addWidget(group_registro_fam)

        # Tabla de Familias
        lbl_fam_registradas = QLabel("Familias en este Refugio")
        lbl_fam_registradas.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 10px;")
        layout_familias.addWidget(lbl_fam_registradas)

        self.table_familias = QTableWidget()
        self.table_familias.setColumnCount(4)
        self.table_familias.setHorizontalHeaderLabels(["ID", "Código", "Nombre Representativo", "Acciones"])
        self.table_familias.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_familias.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_familias.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_familias.itemSelectionChanged.connect(self.al_seleccionar_familia)

        layout_familias.addWidget(self.table_familias)
        splitter.addWidget(widget_familias)

        # =============== SUB-SECCIÓN DERECHA: INTEGRANTES ===============
        widget_integrantes = QWidget()
        layout_integrantes = QVBoxLayout(widget_integrantes)

        # Formulario registrar integrante
        self.group_registro_int = QGroupBox("Registrar Integrante de la Familia")
        self.group_registro_int.setEnabled(False) # Deshabilitado hasta seleccionar familia
        form_int_layout = QFormLayout(self.group_registro_int)

        self.txt_int_nombres = QLineEdit()
        self.txt_int_apellidos = QLineEdit()

        self.spin_int_edad = QSpinBox()
        self.spin_int_edad.setRange(0, 120)
        self.spin_int_edad.setValue(30)

        # Sexo (Radio Buttons)
        sexo_container = QWidget()
        sexo_layout = QHBoxLayout(sexo_container)
        sexo_layout.setContentsMargins(0, 0, 0, 0)
        self.radio_m = QRadioButton("M")
        self.radio_f = QRadioButton("F")
        self.radio_m.setChecked(True)
        sexo_layout.addWidget(self.radio_m)
        sexo_layout.addWidget(self.radio_f)
        sexo_layout.addStretch()

        self.button_group_sexo = QButtonGroup(self)
        self.button_group_sexo.addButton(self.radio_m)
        self.button_group_sexo.addButton(self.radio_f)

        self.txt_int_condicion = QLineEdit()
        self.txt_int_condicion.setPlaceholderText("Ej. Alergia, hipertensión, ninguna")

        form_int_layout.addRow("Nombres *:", self.txt_int_nombres)
        form_int_layout.addRow("Apellidos *:", self.txt_int_apellidos)
        form_int_layout.addRow("Edad *:", self.spin_int_edad)
        form_int_layout.addRow("Sexo *:", sexo_container)
        form_int_layout.addRow("Condición Especial:", self.txt_int_condicion)

        self.btn_guardar_int = QPushButton("Agregar Integrante")
        self.btn_guardar_int.setStyleSheet("background-color: #E64A19; color: white; font-weight: bold;")
        self.btn_guardar_int.clicked.connect(self.guardar_integrante)
        form_int_layout.addRow("", self.btn_guardar_int)

        layout_integrantes.addWidget(self.group_registro_int)

        # Panel de Resumen de la Familia seleccionada
        self.group_resumen = QGroupBox("Resumen de Familia Seleccionada")
        layout_resumen = QHBoxLayout(self.group_resumen)

        self.lbl_resumen_total = QLabel("Total Integrantes: 0")
        self.lbl_resumen_total.setStyleSheet("font-weight: bold; color: #1565C0;")

        self.lbl_resumen_detalles = QLabel("Niños: 0  |  Adultos: 0  |  Adultos Mayores: 0")
        self.lbl_resumen_detalles.setStyleSheet("font-weight: bold; color: #37474F;")

        layout_resumen.addWidget(self.lbl_resumen_total)
        layout_resumen.addSpacing(20)
        layout_resumen.addWidget(self.lbl_resumen_detalles)
        layout_resumen.addStretch()

        layout_integrantes.addWidget(self.group_resumen)

        # Tabla de Integrantes
        lbl_int_registrados = QLabel("Integrantes Registrados")
        lbl_int_registrados.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout_integrantes.addWidget(lbl_int_registrados)

        self.table_integrantes = QTableWidget()
        self.table_integrantes.setColumnCount(7)
        self.table_integrantes.setHorizontalHeaderLabels([
            "ID", "Nombres", "Apellidos", "Edad", "Sexo", "Condición Especial", "Acciones"
        ])
        self.table_integrantes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_integrantes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_integrantes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout_integrantes.addWidget(self.table_integrantes)
        splitter.addWidget(widget_integrantes)

        # Establecer tamaños proporcionales para el splitter (50% cada lado)
        splitter.setSizes([450, 550])

        # Carga inicial de refugios
        self.cargar_combo_refugios()

    # ------------------ LOGICA Y CARGA DE DATOS ------------------

    def cargar_combo_refugios(self):
        """
        Carga el dropdown de refugios disponibles.
        """
        self.combo_refugios.blockSignals(True)
        self.combo_refugios.clear()
        try:
            refugios = RefugioController.obtener_todos()
            for r in refugios:
                self.combo_refugios.addItem(r["nombre"], r["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar refugios en selector: {e}")
        finally:
            self.combo_refugios.blockSignals(False)

        # Forzar evento de selección para actualizar tablas
        self.al_seleccionar_refugio()

    def al_seleccionar_refugio(self):
        """
        Evento gatillado al cambiar el refugio seleccionado.
        """
        self.table_familias.setRowCount(0)
        self.table_integrantes.setRowCount(0)
        self.group_registro_int.setEnabled(False)
        self.actualizar_resumen([])

        refugio_id = self.combo_refugios.currentData()
        if refugio_id is None:
            return

        try:
            familias = FamiliaController.obtener_familias_por_refugio(refugio_id)
            for f in familias:
                row_idx = self.table_familias.rowCount()
                self.table_familias.insertRow(row_idx)
                self.table_familias.setItem(row_idx, 0, QTableWidgetItem(str(f["id"])))
                self.table_familias.setItem(row_idx, 1, QTableWidgetItem(f["codigo_numero"]))
                self.table_familias.setItem(row_idx, 2, QTableWidgetItem(f["nombre_representativo"]))

                # Botones de Acción: Editar y Eliminar para Familia
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                btn_layout.setSpacing(4)

                btn_editar = QPushButton("Editar")
                btn_editar.setStyleSheet("background-color: #F57C00; color: white; padding: 2px 6px; font-weight: bold;")
                btn_editar.clicked.connect(lambda checked, f=f: self.editar_familia_modal(f))

                btn_eliminar = QPushButton("Eliminar")
                btn_eliminar.setStyleSheet("background-color: #D32F2F; color: white; padding: 2px 6px; font-weight: bold;")
                btn_eliminar.clicked.connect(lambda checked, f_id=f["id"]: self.eliminar_familia(f_id))

                btn_layout.addWidget(btn_editar)
                btn_layout.addWidget(btn_eliminar)
                self.table_familias.setCellWidget(row_idx, 3, btn_container)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar familias: {e}")

    def al_seleccionar_familia(self):
        """
        Evento gatillado al seleccionar una familia de la lista.
        """
        self.table_integrantes.setRowCount(0)

        selected_ranges = self.table_familias.selectedRanges()
        if not selected_ranges:
            self.group_registro_int.setEnabled(False)
            self.actualizar_resumen([])
            return

        row_idx = selected_ranges[0].topRow()
        familia_id_item = self.table_familias.item(row_idx, 0)
        if not familia_id_item:
            self.group_registro_int.setEnabled(False)
            self.actualizar_resumen([])
            return

        familia_id = int(familia_id_item.text())
        self.group_registro_int.setEnabled(True)

        try:
            integrantes = FamiliaController.obtener_integrantes_por_familia(familia_id)
            for i in integrantes:
                r_idx = self.table_integrantes.rowCount()
                self.table_integrantes.insertRow(r_idx)
                self.table_integrantes.setItem(r_idx, 0, QTableWidgetItem(str(i["id"])))
                self.table_integrantes.setItem(r_idx, 1, QTableWidgetItem(i["nombres"]))
                self.table_integrantes.setItem(r_idx, 2, QTableWidgetItem(i["apellidos"]))
                self.table_integrantes.setItem(r_idx, 3, QTableWidgetItem(str(i["edad"])))
                self.table_integrantes.setItem(r_idx, 4, QTableWidgetItem(i["sexo"]))
                self.table_integrantes.setItem(r_idx, 5, QTableWidgetItem(i["condicion_especial"]))

                # Botones de Acción: Editar y Eliminar para Integrante
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                btn_layout.setSpacing(4)

                btn_editar = QPushButton("Editar")
                btn_editar.setStyleSheet("background-color: #F57C00; color: white; padding: 2px 6px; font-weight: bold;")
                btn_editar.clicked.connect(lambda checked, i=i: self.editar_integrante_modal(i))

                btn_eliminar = QPushButton("Eliminar")
                btn_eliminar.setStyleSheet("background-color: #D32F2F; color: white; padding: 2px 6px; font-weight: bold;")
                btn_eliminar.clicked.connect(lambda checked, i_id=i["id"]: self.eliminar_integrante(i_id))

                btn_layout.addWidget(btn_editar)
                btn_layout.addWidget(btn_eliminar)
                self.table_integrantes.setCellWidget(r_idx, 6, btn_container)

            self.actualizar_resumen(integrantes)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar integrantes: {e}")

    def editar_familia_modal(self, familia):
        """
        Abre el modal para editar la familia.
        """
        dialog = EditarFamiliaDialog(familia, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.al_seleccionar_refugio()

    def eliminar_familia(self, familia_id):
        """
        Elimina la familia seleccionada después de una confirmación.
        """
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            "¿Está seguro de que desea eliminar esta familia? Se eliminarán de forma permanente sus integrantes y solicitudes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                FamiliaController.eliminar_familia(familia_id)
                QMessageBox.information(self, "Éxito", "La familia ha sido eliminada correctamente.")
                self.al_seleccionar_refugio()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar la familia: {e}")

    def editar_integrante_modal(self, integrante):
        """
        Abre el modal para editar el integrante.
        """
        dialog = EditarIntegranteDialog(integrante, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.al_seleccionar_familia()

    def eliminar_integrante(self, integrante_id):
        """
        Elimina el integrante seleccionado después de una confirmación.
        """
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            "¿Está seguro de que desea eliminar a este integrante de la familia?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                FamiliaController.eliminar_integrante(integrante_id)
                QMessageBox.information(self, "Éxito", "El integrante ha sido eliminado correctamente.")
                self.al_seleccionar_familia()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar al integrante: {e}")

    def actualizar_resumen(self, integrantes):
        """
        Calcula y actualiza el panel visual del resumen de integrantes por edad.
        """
        resumen = FamiliaController.calcular_resumen_edad(integrantes)
        self.lbl_resumen_total.setText(f"Total Integrantes: {resumen['total']}")
        self.lbl_resumen_detalles.setText(
            f"Niños (<18): {resumen['ninos']}  |  "
            f"Adultos (18-59): {resumen['adultos']}  |  "
            f"Adultos Mayores (60+): {resumen['adultos_mayores']}"
        )

    def guardar_familia(self):
        """
        Registra una nueva familia para el refugio seleccionado.
        """
        refugio_id = self.combo_refugios.currentData()
        if refugio_id is None:
            QMessageBox.warning(self, "Atención", "Debe seleccionar un Refugio para registrar la familia.")
            return

        codigo = self.txt_codigo_fam.text().strip()
        nombre = self.txt_nombre_fam.text().strip()

        if not codigo or not nombre:
            QMessageBox.warning(self, "Campos Requeridos", "Todos los campos con asterisco (*) son obligatorios.")
            return

        try:
            FamiliaController.crear_familia(refugio_id, codigo, nombre)
            QMessageBox.information(self, "Éxito", "Familia registrada correctamente.")
            self.txt_codigo_fam.clear()
            self.txt_nombre_fam.clear()
            self.al_seleccionar_refugio()
        except ValueError as ve:
            QMessageBox.warning(self, "Validación", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la familia: {e}")

    def guardar_integrante(self):
        """
        Agrega un integrante a la familia seleccionada.
        """
        selected_ranges = self.table_familias.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "Atención", "Seleccione primero una familia de la tabla.")
            return

        row_idx = selected_ranges[0].topRow()
        familia_id = int(self.table_familias.item(row_idx, 0).text())

        nombres = self.txt_int_nombres.text().strip()
        apellidos = self.txt_int_apellidos.text().strip()
        edad = self.spin_int_edad.value()
        sexo = "M" if self.radio_m.isChecked() else "F"
        condicion = self.txt_int_condicion.text().strip()

        if not nombres or not apellidos:
            QMessageBox.warning(self, "Campos Requeridos", "Los nombres y apellidos son obligatorios.")
            return

        try:
            FamiliaController.agregar_integrante(familia_id, nombres, apellidos, edad, sexo, condicion)
            QMessageBox.information(self, "Éxito", "Integrante agregado correctamente.")

            # Limpiar campos de integrante
            self.txt_int_nombres.clear()
            self.txt_int_apellidos.clear()
            self.spin_int_edad.setValue(30)
            self.radio_m.setChecked(True)
            self.txt_int_condicion.clear()

            # Recargar integrantes y resumen
            self.al_seleccionar_familia()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el integrante: {e}")
