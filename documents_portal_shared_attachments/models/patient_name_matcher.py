# -*- coding: utf-8 -*-
"""
Lógica común para identificar al paciente desde el nombre del archivo.

Regla:
- El JPG (formato fijo) define el nombre del paciente y es el único que CREA carpeta.
  APELLIDO1_APELLIDO2_NOMBRE1[_NOMBRE2]_P1_2026-08-01_10_50.jpg
- PDF y otros solo BUSCAN carpeta: coinciden por palabras en orden, ignorando
  separadores/acentos/mayúsculas y permitiendo que falte el segundo nombre.
"""
import os
import re
import unicodedata

from odoo import models

JPG_NAME_RE = re.compile(
    r'^(?P<name>.+?)[\s_\-]+P\d+[\s_\-]+\d{4}-\d{2}-\d{2}', re.IGNORECASE
)
IMAGE_EXTS = {'.jpg', '.jpeg', '.png'}
# Palabras mínimas que deben coincidir en orden (ap. paterno, materno, nombre)
MIN_MATCH_TOKENS = 3


def strip_accents(value):
    s = unicodedata.normalize('NFD', value or '')
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def tokenize(value):
    """'Tarazona_Vargas-Énver' -> ['tarazona', 'vargas', 'enver']"""
    return [t for t in re.split(r'[^a-z0-9]+', strip_accents(value).lower()) if t]


def normalize_compact(value):
    """Clave de comparación. documents.folders.name_normalized debe usar ESTA función."""
    return ''.join(tokenize(value))


def extract_patient_from_jpg(filename):
    base, ext = os.path.splitext(filename or '')
    if ext.lower() not in IMAGE_EXTS:
        return None
    m = JPG_NAME_RE.match(base)
    if not m:
        return None
    tokens = tokenize(m.group('name'))
    return ' '.join(tokens).upper() if tokens else None


def extract_name_part(filename):
    """'TARAZONA VARGAS ENVER - INFORME PANORAMICO.pdf' -> 'TARAZONA VARGAS ENVER'"""
    base, _ext = os.path.splitext(filename or '')
    return re.split(r'\s+-\s+', base, maxsplit=1)[0]


def match_score(file_tokens, patient_tokens):
    """Palabras que coinciden en orden; la primera debe ser el apellido paterno."""
    if not file_tokens or not patient_tokens or file_tokens[0] != patient_tokens[0]:
        return 0
    score, pos = 0, 0
    for tok in file_tokens:
        try:
            pos = patient_tokens.index(tok, pos) + 1
        except ValueError:
            break
        score += 1
    return score


def is_match(file_tokens, patient_tokens):
    return match_score(file_tokens, patient_tokens) >= min(MIN_MATCH_TOKENS, len(patient_tokens))


class DocumentsPatientMatcher(models.AbstractModel):
    _name = 'documents.patient.matcher'
    _description = 'Identificación de paciente por nombre de archivo'

    def _find_existing_patient_folders(self, first_tokens):
        Folder = self.env['documents.folders'].sudo()
        first_tokens = sorted(first_tokens)
        if not first_tokens:
            return Folder
        domain = ['|'] * (len(first_tokens) - 1)
        for tok in first_tokens:
            domain.append(('name_normalized', '=like', tok + '%'))
        return Folder.search([('is_patient_directory', '=', True)] + domain)

    def _build_patient_plan(self, attachments):
        """
        Agrupa los archivos por paciente.
        :return: (groups, unmatched)
            groups: lista de dicts {'name', 'folder' (record o False), 'attachments'}
            unmatched: lista de (attachment, motivo)
        """
        Attachment = self.env['ir.attachment']
        groups = {}

        def add_candidate(name, folder=False):
            tokens = tokenize(name)
            if not tokens:
                return
            key = ''.join(tokens)
            for k, g in groups.items():
                if k == key or is_match(tokens, g['tokens']) or is_match(g['tokens'], tokens):
                    if not g['folder'] and len(tokens) > len(g['tokens']):
                        g['name'], g['tokens'] = name, tokens
                    if folder and not g['folder']:
                        g['folder'] = folder
                    return
            groups[key] = {'name': name, 'tokens': tokens, 'folder': folder,
                           'attachments': Attachment}

        # 1) Nombres desde los JPG
        jpg_names = {}
        for att in attachments:
            name = extract_patient_from_jpg(att.name)
            if name:
                jpg_names[att.id] = name

        # 2) Carpetas existentes candidatas (primero, para priorizarlas)
        first_tokens = set()
        for att in attachments:
            toks = tokenize(jpg_names.get(att.id) or extract_name_part(att.name))
            if toks:
                first_tokens.add(toks[0])
        for folder in self._find_existing_patient_folders(first_tokens):
            add_candidate(folder.name, folder)
        for name in jpg_names.values():
            add_candidate(name)

        # 3) Asignar cada archivo
        unmatched = []
        for att in attachments:
            file_tokens = tokenize(jpg_names.get(att.id) or extract_name_part(att.name))
            scored = sorted(
                ((match_score(file_tokens, g['tokens']), k)
                 for k, g in groups.items() if is_match(file_tokens, g['tokens'])),
                reverse=True,
            )
            if not scored:
                unmatched.append((att, 'No hay JPG ni carpeta de paciente con ese nombre'))
            elif len(scored) > 1 and scored[0][0] == scored[1][0]:
                names = ', '.join(groups[k]['name'] for _s, k in scored[:3])
                unmatched.append((att, 'Ambiguo, coincide con: %s' % names))
            else:
                groups[scored[0][1]]['attachments'] |= att

        result = [g for g in groups.values() if g['attachments']]
        result.sort(key=lambda g: g['name'])
        return result, unmatched

    def _get_or_create_patient_folder(self, name):
        """:return: (folder, created)"""
        Folder = self.env['documents.folders'].sudo()
        clean = ' '.join(tokenize(name)).upper()
        existing = Folder.search([
            ('is_patient_directory', '=', True),
            ('name_normalized', '=', normalize_compact(clean)),
        ], limit=1)
        if existing:
            return existing, False
        return Folder.create({'name': clean, 'is_patient_directory': True}), True