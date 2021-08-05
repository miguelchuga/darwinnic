from openerp import models, fields, api

class LibroBancos(models.TransientModel):
    
    _name = "wizard.librobancos"
    _description = "Libro de Bancos"

    state = fields.Selection([('Asentada', 'Asentada'), ('No Asentada', 'No Asentada'), ('Todas', 'Todas')], default='Asentada')
    account_id = fields.Many2one('account.account', string='Cuenta Bancaria', required=True)
    date_from = fields.Date('Start Date', default=fields.Datetime.now)         
    date_to = fields.Date('End Date', default=fields.Datetime.now)
    
    # @api.multi
    # def export_xls(self):
    #     context = self._context
    #     datas = {'ids': context.get('active_ids', [])}
    #     datas['model'] = 'account.account'
    #     datas['form'] = self.read()[0]
    #     for field in datas['form'].keys():
    #         if isinstance(datas['form'][field], tuple):
    #             datas['form'][field] = datas['form'][field][0]
    #     if context.get('xls_export'):
    #         return {'type': 'ir.actions.report.xml',
    #                 'report_name': 'export_librobancos_xls.librobancos_report_xls.xlsx',
    #                 'datas': datas,
    #                 'name': 'Libro Bancos'
    #                 }


    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'account.account'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if context.get('xls_export'):
            return self.env.ref('export_librobancos_xls.librobancos_report_xls').report_action(self,data=datas)
