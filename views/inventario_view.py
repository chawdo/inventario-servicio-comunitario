from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFormLayout, QMessageBox, QGroupBox, QComboBox, QDoubleSpinBox,
    QDialog, QSplitter, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from controllers.inventario_controller import InventarioController


class CategoriasDialog(QDialog):
    """
    Modal para gestionar (crear y listar) las categorías de productos.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestionar Categorías")
        self.resize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Formulario de Registro
        group_registro = QGroupBox("Registrar Nueva Categoría")
        form_layout = QFormLayout(group_registro)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej. Alimentos, Higiene, Medicinas")
        self.txt_descripcion = QLineEdit()
        self.txt_descripcion.setPlaceholderText("Descripción opcional de la categoría")

        form_layout.addRow("Nombre *:", self.txt_nombre)
        form_layout.addRow("Descripción:", self.txt_descripcion)

        self.btn_guardar = QPushButton("Guardar Categoría")
        self.btn_guardar.setStyleSheet("background-color: #00897B; color: white; font-weight: bold;")
        self.btn_guardar.clicked.connect(self.guardar_categoria)
        form_layout.addRow("", self.btn_guardar)

        layout.addWidget(group_registro)

        # Tabla de Categorías Registradas
        lbl_lista = QLabel("Categorías Registradas:")
        lbl_lista.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_lista)

        self.table_categorias = QTableWidget()
        self.table_categorias.setColumnCount(3)
        self.table_categorias.setHorizontalHeaderLabels(["ID", "Nombre", "Descripción"])
        self.table_categorias.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_categorias.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_categorias.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table_categorias)

        self.cargar_categorias()

    def cargar_categorias(self):
        self.table_categorias.setRowCount(0)
        try:
            categorias = InventarioController.obtener_todas_categorias()
            for cat in categorias:
                row_idx = self.table_categorias.rowCount()
                self.table_categorias.insertRow(row_idx)
                self.table_categorias.setItem(row_idx, 0, QTableWidgetItem(str(cat["id"])))
                self.table_categorias.setItem(row_idx, 1, QTableWidgetItem(cat["nombre"]))
                self.table_categorias.setItem(row_idx, 2, QTableWidgetItem(cat["descripcion"]))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar categorías: {e}")

    def guardar_categoria(self):
        nombre = self.txt_nombre.text().strip()
        descripcion = self.txt_descripcion.text().strip()

        if not nombre:
            QMessageBox.warning(self, "Campos Requeridos", "El nombre de la categoría es obligatorio.")
            return

        try:
            InventarioController.crear_categoria(nombre, descripcion)
            QMessageBox.information(self, "Éxito", f"Categoría '{nombre}' registrada con éxito.")
            self.txt_nombre.clear()
            self.txt_descripcion.clear()
            self.cargar_categorias()
        except ValueError as ve:
            QMessageBox.warning(self, "Validación", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la categoría: {e}")


class InventarioView(QWidget):
    """
    Vista del Módulo de Inventario Global y Categorías.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.id_producto_seleccionado = None  # Almacena el ID cuando se está editando
        self.init_ui()

    def init_ui(self):
        # Layout vertical principal
        main_layout = QVBoxLayout(self)

        # ------------------ TOP PANEL: ACCIONES GLOBAL ------------------
        top_layout = QHBoxLayout()
        lbl_modulo = QLabel("Módulo de Inventario Global")
        lbl_modulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl_modulo.setStyleSheet("color: #37474F;")

        self.btn_gestionar_categorias = QPushButton("Gestionar Categorías")
        self.btn_gestionar_categorias.setStyleSheet(
            "background-color: #00796B; color: white; font-weight: bold; padding: 8px 12px;"
        )
        self.btn_gestionar_categorias.clicked.connect(self.abrir_gestion_categorias)

        self.btn_refrescar = QPushButton("Actualizar Inventario")
        self.btn_refrescar.setStyleSheet(
            "background-color: #78909C; color: white; font-weight: bold; padding: 8px 12px;"
        )
        self.btn_refrescar.clicked.connect(self.cargar_inventario)

        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.setStyleSheet(
            "background-color: #2E7D32; color: white; font-weight: bold; padding: 8px 12px;"
        )
        self.btn_exportar.clicked.connect(self.exportar_excel)

        top_layout.addWidget(lbl_modulo)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_gestionar_categorias)
        top_layout.addWidget(self.btn_refrescar)
        top_layout.addWidget(self.btn_exportar)
        main_layout.addLayout(top_layout)

        # ------------------ SPLITTER PRINCIPAL ------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # =============== SUB-SECCIÓN IZQUIERDA: LISTA DE PRODUCTOS ===============
        widget_tabla = QWidget()
        layout_tabla = QVBoxLayout(widget_tabla)
        layout_tabla.setContentsMargins(0, 0, 0, 0)

        lbl_tabla = QLabel("Inventario Global:")
        lbl_tabla.setStyleSheet("font-weight: bold; font-size: 13px; color: #263238;")
        layout_tabla.addWidget(lbl_tabla)

        self.table_inventario = QTableWidget()
        self.table_inventario.setColumnCount(9)
        self.table_inventario.setHorizontalHeaderLabels([
            "ID", "Categoría", "Producto", "Presentación",
            "Tamaño/Peso Unidad", "Unidad", "Stock Disponible",
            "Precio Unidad", "Precio Kg/L"
        ])
        self.table_inventario.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_inventario.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_inventario.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_inventario.itemSelectionChanged.connect(self.al_seleccionar_producto)

        layout_tabla.addWidget(self.table_inventario)
        splitter.addWidget(widget_tabla)

        # =============== SUB-SECCIÓN DERECHA: REGISTRO / EDICIÓN ===============
        widget_formulario = QWidget()
        layout_formulario = QVBoxLayout(widget_formulario)
        layout_formulario.setContentsMargins(0, 0, 0, 0)

        self.group_producto = QGroupBox("Registrar Nuevo Producto")
        form_layout = QFormLayout(self.group_producto)

        # Campos de Formulario
        self.combo_categorias = QComboBox()

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej. Arroz Premium")

        self.txt_empaque = QLineEdit()
        self.txt_empaque.setPlaceholderText("Ej. Saco, Caja, Botella")

        # Configuración de los Spinboxes numéricos
        self.spin_tamano = QDoubleSpinBox()
        self.spin_tamano.setRange(0.01, 10000.0)
        self.spin_tamano.setValue(1.0)
        self.spin_tamano.setDecimals(2)
        self.spin_tamano.valueChanged.connect(self.calcular_precio_unitario_equivalente)

        self.combo_unidades = QComboBox()
        self.combo_unidades.addItems(["kg", "litros", "unidades"])

        self.spin_stock = QDoubleSpinBox()
        self.spin_stock.setRange(0.0, 100000.0)
        self.spin_stock.setValue(0.0)
        self.spin_stock.setDecimals(2)

        self.spin_precio_unidad = QDoubleSpinBox()
        self.spin_precio_unidad.setRange(0.0, 100000.0)
        self.spin_precio_unidad.setValue(0.0)
        self.spin_precio_unidad.setDecimals(2)
        self.spin_precio_unidad.valueChanged.connect(self.calcular_precio_unitario_equivalente)

        # Label para mostrar el cálculo automático de precio por kg/litro en tiempo real
        self.lbl_precio_kilo_litro = QLabel("0.00")
        self.lbl_precio_kilo_litro.setStyleSheet("font-weight: bold; color: #1B5E20; font-size: 14px;")

        # Agregar elementos al Formulario
        form_layout.addRow("Categoría *:", self.combo_categorias)
        form_layout.addRow("Nombre del Producto *:", self.txt_nombre)
        form_layout.addRow("Empaque/Presentación *:", self.txt_empaque)
        form_layout.addRow("Tamaño/Peso Unidad *:", self.spin_tamano)
        form_layout.addRow("Unidad de Medida *:", self.combo_unidades)
        form_layout.addRow("Stock Inicial/Disponible *:", self.spin_stock)
        form_layout.addRow("Precio por Unidad *:", self.spin_precio_unidad)
        form_layout.addRow("Precio Calculado por Kg/Litro:", self.lbl_precio_kilo_litro)

        # Botón de Guardar / Modificar
        self.btn_guardar_producto = QPushButton("Guardar Producto")
        self.btn_guardar_producto.setStyleSheet(
            "background-color: #0288D1; color: white; font-weight: bold; padding: 8px;"
        )
        self.btn_guardar_producto.clicked.connect(self.guardar_producto)
        form_layout.addRow("", self.btn_guardar_producto)

        # Botón para Limpiar Selección / Volver a modo de registro
        self.btn_limpiar_seleccion = QPushButton("Limpiar Selección")
        self.btn_limpiar_seleccion.setStyleSheet(
            "background-color: #90A4AE; color: white; font-weight: bold; padding: 6px;"
        )
        self.btn_limpiar_seleccion.clicked.connect(self.limpiar_seleccion)
        form_layout.addRow("", self.btn_limpiar_seleccion)

        layout_formulario.addWidget(self.group_producto)
        layout_formulario.addStretch()
        splitter.addWidget(widget_formulario)

        # Establecer tamaños iniciales del splitter (65% tabla, 35% formulario)
        splitter.setSizes([650, 350])

        # Cargas iniciales
        self.cargar_categorias_combo()
        self.cargar_inventario()

    # ------------------ OPERACIONES Y ACCIONES UI ------------------

    def abrir_gestion_categorias(self):
        """
        Abre el modal de gestión de categorías.
        Al cerrarse, actualiza el combo de categorías por si se agregó alguna.
        """
        dialog = CategoriasDialog(self)
        dialog.exec()
        self.cargar_categorias_combo()

    def cargar_categorias_combo(self):
        """
        Carga las categorías existentes en el combo dropdown del formulario.
        """
        self.combo_categorias.blockSignals(True)
        self.combo_categorias.clear()
        try:
            categorias = InventarioController.obtener_todas_categorias()
            for cat in categorias:
                self.combo_categorias.addItem(cat["nombre"], cat["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar categorías en formulario: {e}")
        finally:
            self.combo_categorias.blockSignals(False)

    def calcular_precio_unitario_equivalente(self):
        """
        Calcula de forma automática y muestra el precio por kilogramo o litro.
        """
        precio = self.spin_precio_unidad.value()
        tamano = self.spin_tamano.value()

        if tamano > 0:
            calculado = precio / tamano
            self.lbl_precio_kilo_litro.setText(f"{calculado:.2f}")
        else:
            self.lbl_precio_kilo_litro.setText("0.00")

    def cargar_inventario(self):
        """
        Llena la tabla de inventario global desde la base de datos.
        Aplica color de alerta a productos con bajo stock.
        """
        self.table_inventario.setRowCount(0)
        try:
            productos = InventarioController.obtener_todos_productos()
            for prod in productos:
                row_idx = self.table_inventario.rowCount()
                self.table_inventario.insertRow(row_idx)

                # Celdas con datos del producto
                self.table_inventario.setItem(row_idx, 0, QTableWidgetItem(str(prod["id"])))
                self.table_inventario.setItem(row_idx, 1, QTableWidgetItem(prod["categoria_nombre"]))
                self.table_inventario.setItem(row_idx, 2, QTableWidgetItem(prod["nombre"]))
                self.table_inventario.setItem(row_idx, 3, QTableWidgetItem(prod["empaque_unidad"]))
                self.table_inventario.setItem(row_idx, 4, QTableWidgetItem(f"{prod['tamano_unidad_peso']:.2f}"))
                self.table_inventario.setItem(row_idx, 5, QTableWidgetItem(prod["unidad_medida"]))

                # Formatear stock
                stock_item = QTableWidgetItem(f"{prod['stock_unidades']:.2f}")
                self.table_inventario.setItem(row_idx, 6, stock_item)

                self.table_inventario.setItem(row_idx, 7, QTableWidgetItem(f"{prod['precio_unidad']:.2f}"))
                self.table_inventario.setItem(row_idx, 8, QTableWidgetItem(f"{prod['precio_kilo_litro']:.2f}"))

                # Resaltar de acuerdo al nivel de stock
                stock = prod["stock_unidades"]
                if stock == 0:
                    # Sin stock: color de fondo rojo claro o texto en negrita rojo oscuro
                    for col in range(9):
                        self.table_inventario.item(row_idx, col).setForeground(QColor("#C62828"))
                        self.table_inventario.item(row_idx, col).setBackground(QColor("#FFEBEE"))
                elif stock <= 3.0:
                    # Stock bajo: color de fondo amarillo claro
                    for col in range(9):
                        self.table_inventario.item(row_idx, col).setForeground(QColor("#EF6C00"))
                        self.table_inventario.item(row_idx, col).setBackground(QColor("#FFF3E0"))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar inventario: {e}")

    def al_seleccionar_producto(self):
        """
        Carga los datos del producto seleccionado en el formulario para poder editarlo.
        """
        selected_ranges = self.table_inventario.selectedRanges()
        if not selected_ranges:
            return

        row_idx = selected_ranges[0].topRow()
        id_item = self.table_inventario.item(row_idx, 0)
        if not id_item:
            return

        self.id_producto_seleccionado = int(id_item.text())

        # Configurar formulario en modo Edición
        self.group_producto.setTitle("Editar Producto Seleccionado")
        self.btn_guardar_producto.setText("Modificar Producto")
        self.btn_guardar_producto.setStyleSheet(
            "background-color: #E65100; color: white; font-weight: bold; padding: 8px;"
        )

        try:
            # Buscar el producto entre los existentes de la base de datos
            productos = InventarioController.obtener_todos_productos()
            producto = next((p for p in productos if p["id"] == self.id_producto_seleccionado), None)

            if producto:
                # Seleccionar categoría correspondiente
                idx_cat = self.combo_categorias.findData(producto["categoria_id"])
                if idx_cat != -1:
                    self.combo_categorias.setCurrentIndex(idx_cat)

                self.txt_nombre.setText(producto["nombre"])
                self.txt_empaque.setText(producto["empaque_unidad"])
                self.spin_tamano.setValue(producto["tamano_unidad_peso"])

                idx_uni = self.combo_unidades.findText(producto["unidad_medida"])
                if idx_uni != -1:
                    self.combo_unidades.setCurrentIndex(idx_uni)

                self.spin_stock.setValue(producto["stock_unidades"])
                self.spin_precio_unidad.setValue(producto["precio_unidad"])

                self.calcular_precio_unitario_equivalente()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos del producto para edición: {e}")

    def limpiar_seleccion(self):
        """
        Limpia el formulario y restablece el estado de registro nuevo.
        """
        self.id_producto_seleccionado = None
        self.table_inventario.clearSelection()

        # Configurar formulario en modo Registro
        self.group_producto.setTitle("Registrar Nuevo Producto")
        self.btn_guardar_producto.setText("Guardar Producto")
        self.btn_guardar_producto.setStyleSheet(
            "background-color: #0288D1; color: white; font-weight: bold; padding: 8px;"
        )

        # Restablecer campos
        if self.combo_categorias.count() > 0:
            self.combo_categorias.setCurrentIndex(0)
        self.txt_nombre.clear()
        self.txt_empaque.clear()
        self.spin_tamano.setValue(1.0)
        self.combo_unidades.setCurrentIndex(0)
        self.spin_stock.setValue(0.0)
        self.spin_precio_unidad.setValue(0.0)
        self.lbl_precio_kilo_litro.setText("0.00")

    def guardar_producto(self):
        """
        Guarda o actualiza un producto dependiendo del ID del producto seleccionado.
        """
        categoria_id = self.combo_categorias.currentData()
        nombre = self.txt_nombre.text().strip()
        empaque = self.txt_empaque.text().strip()
        tamano = self.spin_tamano.value()
        unidad = self.combo_unidades.currentText()
        stock = self.spin_stock.value()
        precio = self.spin_precio_unidad.value()

        if not categoria_id:
            QMessageBox.warning(self, "Atención", "Debe registrar o seleccionar una categoría.")
            return
        if not nombre or not empaque:
            QMessageBox.warning(self, "Campos Requeridos", "El nombre y el empaque son campos obligatorios.")
            return

        try:
            if self.id_producto_seleccionado is None:
                # CREAR NUEVO PRODUCTO
                InventarioController.crear_producto(
                    categoria_id=categoria_id,
                    nombre=nombre,
                    empaque_unidad=empaque,
                    tamano_unidad_peso=tamano,
                    unidad_medida=unidad,
                    stock_unidades=stock,
                    precio_unidad=precio
                )
                QMessageBox.information(self, "Éxito", f"Producto '{nombre}' registrado correctamente.")
            else:
                # EDITAR PRODUCTO EXISTENTE
                InventarioController.actualizar_producto(
                    producto_id=self.id_producto_seleccionado,
                    categoria_id=categoria_id,
                    nombre=nombre,
                    empaque_unidad=empaque,
                    tamano_unidad_peso=tamano,
                    unidad_medida=unidad,
                    stock_unidades=stock,
                    precio_unidad=precio
                )
                QMessageBox.information(self, "Éxito", f"Producto '{nombre}' modificado correctamente.")

            # Limpiar e invocar recarga de la tabla
            self.limpiar_seleccion()
            self.cargar_inventario()

        except ValueError as ve:
            QMessageBox.warning(self, "Validación", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el producto: {e}")

    def exportar_excel(self):
        """
        Abre un diálogo de guardado y llama al controlador para exportar el inventario a Excel.
        """
        default_filename = "Inventario_Global.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Inventario a Excel",
            default_filename,
            "Archivos de Excel (*.xlsx)"
        )

        if not filepath:
            return

        try:
            InventarioController.exportar_a_excel(filepath)
            QMessageBox.information(self, "Éxito", f"Inventario exportado exitosamente a:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar el inventario a Excel: {e}")
