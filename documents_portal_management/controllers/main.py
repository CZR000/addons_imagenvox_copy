import json
import base64
import logging
import werkzeug

from odoo import http
from odoo.http import request

from odoo.tools import html_escape

class IrAttachemntsShareController(http.Controller):
    
    @http.route('/web/get_attachments/token/<string:token>', type='http', auth="none")
    def get_attachments(self, token , **kwargs):
        try:
            ir_attachment_env = request.env['ir.attachment']
            ir_attachment = ir_attachment_env.sudo().search([('access_token', '=', token)])
            if ir_attachment:
                for attachment in ir_attachment:                    
                    content = base64.b64decode(attachment.datas)
                    disposition = 'attachment; filename=%s' % werkzeug.urls.url_quote(attachment.name)                    
                    return request.make_response(
                        content,
                        [('Content-Length', len(content)),
                         ('Content-Type', attachment.mimetype),
                         ('Content-Disposition', disposition)])
            else:
                error = {
                    'code': 200,
                    'message': "Unable to locate the attachments",
                }
            return request.make_response(html_escape(json.dumps(error)))
            
        except Exception as e:
            se = http.serialize_exception(e)
            error = {
                'code': 200,
                'message': "Error - Odoo Server Error",
            }
            return request.make_response(html_escape(json.dumps(error)))
    
    @http.route('/web/get_attachments_data', type='http', auth="user")
    def get_attachments_data(self, id, **kwargs):
        try:
            ir_attachment_env = request.env['ir.attachment']
            ir_attachment = ir_attachment_env.sudo().browse(int(id))

            if not ir_attachment or not ir_attachment.exists():
                return request.make_response(
                    json.dumps({'error': True, 'message': "Attachment not found"}),
                    [('Content-Type', 'application/json')]
                )


            is_accessible = False
            if request.env.user.id == ir_attachment.create_uid.id:
                is_accessible = True
            elif request.env.user.id in ir_attachment.shared_user_ids.ids:
                is_accessible = True

            if not is_accessible:
                return request.make_response(
                    json.dumps({'error': True, 'message': "You do not have permission to access this attachment"}),
                    [('Content-Type', 'application/json')]
                )

            if not ir_attachment or not ir_attachment.datas:
                return request.make_response(
                    json.dumps({'error': True, 'message': "Attachment not found"}),
                    [('Content-Type', 'application/json')]
                )

            content = base64.b64decode(ir_attachment.datas)
            filename = ir_attachment.name or 'attachment'
            mimetype = ir_attachment.mimetype or 'application/octet-stream'

            return request.make_response(
                content,
                headers=[
                    ('Content-Type', mimetype),
                    ('Content-Disposition', f'attachment; filename="{filename}"'),
                ]
            )
        except Exception as e:
            return request.make_response(
                json.dumps({'error': True, 'message': f"An error occurred: {str(e)}"}),
                [('Content-Type', 'application/json')]
            )