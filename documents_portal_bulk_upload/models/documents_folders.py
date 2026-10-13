# -*- coding: utf-8 -*-
from odoo import models, _


class DocumentsFolders(models.Model):
    _inherit = 'documents.folders'

    def action_bulk_upload(self):
        """Abre el asistente de subida masiva con la carpeta actual precargada."""
        self.ensure_one()
        return {
            'name': _('Subir documentos'),
            'type': 'ir.actions.act_window',
            'res_model': 'documents.bulk.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_folder_id': self.id},
        }
