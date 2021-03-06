# -*- coding: utf-8 -*-
# Copyright (c) 2017 Consultoría Informática Studio 73 S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_invoices(self):
        """
        Según la documentación de la AEAT, la operación de importación se
        registra con TipoFactura = F5, sin FechaOperacion y con el NIF de la
        propia compañia en IDEmisorFactura y Contraparte
        Más información en: 8.1.2.2.Ejemplo mensaje XML de alta de importación
        en el documento de descripción de los servicios web:
        http://bit.ly/2rGWiAI

        """
        res = super(AccountInvoice, self)._get_invoices()
        if res.get('FacturaRecibida', False):
            if self.is_dua_sii_invoice():
                res['FacturaRecibida']['TipoFactura'] = 'F5'
                res['FacturaRecibida'].pop('FechaOperacion', None)
                res['FacturaRecibida']['IDEmisorFactura'] = \
                    {'NIF': self.company_id.vat[2:]}
                res['IDFactura']['IDEmisorFactura'] = \
                    {'NIF': self.company_id.vat[2:]}
                res['FacturaRecibida']['Contraparte']['NIF'] = \
                    self.company_id.vat[2:]
                res['FacturaRecibida']['Contraparte']['NombreRazon'] = \
                    self.company_id.name
            if self.registration_key.code == '13':
                res['FacturaRecibida']['TipoFactura'] = 'F6'
            if self.type in ['in_refund']:
                res['FacturaRecibida']['TipoFactura'] = 'R4'
        return res

    @api.multi
    def is_dua_sii_invoice(self):
        """
        :return:
        """
        self.ensure_one()
        if self.fiscal_position_id.name == u'Importación con DUA':
            if self.tax_line_ids.filtered(
                    lambda x: x.tax_id.description in
                    ['P_IVA21_IBC', 'P_IVA10_IBC', 'P_IVA4_IBC',
                     'P_IVA21_IBI', 'P_IVA10_IBI', 'P_IVA4_IBI',
                     'P_IVA21_SP_EX', 'P_IVA10_SP_EX',
                     'P_IVA4_SP_EX']
            ):
                return True
        return False

    @api.multi
    def is_sii_invoice(self):
        """ is_sii_invoice() -> bool
            Check if the invoice must be not sended to AEAT because is
            a supplier DUA invoice, in that case should be sended
            the freight forwarder invoice instead.
            :param
            :return: bool
        """
        self.ensure_one()
        if self.fiscal_position_id.name == u'Importación con DUA' and \
                not self.is_dua_sii_invoice():
            return False
        return True
