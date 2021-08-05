# -*- coding: utf-8 -*-
# from odoo import http


# class McLibroComprasV13(http.Controller):
#     @http.route('/mc_libro_compras_v13/mc_libro_compras_v13/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mc_libro_compras_v13/mc_libro_compras_v13/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mc_libro_compras_v13.listing', {
#             'root': '/mc_libro_compras_v13/mc_libro_compras_v13',
#             'objects': http.request.env['mc_libro_compras_v13.mc_libro_compras_v13'].search([]),
#         })

#     @http.route('/mc_libro_compras_v13/mc_libro_compras_v13/objects/<model("mc_libro_compras_v13.mc_libro_compras_v13"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mc_libro_compras_v13.object', {
#             'object': obj
#         })
