# -*- coding: utf-8 -*-
from odoo import api, fields, models


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    mega_menu_item_ids = fields.One2many(
        'website.menu.mega.item',
        'menu_id',
        string='Mega Menu Items',
        help='Items que aparecerán en el mega menú con sus submenús'
    )
    
    use_dynamic_mega_menu = fields.Boolean(
        string='Usar Mega Menú Dinámico',
        default=False,
        help='Si está activo, el mega menú se generará dinámicamente desde los items configurados'
    )
    
    @api.onchange('use_dynamic_mega_menu')
    def _onchange_use_dynamic_mega_menu(self):
        """Al activar dinámico, generar template base si no existe"""
        if self.use_dynamic_mega_menu and not self.mega_menu_content:
            self.mega_menu_content = self.env['ir.ui.view']._render_template(
                'website_mega_menu_submenu.dynamic_mega_menu_base'
            )