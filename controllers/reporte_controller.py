import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from database.schema import get_connection

class ReporteController:
    """
    Controlador para la consulta y exportación de reportes detallados a Excel.
    """

    @staticmethod
    def obtener_datos_reporte(semana_id: int, refugio_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta la consulta SQL definida en REQUIREMENTS.md para obtener la lista de solicitudes,
        con un filtro opcional por refugio_id.
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Consulta base
        query = """
        SELECT
            s.nombre_semana AS "Semana",
            r.nombre AS "Refugio",
            f.codigo_numero AS "Código Familia",
            f.nombre_representativo AS "Familia",
            (i.nombres || ' ' || i.apellidos) AS "Integrante",
            i.edad AS "Edad",
            i.sexo AS "Sexo",
            COALESCE(p.nombre, ds.nombre_producto_manual) AS "Producto Solicitado",
            ds.cantidad_solicitada AS "Cantidad",
            ds.unidad_medida_solicitada AS "Unidad",
            CASE
                WHEN ds.en_inventario = 1 THEN 'Sí'
                ELSE 'No'
            END AS "Disponibilidad en Inventario"
        FROM solicitudes sol
        INNER JOIN semanas s ON sol.semana_id = s.id
        INNER JOIN familias f ON sol.familia_id = f.id
        INNER JOIN refugios r ON f.refugio_id = r.id
        LEFT JOIN integrantes i ON i.familia_id = f.id
        INNER JOIN detalles_solicitud ds ON ds.solicitud_id = sol.id
        LEFT JOIN productos p ON ds.producto_id = p.id
        WHERE s.id = ?
        """

        params = [semana_id]
        if refugio_id is not None:
            query += " AND r.id = ?"
            params.append(refugio_id)

        # El requerimiento dice: "ORDER BY f.codigo_numero, i.apellidos"
        query += " ORDER BY f.codigo_numero, i.apellidos"

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()

            column_names = [
                "Semana", "Refugio", "Código Familia", "Familia", "Nombre Integrante",
                "Edad", "Sexo", "Producto Solicitado", "Cantidad", "Unidad", "Disponibilidad en Inventario"
            ]

            reporte = []
            for row in rows:
                item = {}
                for idx, col in enumerate(column_names):
                    val = row[idx]
                    # Limpieza de None
                    if val is None:
                        val = ""
                    item[col] = val
                reporte.append(item)

            return reporte
        except sqlite3.Error as e:
            print(f"Error al obtener datos de reporte: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def exportar_a_excel(semana_id: int, refugio_id: Optional[int], filepath: str) -> None:
        """
        Genera el reporte a partir de la consulta SQL y lo exporta a un archivo Excel (.xlsx)
        con formato limpio, encabezados resaltados y auto-ajuste de columnas utilizando pandas y openpyxl.
        """
        # 1. Obtener datos
        datos = ReporteController.obtener_datos_reporte(semana_id, refugio_id)

        # 2. Crear DataFrame de pandas
        columnas = [
            "Semana", "Refugio", "Código Familia", "Familia", "Nombre Integrante",
            "Edad", "Sexo", "Producto Solicitado", "Cantidad", "Unidad", "Disponibilidad en Inventario"
        ]

        df = pd.DataFrame(datos, columns=columnas)

        # 3. Exportar usando pandas + openpyxl
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Reporte de Solicitudes")

            # Formateo con openpyxl
            workbook = writer.book
            worksheet = writer.sheets["Reporte de Solicitudes"]

            # Estilos de openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            header_fill = PatternFill(start_color="00897B", end_color="00897B", fill_type="solid") # Turquesa oscuro del tema
            header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
            header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Borde fino gris
            thin_border_side = Side(border_style="thin", color="CCCCCC")
            thin_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

            # Aplicar estilos a cabecera (Fila 1)
            for col_idx in range(1, len(columnas) + 1):
                cell = worksheet.cell(row=1, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
                cell.border = thin_border

            # Aplicar estilos a las celdas de datos
            data_font = Font(name="Arial", size=10)
            data_alignment_center = Alignment(horizontal="center", vertical="center")
            data_alignment_left = Alignment(horizontal="left", vertical="center")

            # Centrar ciertas columnas como Semana, Código, Edad, Sexo, Unidad, Disponibilidad
            center_columns = {1, 3, 6, 7, 10, 11}

            for row_idx in range(2, len(df) + 2):
                for col_idx in range(1, len(columnas) + 1):
                    cell = worksheet.cell(row=row_idx, column=col_idx)
                    cell.font = data_font
                    cell.border = thin_border

                    if col_idx in center_columns:
                        cell.alignment = data_alignment_center
                    else:
                        cell.alignment = data_alignment_left

            # Ajuste automático del ancho de las columnas
            for col in worksheet.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value is not None:
                        max_len = max(max_len, len(str(cell.value)))
                worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)
