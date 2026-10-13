# -*- coding: utf-8 -*-
from markupsafe import Markup, escape

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SharePatientsToDoctorsWizard(models.TransientModel):
    """
    Acción masiva desde la vista lista de carpetas de paciente:
    comparte TODOS los archivos de las carpetas seleccionadas a la carpeta
    portal de uno o varios doctores (usuarios portal).
    """
    _name = 'documents.share.patients.to.doctors.wizard'
    _description = 'Asignar carpetas de paciente a doctores'

    patient_folder_ids = fields.Many2many(
        'documents.folders',
        'wizard_share_doctor_patient_rel',
        'wizard_id',
        'folder_id',
        string='Carpetas de paciente',
        readonly=True,
    )
    ignored_count = fields.Integer(
        string='Carpetas ignoradas',
        readonly=True,
        help='Carpetas seleccionadas que no son de paciente.',
    )
    doctor_user_ids = fields.Many2many(
        'res.users',
        'wizard_share_doctor_user_rel',
        'wizard_id',
        'user_id',
        string='Doctor(es)',
        required=True,
        domain="[('share', '=', True)]",
        help='Usuarios del portal. Los archivos se comparten a su carpeta de portal.',
    )
    users_without_folder_ids = fields.Many2many(
        'res.users',
        compute='_compute_users_without_folder_ids',
        string='Doctores sin carpeta asignada',
    )
    attachment_count = fields.Integer(
        string='Archivos en total',
        compute='_compute_attachment_count',
    )

    # ------------------------------------------------------------------ base
    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        ctx = self.env.context
        if ctx.get('active_model') != 'documents.folders' or not ctx.get('active_ids'):
            return vals
        selected = self.env['documents.folders'].browse(ctx['active_ids'])
        patients = selected.filtered('is_patient_directory')
        if not patients:
            raise UserError(_('Seleccione al menos una carpeta de paciente.'))
        vals['patient_folder_ids'] = [(6, 0, patients.ids)]
        vals['ignored_count'] = len(selected) - len(patients)
        return vals

    @api.depends('doctor_user_ids')
    def _compute_users_without_folder_ids(self):
        for wiz in self:
            wiz.users_without_folder_ids = wiz.doctor_user_ids.sudo().filtered(
                lambda u: not u.portal_folder_id)

    @api.depends('patient_folder_ids')
    def _compute_attachment_count(self):
        for wiz in self:
            atts = wiz.patient_folder_ids.mapped('attachment_ids') | \
                wiz.patient_folder_ids.mapped('shared_attachment_ids')
            wiz.attachment_count = len(atts)

    # ------------------------------------------------------------ compartir
    def action_share(self):
        """Enlaza pacientes ↔ doctores y comparte los archivos existentes."""
        self.ensure_one()
        if not self.doctor_user_ids:
            raise UserError(_('Seleccione al menos un doctor.'))

        results = []          # [(doctor_user, folder, total_nuevos, [(paciente, n)], nuevos_enlaces)]
        no_folder = self.env['res.users']
        already = 0
        empty_patients = self.patient_folder_ids.filtered(lambda p: not p._patient_files())
        for user in self.doctor_user_ids.sudo():
            folder = user.portal_folder_id
            if not folder:
                no_folder |= user
                continue
            per_patient, new_links = [], 0
            for patient in self.patient_folder_ids.sudo():
                if folder not in patient.doctor_folder_ids:
                    patient.with_context(skip_doctor_sync=True).write(
                        {'doctor_folder_ids': [(4, folder.id)]})
                    new_links += 1
                if patient in empty_patients:
                    continue
                files = patient._patient_files()
                added = patient._share_files_to_doctor(folder)
                already += len(files) - len(added)
                if added:
                    per_patient.append((patient.name, len(added)))
            results.append((user, folder, sum(n for _p, n in per_patient), per_patient, new_links))

        return self.env['documents.share.result.wizard'].open_result(
            _('Resumen: asignar a doctores'),
            self._summary_html(results, already, empty_patients, no_folder),
        )

    def _summary_html(self, results, already, empty_patients, no_folder):
        html = ['<p>Carpetas de paciente procesadas: <b>%s</b>' % len(self.patient_folder_ids)]
        if self.ignored_count:
            html.append(' <span class="text-muted">(%s carpeta(s) ignoradas porque no son '
                        'de paciente)</span>' % self.ignored_count)
        html.append('</p>')

        if results and not sum(r[2] for r in results):
            html.append('<div class="alert alert-info">No se compartió ningún archivo nuevo: '
                        'los doctores ya tenían todos los archivos.</div>')
        for user, folder, n, per_patient, new_links in results:
            title = '%s <span class="text-muted">(carpeta: %s · %s paciente(s) asignado(s) nuevo(s))</span>' % (
                escape(user.name), escape(folder.complete_name or folder.name), new_links)
            if not n:
                html.append('<p><b>%s</b>: <span class="text-muted">sin archivos nuevos</span></p>'
                            % title)
                continue
            rows = ''.join('<li>%s <span class="text-muted">(%s archivo%s)</span></li>'
                           % (escape(p), c, '' if c == 1 else 's') for p, c in per_patient)
            html.append('<h5 class="text-primary">%s: %s archivo(s) nuevo(s) de %s paciente(s)</h5>'
                        '<ul>%s</ul>' % (title, n, len(per_patient), rows))
        if already:
            html.append('<p class="text-muted">%s archivo(s) ya estaban compartidos y se '
                        'omitieron.</p>' % already)
        if no_folder:
            html.append('<div class="alert alert-danger">No se compartió a: <b>%s</b>. '
                        'Estos usuarios no tienen carpeta de portal asignada.</div>'
                        % ', '.join(escape(n) for n in no_folder.mapped('name')))
        if empty_patients:
            html.append('<div class="alert alert-warning">Carpetas de paciente sin archivos: %s</div>'
                        % ', '.join(escape(n) for n in empty_patients.mapped('name')))
        return Markup(''.join(html))