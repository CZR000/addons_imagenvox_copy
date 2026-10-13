# -*- coding: utf-8 -*-
from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_sale_line_taxes = fields.Boolean(
        related="company_id.show_sale_line_taxes",
        readonly=False,
    )

    show_sale_line_subtotal = fields.Boolean(
        related="company_id.show_sale_line_subtotal",
        readonly=False,
    )

    show_sale_totals_taxes = fields.Boolean(
        related="company_id.show_sale_totals_taxes",
        readonly=False,
    )