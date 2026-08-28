"""Exportadores a Excel (.xlsx) usando openpyxl."""

from datetime import datetime
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from core.models import TipoMovimiento
from movimientos.models import Movimiento


# ---- Estilos comunes --------------------------------------------------------

HEADER_FILL = PatternFill("solid", fgColor="0B3666")
HEADER_FONT = Font(bold=True, color="FFFFFF")
TITLE_FONT = Font(bold=True, size=14, color="0B3666")
MONEY_FILL = PatternFill("solid", fgColor="EAF1FB")
THIN = Side(border_style="thin", color="CBD5E1")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
MONEY_FORMAT = '"$"#,##0.00'


def _autosize(ws, min_width: int = 10, max_width: int = 50):
    for col in ws.columns:
        try:
            letter = col[0].column_letter
        except AttributeError:
            continue
        length = max((len(str(c.value)) for c in col if c.value is not None), default=10)
        ws.column_dimensions[letter].width = max(min_width, min(length + 2, max_width))


def _estilo_header(ws, row: int, ncols: int):
    for col in range(1, ncols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER


# ---- Exportadores -----------------------------------------------------------


def exportar_movimientos(qs, titulo: str = "Movimientos") -> Workbook:
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimientos"

    ws.append([titulo])
    ws["A1"].font = TITLE_FONT
    ws.append([f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
    ws.append([])

    headers = ["Fecha", "Tipo", "Concepto", "Categoria", "Descripcion", "Valor", "Origen"]
    ws.append(headers)
    _estilo_header(ws, ws.max_row, len(headers))

    for m in qs:
        ws.append([
            m.fecha,
            m.get_tipo_display(),
            m.concepto or "",
            m.categoria.nombre if m.categoria else "",
            m.descripcion or "",
            float(m.valor),
            m.get_origen_display(),
        ])
        last = ws.max_row
        ws.cell(row=last, column=1).number_format = "yyyy-mm-dd"
        ws.cell(row=last, column=6).number_format = MONEY_FORMAT

    _autosize(ws)
    return wb


def exportar_ingresos(qs) -> Workbook:
    return exportar_movimientos(qs.filter(tipo=TipoMovimiento.INGRESO), "Ingresos")


def exportar_egresos(qs) -> Workbook:
    return exportar_movimientos(qs.filter(tipo=TipoMovimiento.EGRESO), "Egresos")


def exportar_reporte_financiero(reporte: dict) -> Workbook:
    wb = Workbook()

    # ---- Hoja resumen ----
    ws = wb.active
    ws.title = "Reporte financiero"

    ws["A1"] = "ALSI BALANCE - Reporte Financiero"
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:C1")

    ws["A2"] = f"Periodo: {reporte['fecha_desde']:%Y-%m-%d} a {reporte['fecha_hasta']:%Y-%m-%d}"
    ws.merge_cells("A2:C2")
    ws["A3"] = f"Generado: {datetime.now():%Y-%m-%d %H:%M}"
    ws.merge_cells("A3:C3")
    ws.append([])

    ws.append(["Concepto", "Valor"])
    _estilo_header(ws, ws.max_row, 2)
    filas = [
        ("Saldo inicial", reporte["saldo_inicial_periodo"]),
        ("Ingresos", reporte["ingresos"]),
        ("Egresos", reporte["egresos"]),
        ("Balance", reporte["balance"]),
        ("Saldo final", reporte["saldo_final"]),
    ]
    for etiqueta, valor in filas:
        ws.append([etiqueta, float(valor)])
        cell = ws.cell(row=ws.max_row, column=2)
        cell.number_format = MONEY_FORMAT
        cell.fill = MONEY_FILL

    _autosize(ws, min_width=20, max_width=40)

    # ---- Hoja ingresos por categoria ----
    ws2 = wb.create_sheet("Ingresos por categoria")
    ws2.append(["Categoria", "Total"])
    _estilo_header(ws2, 1, 2)
    for row in reporte["ingresos_por_categoria"]:
        ws2.append([row["categoria__nombre"], float(row["total"] or 0)])
        ws2.cell(row=ws2.max_row, column=2).number_format = MONEY_FORMAT
    _autosize(ws2)

    # ---- Hoja egresos por categoria ----
    ws3 = wb.create_sheet("Egresos por categoria")
    ws3.append(["Categoria", "Total"])
    _estilo_header(ws3, 1, 2)
    for row in reporte["egresos_por_categoria"]:
        ws3.append([row["categoria__nombre"], float(row["total"] or 0)])
        ws3.cell(row=ws3.max_row, column=2).number_format = MONEY_FORMAT
    _autosize(ws3)

    # ---- Hoja detalle de movimientos ----
    ws4 = wb.create_sheet("Detalle movimientos")
    headers = ["Fecha", "Tipo", "Concepto", "Categoria", "Valor"]
    ws4.append(headers)
    _estilo_header(ws4, 1, len(headers))
    for m in reporte["movimientos"]:
        ws4.append([
            m.fecha,
            m.get_tipo_display(),
            m.concepto or "",
            m.categoria.nombre if m.categoria else "",
            float(m.valor),
        ])
        ws4.cell(row=ws4.max_row, column=1).number_format = "yyyy-mm-dd"
        ws4.cell(row=ws4.max_row, column=5).number_format = MONEY_FORMAT
    _autosize(ws4)

    return wb


def workbook_to_response(wb: Workbook, filename: str):
    """Helper para que las vistas serialicen el workbook a una respuesta HTTP."""
    from django.http import HttpResponse

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
