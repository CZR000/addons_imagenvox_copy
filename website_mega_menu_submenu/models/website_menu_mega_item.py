# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WebsiteMenuMegaItem(models.Model):
    _name = 'website.menu.mega.item'
    _description = 'Mega Menu Item'
    _order = 'sequence, id'
    
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True
    )
    
    menu_id = fields.Many2one(
        'website.menu',
        string='Menú Padre',
        required=True,
        ondelete='cascade'
        # REMOVIDO EL DOMAIN que causaba el error
    )
    
    url = fields.Char(
        string='URL',
        help='URL del item. Dejar vacío si tiene sub-items'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    icon = fields.Char(
        string='Ícono',
        default='fa-check-square',
        help='Clase de Font Awesome (ej: fa-check-square, fa-star)'
    )
    
    has_submenu = fields.Boolean(
        string='Tiene Submenú',
        compute='_compute_has_submenu',
        store=True
    )
    
    submenu_item_ids = fields.One2many(
        'website.menu.mega.subitem',
        'parent_item_id',
        string='Sub-items'
    )
    
    new_window = fields.Boolean(
        string='Nueva Ventana',
        default=False
    )
    
    is_visible = fields.Boolean(
        string='Visible',
        default=True
    )
    
    column_position = fields.Integer(
        string='Posición de Columna',
        default=1,
        help='Posición en el grid del mega menú (1-12)'
    )
    
    column_width = fields.Integer(
        string='Ancho de Columna',
        default=2,
        help='Ancho en el grid (1-12)'
    )
    
    @api.depends('submenu_item_ids')
    def _compute_has_submenu(self):
        for item in self:
            item.has_submenu = bool(item.submenu_item_ids)
    
    @api.constrains('url', 'submenu_item_ids')
    def _check_url_or_submenu(self):
        for item in self:
            if item.url and item.submenu_item_ids:
                raise ValidationError(_(
                    'Un item no puede tener URL y sub-items al mismo tiempo. '
                    'Elija una de las dos opciones.'
                ))


class WebsiteMenuMegaSubitem(models.Model):
    _name = 'website.menu.mega.subitem'
    _description = 'Mega Menu Sub-item'
    _order = 'sequence, id'
    
    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True
    )
    
    parent_item_id = fields.Many2one(
        'website.menu.mega.item',
        string='Item Padre',
        required=True,
        ondelete='cascade'
    )
    
    url = fields.Char(
        string='URL',
        required=True,
        default='/'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    
    icon = fields.Char(
        string='Ícono',
        default='fa-angle-right',
        help='Clase de Font Awesome'
    )
    
    new_window = fields.Boolean(
        string='Nueva Ventana',
        default=False
    )
    
    is_visible = fields.Boolean(
        string='Visible',
        default=True
    )