# -*- coding: utf-8 -*-
from odoo import _, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    show_sale_line_taxes = fields.Boolean(
        string="Mostrar Impuestos en PDF de Ventas",
        default=True,
    )

    show_sale_line_subtotal = fields.Boolean(
        string="Mostrar Importe en PDF de Ventas",
        default=True,
    )

    show_sale_totals_taxes = fields.Boolean(
        string="Mostrar Fila de Impuestos (IGV) en Totales",
        default=True,
    )
