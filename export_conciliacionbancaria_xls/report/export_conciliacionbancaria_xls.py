# -*- coding: utf-8 -*-

#from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo import models
import xlsxwriter
import xlwt
from xlwt.Utils import rowcol_to_cell
from xlsxwriter.utility import xl_rowcol_to_cell
import datetime

class ConciliacionBancariaXls(models.AbstractModel):#ReportXlsx):
    _name = 'report.export_conciliacionbancaria_xls.conciliacion_report_xls'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self, workbook, data, lines):
                           
        sheet = workbook.add_worksheet('Conciliacion Bancaria')
        
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,  'bottom': True, 'top': True, 'bold': True})
        format21 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        formatleft21 = workbook.add_format({'font_size': 12, 'align': 'left', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
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
        sheet.set_column(1, 1, 50)
        sheet.set_column(2, 8, 14)      

        sheet.merge_range('A1:I1',  self.env.user.company_id.name, format21) 
        sheet.merge_range('A2:I2', 'Conciliacion Bancaria', format21)
        sheet.merge_range('A3:I3', self.env['bank.reconciliation'].browse(data['form']['conciliacion_id']).name, format21)
  
        rec_row = 5
        
        bank_reconciliation_obj = self.env['bank.reconciliation']
        
        bank_reconciliation_ids = bank_reconciliation_obj.search([('id', '=', data['form']['conciliacion_id'])])
        
        if bank_reconciliation_ids:            
              
            saldo_banco = bank_reconciliation_obj.browse(bank_reconciliation_ids[0].id).bank_account
        
            saldo_contabilidad = bank_reconciliation_obj.browse(bank_reconciliation_ids[0].id).bank_statement
            
            en_circulacion = bank_reconciliation_obj.browse(bank_reconciliation_ids[0].id).less_unrepresented_amount
            
            no_operados = bank_reconciliation_obj.browse(bank_reconciliation_ids[0].id).deposit_not_credited_bank
            
            diferencia = bank_reconciliation_obj.browse(bank_reconciliation_ids[0].id).differance
            
        else:
            
            saldo_banco = 0
            
            saldo_contabilidad = 0
            
            en_circulacion = 0
            
            no_operados = 0
            
            diferencia = 0      
            
        sheet.write(rec_row, 1, 'Saldo Final Estado de Cuenta Bancario:', formatleft21)
        
        sheet.write(rec_row, 4, saldo_contabilidad, money)
        
        rec_row += 2
        
        sheet.write(rec_row, 1, 'Conciliacion Bancaria:', formatleft21)
        
        rec_row += 2
        
        sheet.write(rec_row, 1, '(-) Cheques y Notas Debito en Circulacion:', formatleft21)
        
        sheet.write(rec_row, 4, en_circulacion, money)
        
        rec_row += 2
        
        sheet.write(rec_row, 1, '(+) Depositos y Creditos no Operados:', formatleft21)
        
        sheet.write(rec_row, 4, no_operados, money)
        
        rec_row += 2
        
        sheet.write(rec_row, 1, 'SUMATORIA:', formatleft21)
        
        rec_row += 2
        
        sheet.write(rec_row, 1, 'Saldo de La Contabilidad:', formatleft21)
        
        sheet.write(rec_row, 4, saldo_banco, money)
            
        rec_row += 2
        
        sheet.write(rec_row, 1, 'Diferencia:', formatleft21)
        
        sheet.write(rec_row, 4, diferencia, money)
        
        rec_row += 2
        
        if data['form']['imprime_movimientos_conciliados'] == "si":
            
            sheet.write(rec_row, 1, 'Movimientos Conciliados', formatleft21)
       
            rec_row += 2
         
            sheet.write(rec_row, 0, 'Fecha', cyan_mark)
            sheet.write(rec_row, 1, 'Tipo', cyan_mark)  
            sheet.write(rec_row, 2, 'Transacción', cyan_mark)
            sheet.write(rec_row, 3, 'Asiento', cyan_mark)
            sheet.write(rec_row, 4, 'Referencia', cyan_mark)
            sheet.write(rec_row, 5, 'A nombre de', cyan_mark)
            sheet.write(rec_row, 6, 'Crédito', cyan_mark)
            sheet.write(rec_row, 7, 'Débito', cyan_mark)
            sheet.write(rec_row, 8, 'Otra Moneda', cyan_mark)

            sql = """
                 SELECT id_conciliacion, id_diario_conciliacion, start_date, end_date, descripcion_conciliacion,
                        account_rec_id, id_apunte, partner_id, debit, credit, balance, nombre_partner, document_number,
                        nombre_linea, ref, date, date_maturity, is_not_confirm, is_bank_reconcile, move_name,
                        payment_type, check_number, x_deposito, x_cheque_manual, amount_currency
                  FROM "MC_conciliacion"
                 WHERE id_conciliacion = %s
                   AND is_bank_reconcile
                 ORDER BY date, id_apunte;
                 """
        
            self.env.cr.execute(sql, (data['form']['conciliacion_id'],))
          
            rec_row += 1
        
            rec_inicio = rec_row
        
            doc_count = 0
        
            for query_line in self.env.cr.dictfetchall():
             
                fs = query_line['date'].strftime('%Y-%m-%d').split('-')
                _fecha=((fs[2])+"-"+fs[1]+"-"+fs[0])
            
                sheet.write(rec_row, 0, _fecha, font_size_8)
                   
                if  query_line['payment_type'] == 'outbound': 
                    sheet.write(rec_row, 1, "CHEQUE", font_size_8)
                elif    query_line['payment_type'] == 'inbound': 
                    sheet.write(rec_row, 1, 'DEPOSITO', font_size_8)
                elif    query_line['payment_type'] == 'transfer': 
                    sheet.write(rec_row, 1, 'TRANSFERENCIA', font_size_8)
                else:   sheet.write(rec_row, 1, query_line['nombre_linea'], font_size_8) 

                sheet.write(rec_row, 2, query_line['nombre_linea'], font_size_8)
                sheet.write(rec_row, 3, query_line['move_name'], font_size_8)
                sheet.write(rec_row, 4, query_line['document_number'], font_size_8)
                sheet.write(rec_row, 5, query_line['ref'], font_size_8)
                sheet.write(rec_row, 6, query_line['debit'], font_number_size_8)
                sheet.write(rec_row, 7, query_line['credit'], font_number_size_8)
                sheet.write(rec_row, 8, query_line['amount_currency'], font_number_size_8)
            
                doc_count += 1
                rec_row += 1
                     
            sheet.write(rec_row, 1, 'Total Documentos:', formatleft21)
            sheet.write(rec_row, 3, doc_count, formatleft21) 
        
            first_cell = rowcol_to_cell(rec_inicio, 6)
            last_cell = rowcol_to_cell(rec_row-1, 6)
        
            debitos = '=SUM(%s:%s)' % (first_cell, last_cell)
        
            sheet.write_formula(rec_row, 6, debitos, money)
        
            first_cell = rowcol_to_cell(rec_inicio, 7)
            last_cell = rowcol_to_cell(rec_row-1, 7)

            creditos = '=SUM(%s:%s)' % (first_cell, last_cell)
        
            sheet.write_formula(rec_row, 7, creditos, money)
        
            first_cell = rowcol_to_cell(rec_inicio, 8)
            last_cell = rowcol_to_cell(rec_row-1, 8)

            otra_moneda = '=SUM(%s:%s)' % (first_cell, last_cell)
        
            sheet.write_formula(rec_row, 8, otra_moneda, money)
        
            rec_row += 2
        
        sheet.write(rec_row, 1, 'Movimientos No Conciliados', formatleft21)
       
        rec_row += 2 
        
        sheet.write(rec_row, 0, 'Fecha', cyan_mark)
        sheet.write(rec_row, 1, 'Tipo', cyan_mark)  
        sheet.write(rec_row, 2, 'Transacción', cyan_mark)
        sheet.write(rec_row, 3, 'Asiento', cyan_mark)
        sheet.write(rec_row, 4, 'Referencia', cyan_mark)
        sheet.write(rec_row, 5, 'A nombre de', cyan_mark)
        sheet.write(rec_row, 6, 'Crédito', cyan_mark)
        sheet.write(rec_row, 7, 'Débito', cyan_mark)
        sheet.write(rec_row, 8, 'Otra Moneda', cyan_mark)
        
        rec_row += 1
        
        rec_inicio = rec_row
        
        sql = """
        SELECT id_conciliacion, id_diario_conciliacion, start_date, end_date, descripcion_conciliacion,
        	account_rec_id, id_apunte, partner_id, debit, credit, balance, nombre_partner, document_number,
        	nombre_linea, ref, date, date_maturity, is_not_confirm, is_bank_reconcile, move_name,
        	payment_type, check_number, x_deposito, x_cheque_manual, amount_currency
         FROM "MC_conciliacion"
        WHERE id_conciliacion = %s
          AND Not is_bank_reconcile
        ORDER BY date, id_apunte;
        """
        
        self.env.cr.execute(sql, (data['form']['conciliacion_id'],))
        
        doc_count = 0
        
        for query_line in self.env.cr.dictfetchall():
             
            fs = query_line['date'].strftime('%Y-%m-%d').split('-')
            _fecha=((fs[2])+"-"+fs[1]+"-"+fs[0])
            
            sheet.write(rec_row, 0, _fecha, font_size_8)
            
            if  query_line['payment_type'] == 'outbound': 
                sheet.write(rec_row, 1, "CHEQUE", font_size_8)
            elif    query_line['payment_type'] == 'inbound': 
                sheet.write(rec_row, 1, 'DEPOSITO', font_size_8)
            elif    query_line['payment_type'] == 'transfer': 
                sheet.write(rec_row, 1, 'TRANSFERENCIA', font_size_8)
            else:   sheet.write(rec_row, 1, query_line['nombre_linea'], font_size_8) 
            
            sheet.write(rec_row, 2, query_line['nombre_linea'], font_size_8)
            sheet.write(rec_row, 3, query_line['move_name'], font_size_8)
            sheet.write(rec_row, 4, query_line['document_number'], font_size_8)
            sheet.write(rec_row, 5, query_line['ref'], font_size_8)
            sheet.write(rec_row, 6, query_line['debit'], font_number_size_8)
            sheet.write(rec_row, 7, query_line['credit'], font_number_size_8)
            sheet.write(rec_row, 8, query_line['amount_currency'], font_number_size_8)
        
            doc_count += 1
            rec_row += 1
        
        sheet.write(rec_row, 1, 'Total Documentos:', formatleft21)
        sheet.write(rec_row, 3, doc_count, formatleft21) 
        
        first_cell = rowcol_to_cell(rec_inicio, 6)
        last_cell = rowcol_to_cell(rec_row-1, 6)
        
        debitos = '=SUM(%s:%s)' % (first_cell, last_cell)
        
        sheet.write_formula(rec_row, 6, debitos, money)
        
        first_cell = rowcol_to_cell(rec_inicio, 7)
        last_cell = rowcol_to_cell(rec_row-1, 7)

        creditos = '=SUM(%s:%s)' % (first_cell, last_cell)
        
        sheet.write_formula(rec_row, 7, creditos, money)
         
        first_cell = rowcol_to_cell(rec_inicio, 8)
        last_cell = rowcol_to_cell(rec_row-1, 8)

        otra_moneda = '=SUM(%s:%s)' % (first_cell, last_cell)
        
        sheet.write_formula(rec_row, 8, otra_moneda, money)
                
        rec_row += 4 
        
        sheet.write(rec_row, 1, 'Elaborado por', formatleft21)
        sheet.write(rec_row, 5, 'Aprobado por', formatleft21)
        
#ConciliacionBancariaXls('report.export_conciliacionbancaria_xls.conciliacionbancaria_report_xls.xlsx', 'bank.reconciliation')