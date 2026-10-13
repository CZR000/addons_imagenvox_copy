# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ShareResultWizard(models.TransientModel):
    """Popup de resumen reutilizable (clasificación y compartir a doctores)."""
    _name = 'documents.share.result.wizard'
    _description = 'Resumen de operación sobre documentos'

    summary_html = fields.Html(string='Resumen', readonly=True, sanitize=False)

    @api.model
    def open_result(self, title, summary_html):
        result = self.create({'summary_html': summary_html})
        return {
            'type': 'ir.actions.act_window',
            'name': title,
            'res_model': self._name,
            'res_id': result.id,
            'view_mode': 'form',
            'target': 'new',
        }