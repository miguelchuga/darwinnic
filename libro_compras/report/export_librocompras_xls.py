from odoo import models
import xlsxwriter
import xlwt
from xlwt.Utils import rowcol_to_cell
from xlsxwriter.utility import xl_rowcol_to_cell
import datetime

class ConciliacionBancariaXls(models.AbstractModel):
    _name = 'report.libro_compras.report_librocompras_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):

                
        sheet = workbook.add_worksheet('Libro de Compras')
        sheet2 = workbook.add_worksheet('Top 10')

        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        formatleft21 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        formatright21 = workbook.add_format({'font_size': 10, 'align': 'right', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        formatcenter21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        font_size_12 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'align': 'left', 'font_size': 12})
        font_size_10 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'align': 'left', 'font_size': 10})
        fontSize10Normal = workbook.add_format({'align': 'left', 'font_size': 10})
        fontSizeCenter10 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'align': 'center', 'font_size': 10})
        fontSizeRight10 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'align': 'right', 'font_size': 10})
        format_date = workbook.add_format({'num_format':'dd-mm-yyyy','bottom': True, 'top': True, 'right': True, 'left': True, 'align': 'left', 'font_size': 10})
        
        
        #Encabezado Reporte
        sheet.write('A1','Empresa: ',formatright21)
        sheet.merge_range('B1:G1',lines.company_id.name,formatleft21)
        
        sheet.write('A2','Nit: ',formatright21)
        sheet.merge_range('B2:G2',lines.company_id.vat,font_size_10)

        sheet.write('A3','Dirección: ',formatright21)
        sheet.merge_range('B3:G3',lines.company_id.street,font_size_10)

        #Titulo
        sheet.merge_range('A5:B5','LIBRO DE COMPRAS',formatleft21)
        sheet.write('D5','Desde: ',formatright21)
        sheet.merge_range('E5:F5',lines.fecha_desde,format_date)
        sheet.write('H5','Hasta: ',formatright21)
        sheet.merge_range('I5:J5',lines.fecha_hasta,format_date)

        #Encabezado Detalle

        rec_row = 6

        sheet.write(rec_row,0,' # ',fontSizeCenter10)
        sheet.write(rec_row,1,'FECHA',formatcenter21)
        sheet.write(rec_row,2,'NOMBRE',formatcenter21)
        sheet.write(rec_row,3,'SERIE',formatcenter21)
        sheet.write(rec_row,4,'NRO.',formatcenter21)
        sheet.write(rec_row,5,'NIT',formatcenter21)
        sheet.write(rec_row,6,'BIENES',formatcenter21)
        sheet.write(rec_row,7,'SERVICIOS',formatcenter21)
        sheet.write(rec_row,8,'IMPORTACIÓN',formatcenter21)
        sheet.write(rec_row,9,'ACTIVOS',formatcenter21)
        sheet.set_column(6,8,15,None)
        sheet.write(rec_row,10,'COMBUSTIBLE',formatcenter21)
        sheet.set_column(6,9,15,None)
        sheet.write(rec_row,11,'PEQ. CONT.',formatcenter21)
        sheet.write(rec_row,12,'IVA',formatcenter21)
        sheet.write(rec_row,13,'TOTAL',formatcenter21)
        sheet.write(rec_row,14,'EXCENTOS',formatcenter21)

        rec_row += 1

        lw3 = []
        w3 = 0
        
        #Se obtiene el mayor numero de caracteres de toda la columna
        w1 = max([len(str(l.fecha_documento)) for l in lines.libro_line_ids])
        w2 = max([len(l.proveedor) for l in lines.libro_line_ids])
        for l in lines.libro_line_ids:
            if l.serie:
                lw3.append(len(l.serie))
        w3 = max(lw3) if lw3 else 10
        #w4 = max([len(str(l.correlativo)) for l in lines.libro_line_ids])
        w5 = max([len(str(l.nit_dpi)) for l in lines.libro_line_ids])

        #Se configura columna con el dato anterior para que se ajuste la informacion en la celda
        sheet.set_column('B:B',w1,None)    
        sheet.set_column('C:C',w2,None)
        sheet.set_column('D:D',w3,None)
        #sheet.set_column('E:E',w4,None)
        sheet.set_column('F:F',w5,None)


        #Variables para Totales al final del Detalle
        totBienes = totServicios = totPequenio = totIva = totTotal = 0
        correlativoNo = 1
        #Variables para Resumen
        #Totales para Documentos tipo Factura
        totFactDoc = totBienesFa = totServiciosFa = totImportFa = totActivoFc = totCombustibleFa = totPeqContFa = totIvaFa = totTotalFa = totExcentoFa = 0
        #Totales para Documentos tipo Nota de Credito
        totNcDoc = totBienesNc = totServiciosNc = totImportNc = totActivoNc = totCombustibleNc = totPeqContNc = totIvaNc = totTotalNc = totExcentoNc = 0
        #Totales del Resumen Final
        totDoc = totBienRes = totSerRes = totImpRes = totActRes = totCombRes = totPequRes = totIvaRes = totTotRes = totExcRes = 0
        #VARIABLES TOTALES BIENES, SERVICIOS Y EXCENTO
        total_bienes = total_servicios = total_excento = 0

        #Lineas de Detalle
        for line in lines.libro_line_ids:
            sheet.write(rec_row,0,correlativoNo,fontSizeCenter10)
            correlativoNo += 1
            sheet.write(rec_row,1,line.fecha_documento,format_date)

            sheet.write(rec_row,2,line.proveedor,font_size_10)
            sheet.write(rec_row,3,line.invoice_id.serie_gt,font_size_10)
            sheet.write(rec_row,4,line.invoice_id.ref,font_size_10)
            sheet.write(rec_row,5,line.nit_dpi,font_size_10)

            total_bienes = line.local_bienes_gravados + line.local_bienes_exentos + line.importacion_bienes_exentos
            sheet.write(rec_row,6,total_bienes,fontSizeRight10)
            totBienes += total_bienes

            total_servicios = line.local_servicios_gravados + line.local_servicios_exentos + line.importacion_servicios_gravados + line.importacion_servicios_exentos
            sheet.write(rec_row,7,total_servicios,fontSizeRight10)
            totServicios += total_servicios

            sheet.write(rec_row,8,line.importacion_bienes_gravados,fontSizeRight10)

            sheet.write(rec_row,9,line.activos_fijos,fontSizeRight10)
            sheet.write(rec_row,10,line.local_bienes_gravados_combustible,fontSizeRight10)
            
            total_pequenio = line.local_bienes_pequenio_contribuyente + line.local_servicios_pequenio_contribuyente
            sheet.write(rec_row,11,total_pequenio,fontSizeRight10)
            totPequenio += total_pequenio

            sheet.write(rec_row,12,line.iva,fontSizeRight10)
            totIva += line.iva

            sheet.write(rec_row,13,line.total,fontSizeRight10)
            totTotal += line.total

            total_excento = line.idp + line.timbre_prensa + line.tasa_municipal + line.inguat
            sheet.write(rec_row,14,total_excento,fontSizeRight10)

            if line.asiste_libro == 'NC':
                totNcDoc += 1
                totBienesNc += total_bienes
                totServiciosNc += total_servicios
                totImportNc += line.importacion_bienes_gravados
                totActivoNc += line.activos_fijos
                totCombustibleNc += line.local_bienes_gravados_combustible
                totPeqContNc += total_pequenio
                totIvaNc += line.iva
                totTotalNc += line.total
                totExcentoNc += total_excento
            else:
                totFactDoc += 1
                totBienesFa += total_bienes
                totServiciosFa += total_servicios
                totImportFa += line.importacion_bienes_gravados
                totActivoFc += line.activos_fijos
                totCombustibleFa += line.local_bienes_gravados_combustible
                totPeqContFa += total_pequenio
                totIvaFa += line.iva
                totTotalFa += line.total
                totExcentoFa += total_excento

            totDoc = totNcDoc + totFactDoc
            totBienRes = totBienesNc + totBienesFa
            totSerRes = totServiciosNc + totServiciosFa
            totImpRes = totImportNc + totImportFa
            totActRes = totActivoNc + totActivoFc
            totCombRes = totCombustibleNc + totCombustibleFa
            totPequRes = totPeqContNc + totPeqContFa
            totIvaRes = totIvaNc + totIvaFa
            totTotRes = totTotalNc + totTotalFa
            totExcRes = totExcentoNc + totExcentoFa

            rec_row += 1

        #TOTALES DEL DETALLE
        sheet.write(rec_row,5,'TOTAL',font_size_10)
        sheet.write(rec_row,6,totBienes,fontSizeRight10)
        sheet.write(rec_row,7,totServicios,fontSizeRight10)
        sheet.write(rec_row,8,totImpRes,fontSizeRight10)
        sheet.write(rec_row,9,totActRes,fontSizeRight10)
        sheet.write(rec_row,10,totCombRes,fontSizeRight10)
        sheet.write(rec_row,11,totPequenio,fontSizeRight10)
        sheet.write(rec_row,12,totIva,fontSizeRight10)
        sheet.write(rec_row,13,totTotal,fontSizeRight10)
        sheet.write(rec_row,14,totExcRes,fontSizeRight10)


        #Encabezado Resumen
        rec_row += 3
        sheet.write(rec_row,4,'RESUMEN',formatcenter21)
        sheet.write(rec_row,5,'DOC CNT',formatcenter21)
        sheet.write(rec_row,6,'BIENES',formatcenter21)
        sheet.write(rec_row,7,'SERVICIOS',formatcenter21)
        sheet.write(rec_row,8,'IMPORTACIONES',formatcenter21)
        sheet.write(rec_row,9,'ACTIVOS',formatcenter21)
        sheet.write(rec_row,10,'COMBUSTIBLE',formatcenter21)
        sheet.write(rec_row,11,'PEQ. CONT.',formatcenter21)
        sheet.write(rec_row,12,'IVA',formatcenter21)
        sheet.write(rec_row,13,'TOTAL',formatcenter21)

        #Valores del Resumen
        rec_row += 1
        sheet.write(rec_row,4,'FACT',formatcenter21)
        sheet.write(rec_row,5,totFactDoc,fontSizeRight10)
        sheet.write(rec_row,6,totBienesFa,fontSizeRight10)
        sheet.write(rec_row,7,totServiciosFa,fontSizeRight10)
        sheet.write(rec_row,8,totImportFa,fontSizeRight10)
        sheet.write(rec_row,9,totActivoFc,fontSizeRight10)
        sheet.write(rec_row,10,totCombustibleFa,fontSizeRight10)
        sheet.write(rec_row,11,totPeqContFa,fontSizeRight10)
        sheet.write(rec_row,12,totIvaFa,fontSizeRight10)
        sheet.write(rec_row,13,totTotalFa,fontSizeRight10)

        rec_row += 1
        sheet.write(rec_row,4,'N/C',formatcenter21)
        sheet.write(rec_row,5,totNcDoc,fontSizeRight10)
        sheet.write(rec_row,6,totBienesNc,fontSizeRight10)
        sheet.write(rec_row,7,totServiciosNc,fontSizeRight10)
        sheet.write(rec_row,8,totImportNc,fontSizeRight10)

        sheet.write(rec_row,9,totActivoNc,fontSizeRight10)
        sheet.write(rec_row,10,totCombustibleNc,fontSizeRight10)
        sheet.write(rec_row,11,totPeqContNc,fontSizeRight10)
        sheet.write(rec_row,12,totIvaNc,fontSizeRight10)
        sheet.write(rec_row,13,totTotalNc,fontSizeRight10)

        rec_row += 1
        sheet.write(rec_row,4,'TOTAL',formatcenter21)
        sheet.write(rec_row,5,totDoc,fontSizeRight10)
        sheet.write(rec_row,6,totBienRes,fontSizeRight10)
        sheet.write(rec_row,7,totSerRes,fontSizeRight10)
        sheet.write(rec_row,8,totImpRes,fontSizeRight10)
        sheet.write(rec_row,9,totActRes,fontSizeRight10)
        sheet.write(rec_row,10,totCombRes,fontSizeRight10)
        sheet.write(rec_row,11,totPequRes,fontSizeRight10)
        sheet.write(rec_row,12,totIvaRes,fontSizeRight10)
        sheet.write(rec_row,13,totTotRes,fontSizeRight10)
        

        ############# HOJA 2 ############# 

        #Encabezado Reporte
        sheet2.write('A1','Empresa: ',formatright21)
        sheet2.merge_range('B1:G1',lines.company_id.name,formatleft21)
        
        sheet2.write('A2','Nit: ',formatright21)
        sheet2.merge_range('B2:G2',lines.company_id.vat,font_size_10)

        sheet2.write('A3','Dirección: ',formatright21)
        sheet2.merge_range('B3:G3',lines.company_id.street,font_size_10)

        #Titulo
        sheet2.merge_range('A5:B5','TOP 10 PROVEEDORES',formatleft21)
        sheet2.write('D5','Desde: ',formatright21)
        sheet2.merge_range('E5:F5',lines.fecha_desde,format_date)
        sheet2.write('H5','Hasta: ',formatright21)
        sheet2.merge_range('I5:J5',lines.fecha_hasta,format_date)

        rec_row = 6

        sheet2.write(rec_row,0,'NOMBRE',formatcenter21)
        sheet2.write(rec_row,1,'NIT',formatcenter21)
        sheet2.write(rec_row,2,'TOTAL',formatcenter21)
        sheet2.write(rec_row,3,'DOCS. CNT.',formatcenter21)

        s21 = max([len(str(l.proveedor)) for l in lines.libro_top_proveedores_ids])
        sheet2.set_column('A:A',s21,None)

        s22 = max([len(str(l.nit_dpi)) for l in lines.libro_top_proveedores_ids])
        sheet2.set_column('B:B',s22,None)

        rec_row += 2
        for line in lines.libro_top_proveedores_ids:
            
            sheet2.write(rec_row,0,line.proveedor,font_size_10)
            sheet2.write(rec_row,1,line.nit_dpi,font_size_10)
            sheet2.write(rec_row,2,line.base,fontSizeRight10)
            sheet2.write(rec_row,3,line.cantidad,fontSizeRight10)

            rec_row += 1


