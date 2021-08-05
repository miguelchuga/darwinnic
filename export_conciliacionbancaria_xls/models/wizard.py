from openerp import models, fields, api

class ConciliacionBancaria(models.TransientModel):
    
    _name = "wizard.conciliacionbancaria"
    _description = "Conciliacion Bancaria"

    conciliacion_id = fields.Many2one('bank.reconciliation', string='Conciliacion Bancaria', required=True)
    imprime_movimientos_conciliados = fields.Selection([('si', 'Si'), ('no','No')], 'Imprime Movimientos Conciliados? ', default='no',required=True)

    # @api.multi
    # def export_xls(self):
    #     context = self._context
    #     datas = {'ids': context.get('active_ids', [])}
    #     datas['model'] = 'bank.reconciliation'
    #     datas['form'] = self.read()[0]
    #     for field in datas['form'].keys():
    #         if isinstance(datas['form'][field], tuple):
    #             datas['form'][field] = datas['form'][field][0]
    #     if context.get('xls_export'):
    #         return {'type': 'ir.actions.report.xml',
    #                 'report_name': 'export_conciliacionbancaria_xls.conciliacionbancaria_report_xls.xlsx',
    #                 'datas': datas,
    #                 'name': 'Conciliacion Bancaria'
    #                 }

    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'bank.reconciliation'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if context.get('xls_export'):
            return self.env.ref('export_conciliacionbancaria_xls.conciliacion_report_xls').report_action(self,data=datas)