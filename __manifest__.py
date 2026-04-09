# __manifest__.py
{
    'name': 'Match Ticket Booking',
    'version': '1.0',
    'summary': 'Manage users, tickets, bookings, and payments',
    'description': 'A complete module to manage football match tickets based on class diagram.',
    'author': 'Your Name',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv', # لا تنسى إعطاء الصلاحيات هنا
        'views/views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'installable': True,
'category': 'Sales', # أو ممكن تكتب 'Entertainment'
    'sequence': 1,       # السطر ده بيخليه يظهر في أول صفحة التطبيقات
}