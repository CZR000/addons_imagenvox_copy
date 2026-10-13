# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    shared_folder_ids = fields.Many2many(
        'documents.folders',
        'attachment_shared_folders_rel',
        'attachment_id',
        'folder_id',
        string='También visible en',
    )

    # ------------------------------------------------------------------
    # Sincronización automática paciente → doctores
    # ------------------------------------------------------------------
    def _linked_patient_folders(self):
        """{attachment_id: set(ids de carpetas de paciente con doctores donde está)}"""
        result = {}
        for att in self.sudo():
            folders = (att.folder_id | att.shared_folder_ids).filtered('doctor_folder_ids')
            result[att.id] = set(folders.ids)
        return result

    def _sync_doctor_folders(self, before):
        """Compara carpetas de paciente antes/después y comparte o quita en los doctores."""
        Folder = self.env['documents.folders'].sudo()
        after = self._linked_patient_folders()
        for att in self.sudo():
            old, new = before.get(att.id, set()), after.get(att.id, set())
            for patient in Folder.browse(list(new - old)):
                for doctor in patient.doctor_folder_ids:
                    att.with_context(skip_doctor_sync=True)._share_to_folder(doctor)
            for patient in Folder.browse(list(old - new)):
                patient._unshare_one_from_doctors(att)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('skip_doctor_sync'):
            records.filtered('folder_id')._sync_doctor_folders({})
        return records

    def write(self, vals):
        if self.env.context.get('skip_doctor_sync') or not (
                {'folder_id', 'shared_folder_ids'} & set(vals)):
            return super().write(vals)
        before = self._linked_patient_folders()
        res = super().write(vals)
        self._sync_doctor_folders(before)
        return res
    
    def _share_to_folder(self, folder):
        """
        Comparte los archivos (recordset) a `folder` en una sola escritura.
        Omite los que ya son de esa carpeta o ya estaban compartidos ahí.
        :return: recordset con los archivos que realmente se agregaron.
        """
        to_add = self.filtered(
            lambda a: a.folder_id.id != folder.id and folder.id not in a.shared_folder_ids.ids
        )
        if to_add:
            to_add.sudo().write({'shared_folder_ids': [(4, folder.id)]})
            portal_user = self.env['res.users'].sudo().search(
                [('portal_folder_id', '=', folder.id)], limit=1)
            if portal_user:
                to_add.sudo().write({'shared_user_ids': [(4, portal_user.id)]})
        return to_add
    
    def _propagate_portal_user_of_folder(self, folder_id):
        """
        Si la carpeta destino pertenece a un usuario portal
        (res.users.portal_folder_id apunta a ella), se agrega ese usuario
        a shared_user_ids para que también vea el archivo en su portal.
        """
        self.ensure_one()
        portal_user = self.env['res.users'].sudo().search(
            [('portal_folder_id', '=', folder_id)], limit=1)
        if portal_user:
            self.sudo().write({'shared_user_ids': [(4, portal_user.id)]})

    def _remove_portal_user_of_folder(self, folder_id):
        """
        Al quitar el archivo de una carpeta invitada: si el usuario portal
        de esa carpeta ya no tiene ninguna otra carpeta (dueña o invitada)
        que contenga el archivo, se retira de shared_user_ids.
        """
        self.ensure_one()
        portal_user = self.env['res.users'].sudo().search(
            [('portal_folder_id', '=', folder_id)], limit=1)
        if not portal_user:
            return
        remaining_folder_ids = [
            fid for fid in (self.folder_id | self.shared_folder_ids).ids
            if fid != folder_id
        ]
        still_has_folder = self.env['res.users'].sudo().search_count([
            ('id', '=', portal_user.id),
            ('portal_folder_id', 'in', remaining_folder_ids),
        ])
        if not still_has_folder:
            self.sudo().write({'shared_user_ids': [(3, portal_user.id)]})

    def action_remove_from_current_folder(self):
        """
        Botón 'Quitar de esta carpeta' en fila de archivo invitado:
        solo quita el ID del M2M, el archivo sigue en su carpeta dueña.
        """
        current_folder_id = self.env.context.get('current_folder_id')
        if not current_folder_id:
            raise UserError(_('No se pudo determinar la carpeta actual.'))
        for att in self:
            if current_folder_id in att.shared_folder_ids.ids:
                att._remove_portal_user_of_folder(current_folder_id)
                att.sudo().write({'shared_folder_ids': [(3, current_folder_id)]})
        return True

    def action_delete_from_current_folder(self):
        """
        Botón 'Eliminar' en fila de archivo dueña:
        si está compartido en otras carpetas, abre wizard de confirmación.
        Si no, borra directo.
        """
        self.ensure_one()
        if self.shared_folder_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Confirmar eliminación'),
                'res_model': 'documents.confirm.delete.attachment.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_attachment_id': self.id,
                },
            }
        self.unlink()
        return True
