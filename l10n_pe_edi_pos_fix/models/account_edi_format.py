import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_pe_edi_extract_cdr_status(self, cdr):
        """
        Sobrescribe el método base para añadir programación defensiva 
        frente a respuestas malformadas de SUNAT u OSE.
        
        Respeta estrictamente el contrato del estándar: 
        Debe retornar un diccionario con 'code' y 'description'.
        """
        try:
            # 1. Ejecutamos la lógica estándar intacta
            return super()._l10n_pe_edi_extract_cdr_status(cdr)
            
        except AttributeError as e:
            # 2. Atrapamos el error específico de OSE/SUNAT sin ResponseCode
            if "'NoneType' object has no attribute 'text'" in str(e):
                _logger.error(
                    "Error EDI Perú: SUNAT/OSE devolvió una respuesta sin el nodo "
                    "ResponseCode. Posible error de certificado o caída del servicio. "
                    "Contenido recibido: %s", 
                    cdr
                )
                
                # 3. Retornamos la estructura EXACTA ('code', 'description') que Odoo 
                # usará en _l10n_pe_edi_retrieve_cdr y _l10n_pe_edi_sign_service_sunat_digiflow_common
                return {
                    'code': '9999', 
                    'description': 'Rechazo del servicio de SUNAT/OSE (Revise su Certificado Digital '
                                   'o conexión). La orden del PoS se guardó exitosamente. '
                                   'Por favor, reintente el envío de esta factura desde el backend.'
                }
                
            # Si es otro error, no interferimos
            raise e
