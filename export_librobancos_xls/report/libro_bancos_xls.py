# -*- coding: utf-8 -*-

#from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo import models
import xlsxwriter
import xlwt
from xlwt.Utils import rowcol_to_cell
from xlsxwriter.utility import xl_rowcol_to_cell
import datetime

class LibroBancosXLS(models.AbstractModel):#ReportXlsx):
    _name = 'report.export_librobancos_xls.librobancos_report_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self, workbook, data, lines):
                           
        sheet = workbook.add_worksheet('Bancos')
        
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,  'bottom': True, 'top': True, 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        formatleft21 = workbook.add_format({'font_size': 10, 'align': 'left', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'align': 'left', 'font_size': 8})
        font_number_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'align': 'right', 'num_format': '#,##0.00', 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8, 
                                        'bg_color': 'red'})        
        black_mark = workbook.add_format({'bottom': True, 'align': 'center', 'top': True, 'right': True, 'left': True, 'font_size': 14, 'font_color': 'white', 'bg_color': 'black', 'bold': True})        
        cyan_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 10, 'bold': True, 'bg_color': 'cyan'})        
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        
        format3.set_align('center')
        
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        
        # Add a number format for cells with money.
        money = workbook.add_format({'num_format': '#,##0.00'})
    
        # Establece ancho de las columnas.
        sheet.set_column(0, 0, 8)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 16)
        sheet.set_column(3, 3, 50)
        sheet.set_column(4, 4, 12)
        sheet.set_column(5, 6, 44)
        sheet.set_column(7, 9, 14)            

        sheet.merge_range('A1:J1', 'LIBRO DE BANCOS', format21)
        sheet.merge_range('A2:J2',  self.env.user.company_id.name, format21)
  
        sheet.write(5, 0, 'Fecha', cyan_mark)
        sheet.write(5, 1, 'Asiento', cyan_mark)
        sheet.write(5, 2, 'Tipo Dococumento', cyan_mark)        
        sheet.write(5, 3, 'Documento', cyan_mark)
        sheet.write(5, 4, 'Etiqueta', cyan_mark)
        sheet.write(5, 5, 'A nombre de', cyan_mark)
        sheet.write(5, 6, 'Concepto', cyan_mark)
        sheet.write(5, 7, 'Crédito', cyan_mark)
        sheet.write(5, 8, 'Débito', cyan_mark)
        sheet.write(5, 9, 'Saldo', cyan_mark)
         
        rec_row = 6
        
        fs = data['form']['date_from'].split('-')
        _fechadesde=((fs[2])+"-"+fs[1]+"-"+fs[0])
        
        fs = data['form']['date_to'].split('-')
        _fechahasta=((fs[2])+"-"+fs[1]+"-"+fs[0])
        
        sheet.merge_range('A3:J3', self.env['account.account'].browse(data['form']['account_id']).name, format21)
        sheet.merge_range('A4:J4', 'Del: ' + _fechadesde + ' Al: ' + _fechahasta, format21)
             
        wsaldo = 0
        
        if  (data['form']['state'] == 'Asentada'):
        
            wstate = 'posted'
            
        elif (data['form']['state'] == 'No Asentada'):
            
            wstate = 'draft'
            
        else:
            
            wstate = ''
        
        if  wstate == '':
        
            sql = """
             SELECT COALESCE(SUM(debit) - SUM(credit),0) AS saldo
              FROM "MC_bancos"
             WHERE account_id = %s
               AND date < %s
             """
            
            self.env.cr.execute(sql, (data['form']['account_id'], data['form']['date_from'],))
        
        else:
            
            sql = """
             SELECT COALESCE(SUM(debit) - SUM(credit),0) AS saldo
              FROM "MC_bancos"
             WHERE account_id = %s
               AND state = %s
               AND date < %s
             """
            
            self.env.cr.execute(sql, (data['form']['account_id'], wstate, data['form']['date_from'],))
        
        for query_line in self.env.cr.dictfetchall():                    
            
            wsaldo = query_line['saldo']
        
        sheet.write(rec_row, 5, 'Saldo Inicial:', formatleft21)    
    
        sheet.write(rec_row, 9, wsaldo, money)
             
        rec_row += 1

        if  wstate == '':
            
            sql = """
             SELECT id, date, account_id, debit, credit, ref, nombre_linea, check_number, x_deposito
                  , x_cheque_manual, nombre_banco, nombre_asiento, nombre_partner, concepto
                  , payment_type, state, etiqueta_analitica  
              FROM "MC_bancos"
             WHERE account_id = %s
               AND date >= %s and date <= %s
               AND is_bank_reconcile     
             ORDER BY date;
             """
            
            self.env.cr.execute(sql, (data['form']['account_id'], data['form']['date_from'], data['form']['date_to'],))
        
        else:
            
            sql = """
             SELECT id, date, account_id, debit, credit, ref, nombre_linea, check_number, x_deposito
                  , x_cheque_manual, nombre_banco, nombre_asiento, nombre_partner, concepto
                  , payment_type, state, etiqueta_analitica
              FROM "MC_bancos"
             WHERE account_id = %s
               AND state = %s 
               AND date >= %s and date <= %s
               AND is_bank_reconcile     
             ORDER BY date;
             """
            
            self.env.cr.execute(sql, (data['form']['account_id'], wstate, data['form']['date_from'], data['form']['date_to'],))
        
        doc_count = 0
        
        fila_inicial_suma = 7
        
        for query_line in self.env.cr.dictfetchall():

            wsaldo = wsaldo - query_line['credit'] + query_line['debit']
             
            fs = query_line['date'].strftime('%Y-%m-%d').split('-')
            _fecha=((fs[2])+"-"+fs[1]+"-"+fs[0])
            
            sheet.write(rec_row, 0, _fecha, font_size_8)
            sheet.write(rec_row, 1, query_line['nombre_asiento'], font_size_8)
            sheet.write(rec_row, 6, query_line['concepto'], font_size_8) 
            
            if  query_line['payment_type'] == 'outbound':
                if  query_line['check_number']: 
                    sheet.write(rec_row, 2, "CHEQUE", font_size_8)
                else:                    
                    sheet.write(rec_row, 2, "ND", font_size_8)
            elif    query_line['payment_type'] == 'inbound':                    
                    sheet.write(rec_row, 2, 'DEPOSITO', font_size_8)
            elif    query_line['payment_type'] == 'transfer': 
                    sheet.write(rec_row, 2, 'TRANSFERENCIA', font_size_8)
            else:
                    sheet.write(rec_row, 2, '', font_size_8)
                    sheet.write(rec_row, 5, query_line['nombre_linea'], font_size_8) 

            print(query_line['ref'])
            if query_line['ref']:
                if  'revertido desde:' in query_line['ref']:
                    sheet.write(rec_row, 2, 'REVERTIDO', font_size_8)
                
            if  query_line['x_deposito']: 
                sheet.write(rec_row, 3, query_line['x_deposito'], font_size_8)
            elif    query_line['x_cheque_manual']: 
                    sheet.write(rec_row, 3, query_line['x_cheque_manual'], font_size_8)
            elif    query_line['check_number']: 
                    sheet.write(rec_row, 3, query_line['check_number'], font_size_8)
            else:    sheet.write(rec_row, 3, query_line['ref'], font_size_8)

            sheet.write(rec_row, 4, query_line['etiqueta_analitica'], font_size_8)               
            sheet.write(rec_row, 5, query_line['nombre_partner'], font_size_8)                 
            sheet.write(rec_row, 7, query_line['debit'], font_number_size_8)
            sheet.write(rec_row, 8, query_line['credit'], font_number_size_8)
            sheet.write(rec_row, 9, wsaldo, font_number_size_8)
            
            doc_count += 1
            rec_row += 1
                     
        sheet.write(rec_row, 4, 'Total Documentos:', formatleft21)
        sheet.write(rec_row, 5, doc_count, formatleft21) 
        
        first_cell = rowcol_to_cell(fila_inicial_suma, 7)
        last_cell = rowcol_to_cell(rec_row-1, 7)
        
        debitos = '=SUM(%s:%s)' % (first_cell, last_cell)
        
        sheet.write_formula(rec_row, 7, debitos, money)
        
        first_cell = rowcol_to_cell(fila_inicial_suma, 8)
        last_cell = rowcol_to_cell(rec_row-1, 8)

        creditos = '=SUM(%s:%s)' % (first_cell, last_cell)
        
        sheet.write_formula(rec_row, 8, creditos, money)
        
        rec_row += 1
        
        sheet.write(rec_row, 5, 'Saldo Final:', formatleft21)    
        
        sheet.write(rec_row, 9, wsaldo, money)
        
        if  wstate == '':
           
            sql = """
             SELECT id, date, account_id, debit, credit, ref, nombre_linea, check_number, x_deposito
                  , x_cheque_manual, nombre_banco, nombre_asiento, nombre_partner, concepto
                  , payment_type, state, etiqueta_analitica 
              FROM "MC_bancos"
             WHERE account_id = %s
               AND date >= %s and date <= %s
               AND NOT is_bank_reconcile
             ORDER BY date;
             """
            
            self.env.cr.execute(sql, (data['form']['account_id'], data['form']['date_from'], data['form']['date_to'],))
              
        else:
        
            sql = """
             SELECT id, date, account_id, debit, credit, ref, nombre_linea, check_number, x_deposito
                  , x_cheque_manual, nombre_banco, nombre_asiento, nombre_partner, concepto
                  , payment_type, state, etiqueta_analitica 
              FROM "MC_bancos"
             WHERE account_id = %s
               AND state = %s 
               AND date >= %s and date <= %s
               AND NOT is_bank_reconcile
             ORDER BY date;
             """
            
            self.env.cr.execute(sql, (data['form']['account_id'], wstate, data['form']['date_from'], data['form']['date_to'],))
        
        doc_count = 0
        
        fila_inicial_suma = rec_row
        
        for query_line in self.env.cr.dictfetchall():

            wsaldo = wsaldo - query_line['credit'] + query_line['debit']
             
            fs = query_line['date'].strftime('%Y-%m-%d').split('-')
            _fecha=((fs[2])+"-"+fs[1]+"-"+fs[0])
            
            sheet.write(rec_row, 0, _fecha, font_size_8)
            sheet.write(rec_row, 1, query_line['nombre_asiento'], font_size_8)
            sheet.write(rec_row, 6, query_line['concepto'], font_size_8) 

            if  query_line['payment_type'] == 'outbound':
                if  query_line['check_number']: 
                    sheet.write(rec_row, 2, "CHEQUE", font_size_8)
                else:
                    sheet.write(rec_row, 2, "ND", font_size_8)
            elif    query_line['payment_type'] == 'inbound': 
                    sheet.write(rec_row, 2, 'DEPOSITO', font_size_8)
            elif    query_line['payment_type'] == 'transfer': 
                    sheet.write(rec_row, 2, 'TRANSFERENCIA', font_size_8)
            else:
                    sheet.write(rec_row, 5, query_line['nombre_linea'], font_size_8) 
                        
            if  'revertido desde:' in str(query_line['ref']):
                sheet.write(rec_row, 2, 'REVERTIDO', font_size_8)
                
            if  query_line['x_deposito']: 
                sheet.write(rec_row, 3, query_line['x_deposito'], font_size_8)
            elif    query_line['x_cheque_manual']: 
                    sheet.write(rec_row, 3, query_line['x_cheque_manual'], font_size_8)
            elif    query_line['check_number']: 
                    sheet.write(rec_row, 3, query_line['check_number'], font_size_8)
            else:    sheet.write(rec_row, 3, query_line['ref'], font_size_8)
            
            sheet.write(rec_row, 4, query_line['etiqueta_analitica'], font_size_8)     
            sheet.write(rec_row, 5, query_line['nombre_partner'], font_size_8)                 
            sheet.write(rec_row, 7, query_line['debit'], font_number_size_8)
            sheet.write(rec_row, 8, query_line['credit'], font_number_size_8)
            sheet.write(rec_row, 9, wsaldo, font_number_size_8)
            
            doc_count += 1
            rec_row += 1
                     
        sheet.write(rec_row, 4, 'Total Documentos:', formatleft21)
        sheet.write(rec_row, 5, doc_count, formatleft21) 
        
        first_cell = rowcol_to_cell(fila_inicial_suma, 7)
        last_cell = rowcol_to_cell(rec_row-1, 7)
        
        debitos = '=SUM(%s:%s)' % (first_cell, last_cell)
        
        sheet.write_formula(rec_row, 7, debitos, money)
        
        first_cell = rowcol_to_cell(fila_inicial_suma, 8)
        last_cell = rowcol_to_cell(rec_row-1, 8)

        creditos = '=SUM(%s:%s)' % (first_cell, last_cell)
        
        sheet.write_formula(rec_row, 8, creditos, money)
        
        rec_row += 1
        
        sheet.write(rec_row, 5, 'Saldo Final:', formatleft21)    
        
        sheet.write(rec_row, 9, wsaldo, money)
        
#LibroBancosXls('report.export_librobancos_xls.librobancos_report_xls.xlsx', 'account.account')
