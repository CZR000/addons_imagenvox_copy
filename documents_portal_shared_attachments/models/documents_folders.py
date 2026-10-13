# -*- coding: utf-8 -*-
from markupsafe import Markup, escape

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .patient_name_matcher import normalize_compact


class DocumentFolders(models.Model):
    _inherit = 'documents.folders'

    shared_attachment_ids = fields.Many2many(
        'ir.attachment',
        'attachment_shared_folders_rel',
        'folder_id',
        'attachment_id',
        string='Archivos compartidos desde otras carpetas',
    )

    all_attachment_ids = fields.Many2many(
        'ir.attachment',
        compute='_compute_all_attachment_ids',
        string='Todos los archivos visibles',
    )

    name_normalized = fields.Char(
        compute='_compute_name_normalized',
        store=True,
        index=True,
    )

    is_day_directory = fields.Boolean(
        string='Es carpeta del día',
        help='Carpeta donde se suben los archivos del día. Muestra el botón '
             '"Clasificar archivos (masivo)" y oculta "Compartir a otras carpetas".',
    )
    last_classification_date = fields.Datetime(string='Última clasificación', readonly=True)
    last_classification_uid = fields.Many2one('res.users', string='Clasificado por', readonly=True)

    # ── Enlace paciente ↔ doctor ──────────────────────────────────────
    doctor_folder_ids = fields.Many2many(
        'documents.folders',
        'documents_patient_doctor_rel',
        'patient_folder_id',
        'doctor_folder_id',
        string='Doctores con acceso',
        domain="[('is_doctor_directory', '=', True)]",
        help='Todo archivo que entre a esta carpeta de paciente se comparte '
             'automáticamente con estos doctores.',
    )
    patient_folder_ids = fields.Many2many(
        'documents.folders',
        'documents_patient_doctor_rel',
        'doctor_folder_id',
        'patient_folder_id',
        string='Pacientes',
    )
    is_doctor_directory = fields.Boolean(
        string='Es carpeta de doctor',
        compute='_compute_is_doctor_directory',
        search='_search_is_doctor_directory',
        help='Carpeta de portal asignada a un usuario portal (doctor).',
    )
    
    @api.depends('name')
    def _compute_name_normalized(self):
        # Misma normalización que usa el match de pacientes:
        # sin acentos, minúsculas y sin ningún separador.
        for folder in self:
            folder.name_normalized = normalize_compact(folder.name) or False

    @api.depends('attachment_ids', 'shared_attachment_ids')
    def _compute_all_attachment_ids(self):
        for folder in self:
            folder.all_attachment_ids = folder.attachment_ids | folder.shared_attachment_ids

    @api.depends('attachment_ids', 'shared_attachment_ids')
    def _compute_attachment_count(self):
        for folder in self:
            folder.attachment_count = len(folder.attachment_ids) + len(folder.shared_attachment_ids)

    # ------------------------------------------------------------------
    # Enlace paciente ↔ doctor
    # ------------------------------------------------------------------
    @api.model
    def _doctor_folder_ids_set(self):
        users = self.env['res.users'].sudo().search([
            ('share', '=', True), ('portal_folder_id', '!=', False)])
        return set(users.mapped('portal_folder_id').ids)

    def _compute_is_doctor_directory(self):
        doctor_ids = self._doctor_folder_ids_set()
        for folder in self:
            folder.is_doctor_directory = folder.id in doctor_ids

    def _search_is_doctor_directory(self, operator, value):
        ids = list(self._doctor_folder_ids_set())
        positive = (operator == '=' and value) or (operator == '!=' and not value)
        return [('id', 'in' if positive else 'not in', ids)]

    def _get_link_pairs(self):
        """Pares (paciente_id, doctor_id) en los que participa self."""
        pairs = set()
        for folder in self.sudo():
            pairs |= {(folder.id, d.id) for d in folder.doctor_folder_ids}
            pairs |= {(p.id, folder.id) for p in folder.patient_folder_ids}
        return pairs

    @api.model
    def _apply_link_changes(self, added, removed):
        Folder = self.env['documents.folders'].sudo()
        for patient_id, doctor_id in added:
            Folder.browse(patient_id)._share_files_to_doctor(Folder.browse(doctor_id))
        for patient_id, doctor_id in removed:
            Folder.browse(patient_id)._unshare_files_from_doctor(Folder.browse(doctor_id))

    def _patient_files(self):
        self.ensure_one()
        return self.attachment_ids | self.shared_attachment_ids

    def _share_files_to_doctor(self, doctor):
        """Comparte todos los archivos de este paciente al doctor. Devuelve los agregados."""
        self.ensure_one()
        return self._patient_files().with_context(skip_doctor_sync=True)._share_to_folder(doctor)

    def _unshare_files_from_doctor(self, doctor):
        """Quita del doctor los archivos de este paciente (si no le llegan por otro paciente)."""
        self.ensure_one()
        other_patients = doctor.sudo().patient_folder_ids - self
        for att in self._patient_files():
            if doctor.id not in att.shared_folder_ids.ids:
                continue
            if (att.folder_id | att.shared_folder_ids) & other_patients:
                continue
            att._remove_portal_user_of_folder(doctor.id)
            att.sudo().with_context(skip_doctor_sync=True).write(
                {'shared_folder_ids': [(3, doctor.id)]})

    def _unshare_one_from_doctors(self, att):
        """El archivo salió de este paciente: quitarlo de sus doctores."""
        self.ensure_one()
        for doctor in self.sudo().doctor_folder_ids:
            other_patients = doctor.patient_folder_ids - self
            if doctor.id not in att.shared_folder_ids.ids:
                continue
            if (att.folder_id | att.shared_folder_ids) & other_patients:
                continue
            att._remove_portal_user_of_folder(doctor.id)
            att.sudo().with_context(skip_doctor_sync=True).write(
                {'shared_folder_ids': [(3, doctor.id)]})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('skip_doctor_sync'):
            self._apply_link_changes(records._get_link_pairs(), set())
        return records

    def write(self, vals):
        if self.env.context.get('skip_doctor_sync') or not (
                {'doctor_folder_ids', 'patient_folder_ids'} & set(vals)):
            return super().write(vals)
        before = self._get_link_pairs()
        res = super().write(vals)
        after = self._get_link_pairs()
        self._apply_link_changes(after - before, before - after)
        return res
    
    # ------------------------------------------------------------------
    # Clasificar archivos (masivo) — solo carpetas del día
    # ------------------------------------------------------------------
    def action_classify_documents(self):
        self.ensure_one()
        if not self.is_day_directory:
            raise UserError(_('Esta acción solo está disponible en carpetas del día.'))

        Matcher = self.env['documents.patient.matcher']
        attachments = self.attachment_ids | self.shared_attachment_ids
        groups, unmatched = Matcher._build_patient_plan(attachments)

        created, updated = [], []
        already = 0
        for g in groups:
            if g['folder']:
                folder, is_new = g['folder'], False
            else:
                folder, is_new = Matcher._get_or_create_patient_folder(g['name'])
            added = g['attachments']._share_to_folder(folder)
            already += len(g['attachments']) - len(added)
            if is_new:
                created.append((folder.name, len(added)))
            elif added:
                updated.append((folder.name, len(added)))

        self.sudo().write({
            'last_classification_date': fields.Datetime.now(),
            'last_classification_uid': self.env.uid,
        })
        return self.env['documents.share.result.wizard'].open_result(
            _('Resumen de clasificación'),
            self._classification_summary_html(len(attachments), created, updated, already, unmatched),
        )

    def _classification_summary_html(self, total, created, updated, already, unmatched):
        def items(rows):
            return ''.join(
                '<li>%s <span class="text-muted">(%s archivo%s)</span></li>'
                % (escape(name), n, '' if n == 1 else 's') for name, n in rows)

        html = ['<p>Archivos revisados: <b>%s</b></p>' % total]
        html.append('<h5 class="text-success">Carpetas creadas: %s</h5>' % len(created))
        html.append('<ul>%s</ul>' % items(created) if created
                    else '<p class="text-muted">Ninguna</p>')
        html.append('<h5 class="text-primary">Carpetas actualizadas (solo se agregaron archivos): %s</h5>'
                    % len(updated))
        html.append('<ul>%s</ul>' % items(updated) if updated
                    else '<p class="text-muted">Ninguna</p>')
        if not created and not updated:
            html.append('<div class="alert alert-info">No se creó ni actualizó ninguna carpeta: '
                        'todos los archivos ya estaban clasificados.</div>')
        if already:
            html.append('<p class="text-muted">%s archivo(s) ya estaban en la carpeta de su '
                        'paciente y se omitieron.</p>' % already)
        if unmatched:
            rows = ''.join('<li>%s <span class="text-muted">— %s</span></li>'
                           % (escape(att.name), escape(reason)) for att, reason in unmatched)
            html.append('<div class="alert alert-warning"><b>%s archivo(s) no se pudieron '
                        'clasificar.</b> Corrija el nombre del archivo (o suba el JPG del '
                        'paciente) y vuelva a clasificar.<ul class="mb-0">%s</ul></div>'
                        % (len(unmatched), rows))
        return Markup(''.join(html))