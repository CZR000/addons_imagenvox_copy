from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DocumentFolders(models.Model):
    _name = 'documents.folders'
    _description = 'Directory'
    _parent_name = 'parent_folder_id'
    _order = 'name'
    _rec_name = 'complete_name'

    name = fields.Char(string='Name', required=True)
    image = fields.Binary(string="Image")
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    sequence = fields.Integer('Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    parent_folder_id = fields.Many2one('documents.folders', string='Parent Folder', ondelete="cascade",
                                       domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    children_folder_ids = fields.One2many('documents.folders', 'parent_folder_id', string="Sub Folders")
    attachment_ids = fields.One2many('ir.attachment', 'folder_id', string="Attachments")
    model_id = fields.Many2one('ir.model', string='Model')
    attachment_count = fields.Integer(compute="_compute_attachment_count")
    folder_count = fields.Integer(compute="_compute_folder_count")
    is_personal_directory = fields.Boolean(string="Is Personal Document", default=False)
    is_portal_directory = fields.Boolean(string="Is Portal Document", default=False)

    # Odoo 17+: name_get() ya no existe -> se usa _compute_display_name
    @api.depends('complete_name', 'name')
    @api.depends_context('hierarchical_naming')
    def _compute_display_name(self):
        hierarchical = self.env.context.get('hierarchical_naming', True)
        for folder in self:
            folder.display_name = (folder.complete_name if hierarchical else folder.name) or ''

    @api.model
    def name_create(self, name):
        record = self.create({'name': name})
        return record.id, record.display_name

    @api.depends('name', 'parent_folder_id.complete_name')
    def _compute_complete_name(self):
        for folder in self:
            if folder.parent_folder_id:
                folder.complete_name = '%s / %s' % (folder.parent_folder_id.complete_name, folder.name)
            else:
                folder.complete_name = folder.name

    @api.constrains('parent_folder_id')
    def _check_parent_folder_id(self):
        if self._has_cycle():
            raise ValidationError(_('You cannot create recursive folder.'))

    @api.depends('children_folder_ids')
    def _compute_folder_count(self):
        for record in self:
            record.folder_count = len(record.children_folder_ids)

    @api.depends()
    def _compute_attachment_count(self):
        groups = self.env['ir.attachment']._read_group(
            [('folder_id', 'in', self.ids)], ['folder_id'], ['__count'])
        counts = {folder.id: count for folder, count in groups}
        for record in self:
            record.attachment_count = counts.get(record.id, 0)

    @api.constrains('model_id')
    def _check_model(self):
        for folder in self:
            if not folder.model_id:
                continue
            count = self.sudo().search_count([('model_id', '=', folder.model_id.id)])
            if count > 1:
                raise ValidationError(_('This models directory has already been established.!'))

    def action_see_attachments(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'domain': [('folder_id', '=', self.id)],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'views': [(False, 'list'), (False, 'form')],
            'view_mode': 'list,form',
            'context': {'default_folder_id': self.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered('model_id'):
            # Solo los adjuntos del modelo de la carpeta (antes recorría TODOS los adjuntos)
            self.env['ir.attachment'].sudo().search([
                ('res_model', '=', record.model_id.model),
            ]).write({'folder_id': record.id})
        return records

    def unlink(self):
        personal_folder = self.env.ref('documents_portal_management.personal_folder', raise_if_not_found=False)
        shared_folder = self.env.ref('documents_portal_management.portal_folder', raise_if_not_found=False)
        protected_ids = {f.id for f in (personal_folder, shared_folder) if f}
        if protected_ids & set(self.ids):
            raise UserError(_("Sorry...! you can't delete Personal/Shared folder, you can rename it."))
        return super().unlink()