/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define('pos_invoice_on_receipt.pos_invoice_on_receipt',function(require){
    "use strict"
    
    var pos_model = require("point_of_sale.models");
    var SuperPosModel = pos_model.PosModel.prototype;
    var SuperOrder = pos_model.Order.prototype;
    var rpc = require('web.rpc');

    pos_model.PosModel = pos_model.PosModel.extend({

        _flush_orders: function(orders, options) {
            var self = this;
            var result, data
            result = data = SuperPosModel._flush_orders.call(this,orders, options)
            _.each(orders,function(order){
                if (order.to_invoice)
                    data.then(function(order_server_id){
                            rpc.query({
                            model: 'pos.order',
                            method: 'read',
                            args:[order_server_id, ['account_move', 'nombre_cliente', 'nit',  'direccion_cliente',  'fecha_factura', 'frase_certificador',  'nombre_certificador','nit_certificador' ,'infilefel_sat_uuid' ,'infilefel_sign_date', 'serie_venta','infile_number','infilefel_comercial_name','serie_venta','infilefel_establishment_street','nit_empresa','nombre_empresa']]
                                }).then(function(result_dict){
                                    if(result_dict.length){
                                        let invoice = result_dict[0].account_move;
   let nombre_cliente = result_dict[0].nombre_cliente;
                                        let nit = result_dict[0].nit;
                                        let direccion_cliente = result_dict[0].direccion_cliente;
                                        let fecha_factura = result_dict[0].fecha_factura;


                                        let comercial_name = result_dict[0].infilefel_comercial_name;
                                        let nombre_empresa = result_dict[0].nombre_empresa;
                                        let nit_empresa = result_dict[0].nit_empresa;

                                        let direccion = result_dict[0].infilefel_establishment_street;
                                        let infile_number = result_dict[0].infile_number
                                        let serie_venta = result_dict[0].serie_venta

                                        let infilefel_sat_uuid = result_dict[0].infilefel_sat_uuid
                                        let infilefel_sign_date = result_dict[0].infilefel_sign_date

                                        let nit_certificador = result_dict[0].nit_certificador
                                        let nombre_certificador = result_dict[0].nombre_certificador
                                        let frase_certificador = result_dict[0].frase_certificador


                                        self.get_order().invoice_id = invoice[1]
                                        self.get_order().infilefel_comercial_name = comercial_name
                                        self.get_order().nombre_empresa = nombre_empresa
                                        self.get_order().nit_empresa = nit_empresa

                                        self.get_order()._infilefel_establishment_street = direccion
                                        self.get_order().infile_number = infile_number
                                        self.get_order().serie_venta = serie_venta
                                        self.get_order().infilefel_sat_uuid = infilefel_sat_uuid
                                        self.get_order().infilefel_sign_date = infilefel_sign_date

                                        self.get_order().nit_certificador = nit_certificador
                                        self.get_order().nombre_certificador = nombre_certificador
                                        self.get_order().frase_certificador = frase_certificador

                                        self.get_order().nombre_cliente = nombre_cliente
                                        self.get_order().nit = nit
                                        self.get_order().direccion_cliente = direccion_cliente
                                        self.get_order().fecha_factura = fecha_factura

                                    }
                            })
                            .catch(function(error){
                                return result
                            })
                    })
            })
            return result

        },

    })
    pos_model.Order = pos_model.Order.extend({
        export_for_printing: function(){
            var self = this
            var receipt = SuperOrder.export_for_printing.call(this)
            if(self.invoice_id){
                var invoice_id = self.invoice_id
                var invoice = invoice_id.split("(")[0]
                var nombre_cliente = self.nombre_cliente
                var nit = self.nit
                var direccion_cliente = self.direccion_cliente
                var fecha_factura = self.fecha_factura

                var comercial_name = self.infilefel_comercial_name
                var nombre_empresa = self.nombre_empresa
                var nit_empresa = self.nit_empresa

                var direccion = self._infilefel_establishment_street
                var infile_number = self.infile_number
                var serie_venta = self.serie_venta
                var infilefel_sat_uuid = self.infilefel_sat_uuid
                var infilefel_sign_date = self.infilefel_sign_date


                var nit_certificador = self.nit_certificador
                var nombre_certificador = self.nombre_certificador
                var frase_certificador = self.frase_certificador

                receipt.invoice_id = invoice
                receipt.infilefel_comercial_name = comercial_name
                receipt.nombre_empresa = nombre_empresa
                receipt._infilefel_establishment_street = direccion
                receipt.nit_empresa = nit_empresa
                receipt.infile_number = infile_number
                receipt.serie_venta = serie_venta
                receipt.infilefel_sat_uuid = infilefel_sat_uuid
                receipt.infilefel_sign_date = infilefel_sign_date

                receipt.nit_certificador = nit_certificador
                receipt.nombre_certificador = nombre_certificador
                receipt.frase_certificador = frase_certificador

                receipt.nombre_cliente = nombre_cliente
                receipt.nit = nit
                receipt.direccion_cliente = direccion_cliente
                receipt.fecha_factura = fecha_factura

            }
            return receipt
        }
    });


})
