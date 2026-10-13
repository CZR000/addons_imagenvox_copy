# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ShareToFoldersWizard(models.TransientModel):
    _name = 'documents.share.to.folders.wizard'
    _description = 'Compartir archivos a otras carpetas'

    source_folder_id = fields.Many2one(
        'documents.folders',
        string='Carpeta actual',
        readonly=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Archivos a compartir',
        required=True,
        domain="['|', ('folder_id', '=', source_folder_id), ('shared_folder_ids', 'in', source_folder_id)]"
    )
    target_folder_ids = fields.Many2many(
        'documents.folders',
        'wizard_share_target_folders_rel',
        'wizard_id',
        'folder_id',
        string='Compartir a estas carpetas',
        required=True,
        domain="[('id', '!=', source_folder_id), ('is_day_directory', '=', False)]",
    )

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        context = self.env.context
        current_folder_id = context.get('current_folder_id')
        if not current_folder_id and context.get('active_model') == 'documents.folders':
            current_folder_id = context.get('active_id')
        if current_folder_id:
            self._check_not_day_folder(self.env['documents.folders'].browse(current_folder_id))
            vals['source_folder_id'] = current_folder_id
        return vals

    @api.model
    def _check_not_day_folder(self, folder):
        if folder and folder.is_day_directory:
            raise UserError(_(
                "En las carpetas del día use el botón 'Clasificar archivos (masivo)'."
            ))

    def action_share(self):
        self.ensure_one()
        self._check_not_day_folder(self.source_folder_id)
        if not self.target_folder_ids:
            raise UserError(_('Debe seleccionar al menos una carpeta destino.'))
        if not self.attachment_ids:
            raise UserError(_('Debe seleccionar al menos un archivo.'))

        touched = self.env['documents.folders']
        for target in self.target_folder_ids:
            if self.attachment_ids._share_to_folder(target):
                touched |= target

        if len(touched) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'documents.folders',
                'res_id': touched.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}