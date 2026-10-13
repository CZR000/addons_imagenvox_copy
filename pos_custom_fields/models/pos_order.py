# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    seller_tag_ids = fields.Many2many(
        'res.partner.category',
        'pos_order_partner_category_rel',
        'order_id',
        'category_id',
        string='Doctor',
        compute='_compute_seller_tag_ids',
        store=True,
        readonly=True
    )

    @api.depends('lines.user_id')
    def _compute_seller_tag_ids(self):
        """Calcula los tags basándose en los vendedores únicos de las líneas"""
        PartnerCategory = self.env['res.partner.category']
        
        for order in self:
            # Obtener todos los vendedores únicos de las líneas
            sellers = order.lines.mapped('user_id').filtered(lambda u: u.id)
            
            if not sellers:
                order.seller_tag_ids = [(5, 0, 0)]  # Limpiar tags
                continue
            
            # Crear o buscar tags para cada vendedor
            tags = self.env['res.partner.category']
            for seller in sellers:
                tag = PartnerCategory.search([('name', '=', seller.name)], limit=1)
                if not tag:
                    tag = PartnerCategory.create({'name': seller.name})
                tags |= tag
            
            order.seller_tag_ids = [(6, 0, tags.ids)]
