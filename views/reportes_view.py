from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from controllers.refugio_controller import RefugioController
from controllers.solicitud_controller import SolicitudController
from controllers.reporte_controller import ReporteController

class ReportesView(QWidget):
    """
    Vista del Módulo de Reportes y Exportación a Excel.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # ------------------ PANEL SUPERIOR: FILTROS ------------------
        filter_group = QGroupBox("Filtros de Reporte")
        filter_layout = QHBoxLayout(filter_group)

        # Selector de Semana
        filter_layout.addWidget(QLabel("Semana *:"))
        self.combo_semana = QComboBox()
        self.combo_semana.setMinimumWidth(220)
        self.combo_semana.currentIndexChanged.connect(self.cargar_vista_previa)
        filter_layout.addWidget(self.combo_semana)

        # Selector de Refugio
        filter_layout.addWidget(QLabel("Refugio:"))
        self.combo_refugio = QComboBox()
        self.combo_refugio.setMinimumWidth(220)
        self.combo_refugio.currentIndexChanged.connect(self.cargar_vista_previa)
        filter_layout.addWidget(self.combo_refugio)

        # Botón de refresco manual
        self.btn_refrescar = QPushButton("Refrescar")
        self.btn_refrescar.setStyleSheet("background-color: #0288D1; color: white; font-weight: bold; padding: 6px 12px;")
        self.btn_refrescar.clicked.connect(self.cargar_vista_previa)
        filter_layout.addWidget(self.btn_refrescar)

        filter_layout.addStretch()

        # Botón de exportación a Excel
        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.setStyleSheet("background-color: #2E7D32; color: white; font-weight: bold; padding: 6px 15px;")
        self.btn_exportar.clicked.connect(self.exportar_excel)
        filter_layout.addWidget(self.btn_exportar)

        main_layout.addWidget(filter_group)

        # ------------------ TABLA DE VISTA PREVIA ------------------
        preview_group = QGroupBox("Vista Previa del Reporte")
        preview_layout = QVBoxLayout(preview_group)

        self.table_preview = QTableWidget()
        self.columnas = [
            "Semana", "Refugio", "Código Familia", "Familia", "Nombre Integrante",
            "Edad", "Sexo", "Producto Solicitado", "Cantidad", "Unidad", "Disponibilidad en Inventario"
        ]
        self.table_preview.setColumnCount(len(self.columnas))
        self.table_preview.setHorizontalHeaderLabels(self.columnas)
        self.table_preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_preview.horizontalHeader().setStretchLastSection(True)
        self.table_preview.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        preview_layout.addWidget(self.table_preview)
        main_layout.addWidget(preview_group)

        # Cargas iniciales
        self.cargar_semanas()
        self.cargar_refugios()
        self.cargar_vista_previa()

    def cargar_semanas(self):
        """
        Llena el combo de semanas.
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

    def cargar_refugios(self):
        """
        Llena el combo de refugios con opción de filtrar por todos.
        """
        self.combo_refugio.blockSignals(True)
        self.combo_refugio.clear()
        try:
            self.combo_refugio.addItem("Todos los refugios", None)
            refugios = RefugioController.obtener_todos()
            for ref in refugios:
                self.combo_refugio.addItem(ref["nombre"], ref["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar refugios: {e}")
        finally:
            self.combo_refugio.blockSignals(False)

    def cargar_vista_previa(self):
        """
        Carga la tabla de vista previa según la semana y el refugio seleccionados.
        """
        self.table_preview.setRowCount(0)
        semana_id = self.combo_semana.currentData()
        refugio_id = self.combo_refugio.currentData()

        if not semana_id:
            return

        try:
            datos = ReporteController.obtener_datos_reporte(semana_id, refugio_id)
            for item in datos:
                row_idx = self.table_preview.rowCount()
                self.table_preview.insertRow(row_idx)

                for col_idx, col_name in enumerate(self.columnas):
                    val = item[col_name]
                    if col_name == "Cantidad" and isinstance(val, (int, float)):
                        val_str = f"{val:.2f}"
                    else:
                        val_str = str(val)

                    self.table_preview.setItem(row_idx, col_idx, QTableWidgetItem(val_str))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar vista previa del reporte: {e}")

    def exportar_excel(self):
        """
        Abre un diálogo de guardado y llama al controlador para exportar a Excel.
        """
        semana_id = self.combo_semana.currentData()
        refugio_id = self.combo_refugio.currentData()

        if not semana_id:
            QMessageBox.warning(self, "Exportación", "Por favor seleccione una semana válida.")
            return

        # Nombre de archivo por defecto sugerido
        semana_text = self.combo_semana.currentText().replace(" ", "_")
        refugio_text = "Todos" if refugio_id is None else self.combo_refugio.currentText().replace(" ", "_")
        default_filename = f"Reporte_{semana_text}_{refugio_text}.xlsx"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte a Excel",
            default_filename,
            "Archivos de Excel (*.xlsx)"
        )

        if not filepath:
            return # El usuario canceló

        try:
            ReporteController.exportar_a_excel(semana_id, refugio_id, filepath)
            QMessageBox.information(self, "Éxito", f"Reporte exportado exitosamente a:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar el reporte a Excel: {e}")
