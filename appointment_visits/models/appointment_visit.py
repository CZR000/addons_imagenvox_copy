from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AppointmentVisit(models.Model):
    _name = 'appointment.visit'
    _description = 'Visita'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, start_time desc'

    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('Nuevo'),
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True,
        index=True,
    )
    doctor_id = fields.Many2one(
        'res.partner',
        string='Doctor',
        required=True,
        tracking=True,
        index=True,
    )
    visit_date = fields.Date(
        string='Fecha de visita',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    start_time = fields.Float(
        string='Hora de inicio',
        tracking=True,
        help='Hora de inicio en formato 24h (ej. 14.5 = 14:30).',
    )
    end_time = fields.Float(
        string='Hora final',
        tracking=True,
        help='Hora final en formato 24h (ej. 15.75 = 15:45).',
    )
    notes = fields.Text(
        string='Observaciones',
    )
    is_interview = fields.Boolean(
        string='Entrevista',
        tracking=True,
    )
    leave_brochure = fields.Boolean(
        string='Dejar folleto',
        tracking=True,
    )
    interviewee_type = fields.Selection(
        selection=[
            ('doctor', 'Doctor'),
            ('assistant', 'Asistente'),
            ('other', 'Otros'),
        ],
        string='Tipo de Entrevista',
        tracking=True,
    )

    @api.constrains('start_time', 'end_time')
    def _check_time_range(self):
        for rec in self:
            # Si ambas horas son 0.0 asumimos que no se cargaron y no validamos.
            if not rec.start_time and not rec.end_time:
                continue
            if not (0 <= rec.start_time < 24):
                raise ValidationError(_('La hora de inicio debe estar entre 00:00 y 23:59.'))
            if not (0 <= rec.end_time < 24):
                raise ValidationError(_('La hora final debe estar entre 00:00 y 23:59.'))
            if rec.end_time and rec.end_time <= rec.start_time:
                raise ValidationError(_('La hora final debe ser mayor que la hora de inicio.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'appointment.visit'
                ) or _('Nuevo')
        return super().create(vals_list)

    @api.depends('name', 'partner_id')
    def _compute_display_name(self):
        for rec in self:
            if rec.partner_id:
                rec.display_name = f'{rec.name} - {rec.partner_id.name}'
            else:
                rec.display_name = rec.name or _('Nuevo')