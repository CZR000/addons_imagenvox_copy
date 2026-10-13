{
    'name': 'Appointment Visits',
    'version': '18.0.2.1.0',
    'category': 'Services/Appointment',
    'summary': 'Registro de visitas (Cliente/Doctor) dentro del modulo de Citas',
    'author': 'Sinetics',
    'website': 'https://sinetics.com.pe',
    'license': 'LGPL-3',
    'depends': ['appointment', 'contacts', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/appointment_visit_views.xml',
    ],
    'installable': True,
    'application': True,
}
