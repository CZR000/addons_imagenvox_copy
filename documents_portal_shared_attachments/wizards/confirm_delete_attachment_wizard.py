# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ConfirmDeleteAttachmentWizard(models.TransientModel):
    _name = 'documents.confirm.delete.attachment.wizard'
    _description = 'Confirmar borrado de archivo compartido'

    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Archivo',
        required=True,
        readonly=True,
    )
    shared_folder_ids = fields.Many2many(
        'documents.folders',
        related='attachment_id.shared_folder_ids',
        readonly=True,
    )
    shared_folder_count = fields.Integer(
        compute='_compute_shared_folder_count',
        string='Cantidad de carpetas donde está compartido',
    )

    @api.depends('shared_folder_ids')
    def _compute_shared_folder_count(self):
        for w in self:
            w.shared_folder_count = len(w.shared_folder_ids)

    def action_confirm_delete(self):
        self.ensure_one()
        self.attachment_id.unlink()
        return {'type': 'ir.actions.act_window_close'}
