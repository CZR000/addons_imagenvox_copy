# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class BulkUploadWizard(models.TransientModel):
    _name = 'documents.bulk.upload.wizard'
    _description = 'Asistente de subida masiva de documentos'

    folder_id = fields.Many2one(
        'documents.folders', string='Carpeta',
        required=True, readonly=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'documents_bulk_upload_wizard_ir_attachments_rel',
        'wizard_id', 'attachment_id',
        string='Archivos',
        help="Arrastra o selecciona los archivos que quieres subir a la carpeta.",
    )

    def action_upload(self):
        self.ensure_one()

        if not self.attachment_ids:
            raise UserError(_("Selecciona al menos un archivo para subir."))

        Attachment = self.env['ir.attachment']
        created = self.env['ir.attachment']

        # Opción 2: recrear attachments limpios (solo name, folder_id, datas)
        # y eliminar los temporales que generó el widget.
        for tmp in self.attachment_ids:
            created |= Attachment.create({
                'name': tmp.name,
                'folder_id': self.folder_id.id,
                'datas': tmp.datas,
            })

        # Limpiar los attachments temporales creados por el widget,
        # que quedaron vinculados al wizard transient.
        self.attachment_ids.sudo().unlink()

        # Abrir la carpeta para ver el resultado.
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'documents.folders',
            'res_id': self.folder_id.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }
