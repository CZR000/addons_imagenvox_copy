# -*- coding: utf-8 -*-
import base64
from odoo import models, api, _


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Última actualización: solo cuando se sube un documento a una carpeta
        records.sudo().mapped('folder_id')._touch_last_update()
        return records

    def action_download(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/ir.attachment/{self.id}/datas?download=true',
            'target': 'self',
        }

    def action_replace_file(self, file_base64, file_name):
        self.ensure_one()
        self.sudo().write({
            'datas': file_base64,
            'name': file_name,
        })
        return True

    def action_preview_attachment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/ir.attachment/{self.id}/datas?download=false',
            'target': 'new',
        }