from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QMessageBox, QGroupBox, QComboBox, QDoubleSpinBox,
    QDialog, QSplitter, QTextEdit
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
    Vista del Módulo de Solicitudes Semanales y Descuento Híbrido de Inventario.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items_pedido = []  # Lista local de ítems agregados al pedido/solicitud en borrador
        self.productos_inventario = [] # Lista de productos para la búsqueda rápida
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # ------------------ TOP PANEL: GESTIÓN DE SEMANAS ------------------
        top_group = QGroupBox("Gestión de Período y Cabecera de Pedido")
        top_layout = QHBoxLayout(top_group)

        # Selector de Semana
        top_layout.addWidget(QLabel("Semana Activa *:"))
        self.combo_semana = QComboBox()
        self.combo_semana.setMinimumWidth(220)
        top_layout.addWidget(self.combo_semana)

        self.btn_nueva_semana = QPushButton("Nueva Semana")
        self.btn_nueva_semana.setStyleSheet("background-color: #00796B; color: white; font-weight: bold; padding: 6px 10px;")
        self.btn_nueva_semana.clicked.connect(self.abrir_crear_semana)
        top_layout.addWidget(self.btn_nueva_semana)

        top_layout.addSpacing(20)

        # Selector de Refugio
        top_layout.addWidget(QLabel("Refugio *:"))
        self.combo_refugio = QComboBox()
        self.combo_refugio.setMinimumWidth(200)
        self.combo_refugio.currentIndexChanged.connect(self.al_cambiar_refugio)
        top_layout.addWidget(self.combo_refugio)

        # Selector de Familia
        top_layout.addWidget(QLabel("Familia *:"))
        self.combo_familia = QComboBox()
        self.combo_familia.setMinimumWidth(200)
        top_layout.addWidget(self.combo_familia)

        top_layout.addStretch()
        main_layout.addWidget(top_group)

        # ------------------ SPLITTER PRINCIPAL ------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # =============== SECCIÓN IZQUIERDA: BUSCADOR HÍBRIDO ===============
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

        # =============== SECCIÓN DERECHA: TABLA RESUMEN ===============
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

        # Acciones de Confirmación del Pedido
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

        # Ajuste de tamaño inicial (40% izquierdo, 60% derecho)
        splitter.setSizes([400, 600])

        # Cargas iniciales de datos
        self.cargar_semanas()
        self.cargar_refugios()
        self.cargar_productos_inventario()

    # ------------------ CARGAS Y EVENTOS DE SELECTORES ------------------

    def cargar_semanas(self):
        """
        Llena el combo de semanas activas.
        """
        self.combo_semana.clear()
        try:
            semanas = SolicitudController.obtener_todas_semanas()
            for sem in semanas:
                self.combo_semana.addItem(sem["nombre_semana"], sem["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar semanas: {e}")

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
        ref_id = self.combo_refugio.currentData()
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
                    # Mostrar código y nombre
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
                # Ej: Arroz Premium (Saco de 24 kg) - Stock: 10
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

        # Buscar el producto localmente
        prod = next((p for p in self.productos_inventario if p["id"] == prod_id), None)
        if prod:
            self.lbl_stock_info.setText(
                f"Disponible: {prod['stock_unidades']:.2f} {prod['unidad_medida']} | "
                f"Presentación: {prod['empaque_unidad']} ({prod['tamano_unidad_peso']:.2f} {prod['unidad_medida']})"
            )
            self.lbl_stock_info.setStyleSheet("font-weight: bold; color: #2E7D32;")

            # Autoseleccionar unidad de medida
            idx = self.combo_unidad_medida.findText(prod["unidad_medida"])
            if idx != -1:
                self.combo_unidad_medida.setCurrentIndex(idx)

            # Limpiar campo libre manual por comodidad
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

        # Validaciones preliminares
        if cantidad <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor que cero.")
            return

        if not prod_id and not nombre_manual:
            QMessageBox.warning(
                self, "Búsqueda Híbrida",
                "Debe seleccionar un producto del inventario O ingresar el nombre de un Producto Libre (Manual)."
            )
            return

        # Determinar si viene de inventario o manual
        if prod_id:
            # Viene de inventario
            prod = next((p for p in self.productos_inventario if p["id"] == prod_id), None)
            if not prod:
                QMessageBox.warning(self, "Error", "El producto de inventario seleccionado es inválido.")
                return

            # Verificar si ya está en el borrador actual (evitar duplicados o sumar)
            duplicado = next((i for i in self.items_pedido if i["producto_id"] == prod_id), None)
            if duplicado:
                # Validar stock acumulado
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
                # Validar stock individual
                if prod["stock_unidades"] < cantidad:
                    QMessageBox.warning(
                        self, "Stock Insuficiente",
                        f"No hay stock suficiente para agregar este producto. "
                        f"Disponible: {prod['stock_unidades']:.2f}, Solicitado: {cantidad:.2f}"
                    )
                    return

                # Crear nuevo ítem en el borrador
                self.items_pedido.append({
                    "producto_id": prod_id,
                    "nombre_visual": prod["nombre"],
                    "nombre_producto_manual": None,
                    "cantidad_solicitada": cantidad,
                    "unidad_medida_solicitada": unidad,
                    "en_inventario": True
                })
        else:
            # Producto manual
            # Permitir duplicados por nombre si es que se desea, pero preferible consolidar si coincide exactamente
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

        # Limpiar cargador
        self.combo_producto_inv.setCurrentIndex(0)
        self.txt_manual_nombre.clear()
        self.spin_cantidad.setValue(1.0)
        self.lbl_stock_info.setText("Seleccione un producto para ver disponibilidad...")
        self.lbl_stock_info.setStyleSheet("font-weight: bold; color: #0D47A1;")

        # Renderizar la tabla
        self.actualizar_tabla_resumen()

    def actualizar_tabla_resumen(self):
        """
        Refresca visualmente la tabla que contiene el borrador del pedido.
        Aplica color naranja/amarillo para productos manuales [No en Inventario].
        """
        self.table_pedido.setRowCount(0)
        for idx, item in enumerate(self.items_pedido):
            row_idx = self.table_pedido.rowCount()
            self.table_pedido.insertRow(row_idx)

            # 1. Producto (Nombre Visual)
            self.table_pedido.setItem(row_idx, 0, QTableWidgetItem(item["nombre_visual"]))

            # 2. Origen/Estado con estilo diferenciado
            estado_item = QTableWidgetItem()
            if item["en_inventario"]:
                estado_item.setText("En Inventario")
                estado_item.setForeground(QColor("#2E7D32"))
            else:
                estado_item.setText("[No en Inventario]")
                estado_item.setForeground(QColor("#E65100"))
                estado_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))

            self.table_pedido.setItem(row_idx, 1, estado_item)

            # 3. Cantidad
            self.table_pedido.setItem(row_idx, 2, QTableWidgetItem(f"{item['cantidad_solicitada']:.2f}"))

            # 4. Unidad
            self.table_pedido.setItem(row_idx, 3, QTableWidgetItem(item["unidad_medida_solicitada"]))

            # 5. ID Producto
            id_val = str(item["producto_id"]) if item["producto_id"] else "Manual"
            self.table_pedido.setItem(row_idx, 4, QTableWidgetItem(id_val))

            # 6. Botón Acciones (Eliminar de la fila)
            btn_eliminar = QPushButton("Eliminar")
            btn_eliminar.setStyleSheet("background-color: #E53935; color: white; padding: 2px 5px;")
            # Capturar índice actual usando clausura
            btn_eliminar.clicked.connect(lambda checked, idx=idx: self.eliminar_item_borrador(idx))
            self.table_pedido.setCellWidget(row_idx, 5, btn_eliminar)

            # Si es manual, colorear la fila completa en naranja/amarillo suave
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

    # ------------------ REGISTRO Y GUARDADO DEFINITIVO ------------------

    def confirmar_guardar_pedido(self):
        """
        Valida datos generales de cabecera y envía la solicitud al controlador para
        ejecutar el guardado transaccional.
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

        # Confirmación de confirmación
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
            # Enviar solicitud y detalles a través del controlador transaccional
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

            # Limpiar todo y refrescar catálogo de productos
            self.limpiar_pedido_completo()
            self.cargar_productos_inventario()

        except ValueError as ve:
            QMessageBox.warning(self, "Validación de Stock / Error", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Error de Sistema", f"No se pudo guardar la solicitud: {e}")
