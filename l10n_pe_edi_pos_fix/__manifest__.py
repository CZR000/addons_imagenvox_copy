{
    "name": "L10n PE EDI PoS Fix (Timeout/CDR Error)",
    "version": "18.0.1.0.1",
    "category": "Accounting/Localizations/EDI",
    "summary": "Evita Error 500 en el PoS cuando SUNAT/OSE responde un CDR malformado.",
    "description": """
        Este módulo parchea el método _l10n_pe_edi_extract_cdr_status 
        para capturar excepciones cuando el nodo ResponseCode no existe en la respuesta del OSE.
        Permite que el PoS termine de guardar la orden y deja la factura para reintento.
    """,
    "author": "Tech Lead",
    "depends": ["l10n_pe_edi", "point_of_sale"],
    "data": [],
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
