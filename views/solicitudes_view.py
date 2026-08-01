from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QMessageBox, QGroupBox, QComboBox, QDoubleSpinBox,
    QDialog, QSplitter, QTextEdit, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from controllers.refugio_controller import RefugioController
from controllers.familia_controller import FamiliaController
from controllers.inventario_controller import InventarioController
from controllers.solicitud_controller import SolicitudController


class CrearSemanaDialog(QDialog):
    """
    Modal para crear una nueva semana de control.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nueva Semana de Control")
        self.resize(400, 250)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        group = QGroupBox("Datos de la Semana")
        form_layout = QFormLayout(group)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej. Semana 2 - Agosto 2026")

        self.txt_inicio = QLineEdit()
        self.txt_inicio.setPlaceholderText("AAAA-MM-DD")

        self.txt_fin = QLineEdit()
        self.txt_fin.setPlaceholderText("AAAA-MM-DD")

        form_layout.addRow("Nombre Semana *:", self.txt_nombre)
        form_layout.addRow("Fecha Inicio * (AAAA-MM-DD):", self.txt_inicio)
        form_layout.addRow("Fecha Fin * (AAAA-MM-DD):", self.txt_fin)

        layout.addWidget(group)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("Crear Semana")
        self.btn_guardar.setStyleSheet("background-color: #00897B; color: white; font-weight: bold; padding: 6px;")
        self.btn_guardar.clicked.connect(self.guardar_semana)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("background-color: #90A4AE; color: white; font-weight: bold; padding: 6px;")
        self.btn_cancelar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

    def guardar_semana(self):
        nombre = self.txt_nombre.text().strip()
        inicio = self.txt_inicio.text().strip()
        fin = self.txt_fin.text().strip()

        if not nombre or not inicio or not fin:
            QMessageBox.warning(self, "Campos Requeridos", "Todos los campos con (*) son obligatorios.")
            return

        try:
            SolicitudController.crear_semana(nombre, inicio, fin)
            QMessageBox.information(self, "Éxito", f"Semana '{nombre}' creada con éxito.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear la semana: {e}")


class SolicitudesView(QWidget):
    """
    Vista del Módulo de Solicitudes Semanales con Registro Híbrido e Historial de la Semana.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items_pedido = []  # Lista local de ítems agregados al pedido/solicitud en borrador
        self.productos_inventario = [] # Lista de productos para la búsqueda rápida
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # ------------------ TOP PANEL (COMÚN): GESTIÓN DE SEMANA ACTIVA ------------------
        top_group = QGroupBox("Gestión de Período Activo")
        top_layout = QHBoxLayout(top_group)

        # Selector de Semana
        top_layout.addWidget(QLabel("Semana Activa *:"))
        self.combo_semana = QComboBox()
        self.combo_semana.setMinimumWidth(250)
        self.combo_semana.currentIndexChanged.connect(self.al_cambiar_semana_activa)
        top_layout.addWidget(self.combo_semana)

        self.btn_nueva_semana = QPushButton("Nueva Semana")
        self.btn_nueva_semana.setStyleSheet("background-color: #00796B; color: white; font-weight: bold; padding: 6px 10px;")
        self.btn_nueva_semana.clicked.connect(self.abrir_crear_semana)
        top_layout.addWidget(self.btn_nueva_semana)

        top_layout.addStretch()
        main_layout.addWidget(top_group)

        # ------------------ TAB CONTROL: REGISTRO E HISTORIAL ------------------
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ================= TAB 1: REGISTRAR SOLICITUD =================
        tab_registro = QWidget()
        tab_registro_layout = QVBoxLayout(tab_registro)

        # Selector de Refugio y Familia
        header_group = QGroupBox("Cabecera del Pedido")
        header_layout = QHBoxLayout(header_group)

        header_layout.addWidget(QLabel("Refugio *:"))
        self.combo_refugio = QComboBox()
        self.combo_refugio.setMinimumWidth(200)
        self.combo_refugio.currentIndexChanged.connect(self.al_cambiar_refugio)
        header_layout.addWidget(self.combo_refugio)

        header_layout.addWidget(QLabel("Familia *:"))
        self.combo_familia = QComboBox()
        self.combo_familia.setMinimumWidth(200)
        header_layout.addWidget(self.combo_familia)

        header_layout.addStretch()
        tab_registro_layout.addWidget(header_group)

        # Splitter principal para Registro
        splitter = QSplitter(Qt.Orientation.Horizontal)
        tab_registro_layout.addWidget(splitter)

        # Sub-sección Izquierda: Buscador Híbrido
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        search_group = QGroupBox("Buscador / Cargador Híbrido de Productos")
        search_form = QFormLayout(search_group)

        # Selector de producto de inventario
        self.combo_producto_inv = QComboBox()
        self.combo_producto_inv.setEditable(True)
        self.combo_producto_inv.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo_producto_inv.currentIndexChanged.connect(self.al_seleccionar_producto_inv)
        search_form.addRow("Buscar en Inventario:", self.combo_producto_inv)

        # Info de Stock
        self.lbl_stock_info = QLabel("Seleccione un producto para ver disponibilidad...")
        self.lbl_stock_info.setStyleSheet("font-weight: bold; color: #0D47A1;")
        search_form.addRow("Stock Disponible:", self.lbl_stock_info)

        # Botón/Campo de Opción Libre (Producto Manual)
        self.txt_manual_nombre = QLineEdit()
        self.txt_manual_nombre.setPlaceholderText("Nombre del producto libre/no registrado")
        search_form.addRow("Producto Libre (Manual):", self.txt_manual_nombre)

        # Cantidad Solicitada
        self.spin_cantidad = QDoubleSpinBox()
        self.spin_cantidad.setRange(0.01, 10000.0)
        self.spin_cantidad.setDecimals(2)
        self.spin_cantidad.setValue(1.0)
        search_form.addRow("Cantidad Solicitada *:", self.spin_cantidad)

        # Unidad de medida
        self.combo_unidad_medida = QComboBox()
        self.combo_unidad_medida.addItems(["kg", "litros", "unidades"])
        search_form.addRow("Unidad de Medida *:", self.combo_unidad_medida)

        # Botón para Agregar al Resumen
        self.btn_agregar_item = QPushButton("Agregar al Pedido")
        self.btn_agregar_item.setStyleSheet("background-color: #0288D1; color: white; font-weight: bold; padding: 8px;")
        self.btn_agregar_item.clicked.connect(self.agregar_item_pedido)
        search_form.addRow("", self.btn_agregar_item)

        left_layout.addWidget(search_group)

        # Campo Observaciones
        obs_group = QGroupBox("Observaciones del Pedido (Opcional)")
        obs_layout = QVBoxLayout(obs_group)
        self.txt_observaciones = QTextEdit()
        self.txt_observaciones.setMaximumHeight(100)
        obs_layout.addWidget(self.txt_observaciones)
        left_layout.addWidget(obs_group)

        left_layout.addStretch()
        splitter.addWidget(left_widget)

        # Sub-sección Derecha: Tabla Resumen
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        summary_group = QGroupBox("Resumen del Pedido (Borrador Actual)")
        summary_layout = QVBoxLayout(summary_group)

        self.table_pedido = QTableWidget()
        self.table_pedido.setColumnCount(6)
        self.table_pedido.setHorizontalHeaderLabels([
            "Producto", "Origen/Estado", "Cantidad", "Unidad", "ID Producto", "Acciones"
        ])
        self.table_pedido.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_pedido.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_pedido.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        summary_layout.addWidget(self.table_pedido)

        # Acciones de Confirmación
        btn_action_layout = QHBoxLayout()
        self.btn_confirmar_pedido = QPushButton("Confirmar y Guardar Pedido")
        self.btn_confirmar_pedido.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 10px 15px; font-size: 13px;")
        self.btn_confirmar_pedido.clicked.connect(self.confirmar_guardar_pedido)

        self.btn_cancelar_pedido = QPushButton("Limpiar Pedido")
        self.btn_cancelar_pedido.setStyleSheet("background-color: #C62828; color: white; font-weight: bold; padding: 10px 15px; font-size: 13px;")
        self.btn_cancelar_pedido.clicked.connect(self.limpiar_pedido_completo)

        btn_action_layout.addWidget(self.btn_confirmar_pedido)
        btn_action_layout.addWidget(self.btn_cancelar_pedido)
        summary_layout.addLayout(btn_action_layout)

        right_layout.addWidget(summary_group)
        splitter.addWidget(right_widget)

        splitter.setSizes([400, 600])
        self.tabs.addTab(tab_registro, "Registrar Solicitud")

        # ================= TAB 2: HISTORIAL DE SOLICITUDES =================
        tab_historial = QWidget()
        tab_historial_layout = QVBoxLayout(tab_historial)

        splitter_historial = QSplitter(Qt.Orientation.Horizontal)
        tab_historial_layout.addWidget(splitter_historial)

        # Historial Lado Izquierdo: Lista de solicitudes de la semana
        hist_left_container = QWidget()
        hist_left_layout = QVBoxLayout(hist_left_container)
        hist_left_layout.setContentsMargins(0, 0, 0, 0)

        hist_left_group = QGroupBox("Solicitudes de la Semana Activa")
        hist_left_group_layout = QVBoxLayout(hist_left_group)

        self.table_historial = QTableWidget()
        self.table_historial.setColumnCount(5)
        self.table_historial.setHorizontalHeaderLabels([
            "ID", "Código Fam.", "Familia", "Fecha Registro", "Acciones"
        ])
        self.table_historial.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_historial.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_historial.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_historial.itemSelectionChanged.connect(self.al_seleccionar_solicitud_historial)

        hist_left_group_layout.addWidget(self.table_historial)
        hist_left_layout.addWidget(hist_left_group)
        splitter_historial.addWidget(hist_left_container)

        # Historial Lado Derecho: Detalles de la solicitud seleccionada
        hist_right_container = QWidget()
        hist_right_layout = QVBoxLayout(hist_right_container)
        hist_right_layout.setContentsMargins(0, 0, 0, 0)

        hist_right_group = QGroupBox("Detalles de Solicitud Seleccionada")
        hist_right_group_layout = QVBoxLayout(hist_right_group)

        self.table_historial_detalles = QTableWidget()
        self.table_historial_detalles.setColumnCount(4)
        self.table_historial_detalles.setHorizontalHeaderLabels([
            "Producto/Insumo", "Cantidad", "Unidad", "Origen"
        ])
        self.table_historial_detalles.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_historial_detalles.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_historial_detalles.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        hist_right_group_layout.addWidget(self.table_historial_detalles)
        hist_right_layout.addWidget(hist_right_group)
        splitter_historial.addWidget(hist_right_container)

        splitter_historial.setSizes([550, 450])
        self.tabs.addTab(tab_historial, "Historial de Solicitudes de la Semana")

        # Cargas iniciales de datos
        self.cargar_semanas()
        self.cargar_refugios()
        self.cargar_productos_inventario()

    # ------------------ CARGAS Y EVENTOS DE SELECTORES ------------------

    def cargar_semanas(self):
        """
        Llena el combo de semanas activas.
        """
        self.combo_semana.blockSignals(True)
        self.combo_semana.clear()
        try:
            semanas = SolicitudController.obtener_todas_semanas()
            for sem in semanas:
                self.combo_semana.addItem(sem["nombre_semana"], sem["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar semanas: {e}")
        finally:
            self.combo_semana.blockSignals(False)
            self.cargar_historial_solicitudes()

    def al_cambiar_semana_activa(self):
        """
        Gatillado al cambiar el período/semana seleccionada.
        """
        self.cargar_historial_solicitudes()

    def abrir_crear_semana(self):
        """
        Abre el diálogo modal para crear una nueva semana.
        """
        dialog = CrearSemanaDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.cargar_semanas()

    def cargar_refugios(self):
        """
        Llena el combo de refugios disponibles.
        """
        self.combo_refugio.blockSignals(True)
        self.combo_refugio.clear()
        self.combo_familia.clear()
        try:
            refugios = RefugioController.obtener_todos()
            self.combo_refugio.addItem("-- Seleccione un Refugio --", None)
            for ref in refugios:
                self.combo_refugio.addItem(ref["nombre"], ref["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar refugios: {e}")
        finally:
            self.combo_refugio.blockSignals(False)

    def al_cambiar_refugio(self):
        """
        Carga las familias asociadas al refugio seleccionado de forma dinámica.
        """
        ref_id = self.combo_refugios_data = self.combo_refugio.currentData()
        self.combo_familia.clear()
        if not ref_id:
            return

        try:
            familias = FamiliaController.obtener_familias_por_refugio(ref_id)
            if not familias:
                self.combo_familia.addItem("No hay familias registradas", None)
            else:
                self.combo_familia.addItem("-- Seleccione una Familia --", None)
                for fam in familias:
                    display_text = f"{fam['codigo_numero']} - {fam['nombre_representativo']}"
                    self.combo_familia.addItem(display_text, fam["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar familias: {e}")

    def cargar_productos_inventario(self):
        """
        Llena el combo de búsqueda rápida de inventario con todos los productos disponibles.
        """
        self.combo_producto_inv.blockSignals(True)
        self.combo_producto_inv.clear()
        try:
            self.productos_inventario = InventarioController.obtener_todos_productos()
            self.combo_producto_inv.addItem("-- Buscar Producto del Inventario --", None)
            for prod in self.productos_inventario:
                txt = f"{prod['nombre']} ({prod['empaque_unidad']}) - Stock: {prod['stock_unidades']:.2f} {prod['unidad_medida']}"
                self.combo_producto_inv.addItem(txt, prod["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar productos en el buscador: {e}")
        finally:
            self.combo_producto_inv.blockSignals(False)

    def al_seleccionar_producto_inv(self):
        """
        Muestra la disponibilidad de stock y autoselecciona la unidad de medida al elegir un producto.
        """
        prod_id = self.combo_producto_inv.currentData()
        if not prod_id:
            self.lbl_stock_info.setText("Seleccione un producto para ver disponibilidad...")
            self.lbl_stock_info.setStyleSheet("font-weight: bold; color: #0D47A1;")
            return

        prod = next((p for p in self.productos_inventario if p["id"] == prod_id), None)
        if prod:
            self.lbl_stock_info.setText(
                f"Disponible: {prod['stock_unidades']:.2f} {prod['unidad_medida']} | "
                f"Presentación: {prod['empaque_unidad']} ({prod['tamano_unidad_peso']:.2f} {prod['unidad_medida']})"
            )
            self.lbl_stock_info.setStyleSheet("font-weight: bold; color: #2E7D32;")

            idx = self.combo_unidad_medida.findText(prod["unidad_medida"])
            if idx != -1:
                self.combo_unidad_medida.setCurrentIndex(idx)

            self.txt_manual_nombre.clear()

    # ------------------ BORRADOR DE PEDIDO (INTERFAZ LOCAL) ------------------

    def agregar_item_pedido(self):
        """
        Agrega un producto (de inventario o manual) al borrador de la tabla resumen.
        """
        prod_id = self.combo_producto_inv.currentData()
        nombre_manual = self.txt_manual_nombre.text().strip()
        cantidad = self.spin_cantidad.value()
        unidad = self.combo_unidad_medida.currentText()

        if cantidad <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor que cero.")
            return

        if not prod_id and not nombre_manual:
            QMessageBox.warning(
                self, "Búsqueda Híbrida",
                "Debe seleccionar un producto del inventario O ingresar el nombre de un Producto Libre (Manual)."
            )
            return

        if prod_id:
            prod = next((p for p in self.productos_inventario if p["id"] == prod_id), None)
            if not prod:
                QMessageBox.warning(self, "Error", "El producto de inventario seleccionado es inválido.")
                return

            duplicado = next((i for i in self.items_pedido if i["producto_id"] == prod_id), None)
            if duplicado:
                nueva_cantidad_acumulada = duplicado["cantidad_solicitada"] + cantidad
                if prod["stock_unidades"] < nueva_cantidad_acumulada:
                    QMessageBox.warning(
                        self, "Stock Insuficiente",
                        f"No hay stock suficiente para acumular. "
                        f"Disponible: {prod['stock_unidades']:.2f}, Acumulado en borrador: {nueva_cantidad_acumulada:.2f}"
                    )
                    return
                duplicado["cantidad_solicitada"] = nueva_cantidad_acumulada
            else:
                if prod["stock_unidades"] < cantidad:
                    QMessageBox.warning(
                        self, "Stock Insuficiente",
                        f"No hay stock suficiente para agregar este producto. "
                        f"Disponible: {prod['stock_unidades']:.2f}, Solicitado: {cantidad:.2f}"
                    )
                    return

                self.items_pedido.append({
                    "producto_id": prod_id,
                    "nombre_visual": prod["nombre"],
                    "nombre_producto_manual": None,
                    "cantidad_solicitada": cantidad,
                    "unidad_medida_solicitada": ... if False else unidad,
                    "en_inventario": True
                })
        else:
            duplicado = next((i for i in self.items_pedido if i["en_inventario"] is False and i["nombre_producto_manual"].lower() == nombre_manual.lower()), None)
            if duplicado:
                duplicado["cantidad_solicitada"] += cantidad
            else:
                self.items_pedido.append({
                    "producto_id": None,
                    "nombre_visual": nombre_manual,
                    "nombre_producto_manual": nombre_manual,
                    "cantidad_solicitada": cantidad,
                    "unidad_medida_solicitada": unidad,
                    "en_inventario": False
                })

        self.combo_producto_inv.setCurrentIndex(0)
        self.txt_manual_nombre.clear()
        self.spin_cantidad.setValue(1.0)
        self.lbl_stock_info.setText("Seleccione un producto para ver disponibilidad...")
        self.lbl_stock_info.setStyleSheet("font-weight: bold; color: #0D47A1;")

        self.actualizar_tabla_resumen()

    def actualizar_tabla_resumen(self):
        """
        Refresca visualmente la tabla que contiene el borrador del pedido.
        """
        self.table_pedido.setRowCount(0)
        for idx, item in enumerate(self.items_pedido):
            row_idx = self.table_pedido.rowCount()
            self.table_pedido.insertRow(row_idx)

            self.table_pedido.setItem(row_idx, 0, QTableWidgetItem(item["nombre_visual"]))

            estado_item = QTableWidgetItem()
            if item["en_inventario"]:
                estado_item.setText("En Inventario")
                estado_item.setForeground(QColor("#2E7D32"))
            else:
                estado_item.setText("[No en Inventario]")
                estado_item.setForeground(QColor("#E65100"))
                estado_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))

            self.table_pedido.setItem(row_idx, 1, estado_item)
            self.table_pedido.setItem(row_idx, 2, QTableWidgetItem(f"{item['cantidad_solicitada']:.2f}"))
            self.table_pedido.setItem(row_idx, 3, QTableWidgetItem(item["unidad_medida_solicitada"]))

            id_val = str(item["producto_id"]) if item["producto_id"] else "Manual"
            self.table_pedido.setItem(row_idx, 4, QTableWidgetItem(id_val))

            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.setStyleSheet("background-color: #E53935; color: white; padding: 2px 5px;")
            btn_eliminar.clicked.connect(lambda checked, idx=idx: self.eliminar_item_borrador(idx))
            self.table_pedido.setCellWidget(row_idx, 5, btn_eliminar)

            if not item["en_inventario"]:
                for col in range(5):
                    self.table_pedido.item(row_idx, col).setBackground(QColor("#FFF3E0"))

    def eliminar_item_borrador(self, index: int):
        """
        Remueve un ítem de la lista local de borrador.
        """
        if 0 <= index < len(self.items_pedido):
            self.items_pedido.pop(index)
            self.actualizar_tabla_resumen()

    def limpiar_pedido_completo(self):
        """
        Limpia todos los borradores y campos del pedido actual.
        """
        self.items_pedido = []
        self.actualizar_tabla_resumen()
        self.txt_observaciones.clear()
        self.combo_producto_inv.setCurrentIndex(0)
        self.txt_manual_nombre.clear()
        self.spin_cantidad.setValue(1.0)
        self.lbl_stock_info.setText("Seleccione un producto para ver disponibilidad...")
        self.lbl_stock_info.setStyleSheet("font-weight: bold; color: #0D47A1;")

    def confirmar_guardar_pedido(self):
        """
        Valida datos generales de cabecera y envía la solicitud al controlador para ejecutar el guardado transaccional.
        """
        semana_id = self.combo_semana.currentData()
        refugio_id = self.combo_refugio.currentData()
        familia_id = self.combo_familia.currentData()
        observaciones = self.txt_observaciones.toPlainText().strip()

        if not semana_id:
            QMessageBox.warning(self, "Cabecera Incompleta", "Debe seleccionar una semana de control activa.")
            return
        if not refugio_id:
            QMessageBox.warning(self, "Cabecera Incompleta", "Debe seleccionar un refugio válido.")
            return
        if not familia_id:
            QMessageBox.warning(self, "Cabecera Incompleta", "Debe seleccionar una familia válida.")
            return
        if not self.items_pedido:
            QMessageBox.warning(self, "Pedido Vacío", "No puede guardar una solicitud sin ítems/productos agregados.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Pedido",
            "¿Está seguro de que desea confirmar y registrar esta solicitud? "
            "Esto descontará automáticamente el stock de los productos que correspondan.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        try:
            solicitud_id = SolicitudController.crear_solicitud_con_detalles(
                semana_id=semana_id,
                familia_id=familia_id,
                observaciones=observaciones,
                items=self.items_pedido
            )

            QMessageBox.information(
                self, "Éxito",
                f"Pedido registrado exitosamente con ID de solicitud: {solicitud_id}. "
                "El stock correspondiente ha sido descontado correctamente."
            )

            self.limpiar_pedido_completo()
            self.cargar_productos_inventario()
            self.cargar_historial_solicitudes()

        except ValueError as ve:
            QMessageBox.warning(self, "Validación de Stock / Error", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Error de Sistema", f"No se pudo guardar la solicitud: {e}")

    # ================= GESTIÓN E HISTORIAL DE SOLICITUDES =================

    def cargar_historial_solicitudes(self):
        """
        Consulta y muestra las solicitudes registradas para la semana activa.
        """
        # Asegurarse de que el widget de historial esté inicializado antes de escribir en él
        if not hasattr(self, 'table_historial'):
            return

        self.table_historial.setRowCount(0)
        self.table_historial_detalles.setRowCount(0)
        semana_id = self.combo_semana.currentData()

        if not semana_id:
            return

        try:
            solicitudes = SolicitudController.obtener_solicitudes_por_semana(semana_id)
            for s in solicitudes:
                row_idx = self.table_historial.rowCount()
                self.table_historial.insertRow(row_idx)

                self.table_historial.setItem(row_idx, 0, QTableWidgetItem(str(s["id"])))
                self.table_historial.setItem(row_idx, 1, QTableWidgetItem(s["codigo_familia"]))
                self.table_historial.setItem(row_idx, 2, QTableWidgetItem(s["nombre_familia"]))
                self.table_historial.setItem(row_idx, 3, QTableWidgetItem(s["fecha_solicitud"]))

                # Botón de Acción: Eliminar Solicitud
                btn_eliminar = QPushButton("Eliminar")
                btn_eliminar.setStyleSheet("background-color: #D32F2F; color: white; padding: 2px 6px; font-weight: bold;")
                btn_eliminar.clicked.connect(lambda checked, s_id=s["id"]: self.eliminar_solicitud_historial(s_id))
                self.table_historial.setCellWidget(row_idx, 4, btn_eliminar)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar historial de solicitudes: {e}")

    def al_seleccionar_solicitud_historial(self):
        """
        Carga y visualiza los productos/detalles para la solicitud seleccionada del historial.
        """
        self.table_historial_detalles.setRowCount(0)
        selected_ranges = self.table_historial.selectedRanges()
        if not selected_ranges:
            return

        row_idx = selected_ranges[0].topRow()
        solicitud_id_item = self.table_historial.item(row_idx, 0)
        if not solicitud_id_item:
            return

        solicitud_id = int(solicitud_id_item.text())

        try:
            detalles = SolicitudController.obtener_detalles_solicitud(solicitud_id)
            for d in detalles:
                r_idx = self.table_historial_detalles.rowCount()
                self.table_historial_detalles.insertRow(r_idx)

                self.table_historial_detalles.setItem(r_idx, 0, QTableWidgetItem(d["nombre_producto"]))
                self.table_historial_detalles.setItem(r_idx, 1, QTableWidgetItem(f"{d['cantidad']:.2f}"))
                self.table_historial_detalles.setItem(r_idx, 2, QTableWidgetItem(d["unidad"]))

                estado_item = QTableWidgetItem("Inventario" if d["en_inventario"] else "Manual")
                if d["en_inventario"]:
                    estado_item.setForeground(QColor("#2E7D32"))
                else:
                    estado_item.setForeground(QColor("#E65100"))
                self.table_historial_detalles.setItem(r_idx, 3, estado_item)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar los detalles del pedido: {e}")

    def eliminar_solicitud_historial(self, solicitud_id: int):
        """
        Elimina la solicitud y revierte el stock del inventario de forma segura.
        """
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            "¿Está seguro de que desea eliminar esta solicitud? "
            "Esto devolverá de manera automática el stock de los productos de inventario que correspondan.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        try:
            SolicitudController.eliminar_solicitud(solicitud_id)
            QMessageBox.information(
                self, "Éxito",
                "La solicitud ha sido eliminada correctamente y las cantidades correspondientes "
                "han sido devueltas al inventario."
            )
            # Recargar tablas y dropdown de inventario
            self.cargar_historial_solicitudes()
            self.cargar_productos_inventario()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar la solicitud: {e}")
