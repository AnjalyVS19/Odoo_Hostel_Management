{
    'name': "Hostel Management",
    'version': '1.0',
    'summary': "Manage all activities in a hostel",
    'sequence': 1,
    'application':True,
    'depends': ['base', 'mail', 'account', 'product'],
    'data' : [
        'data/rent_product.xml',
        'data/hostel_management_sequence.xml',
        'data/student_sequence.xml',
        'views/room_management_views.xml',
        'views/student_views.xml',
        'views/facilities_view.xml',
        'views/leave_request_views.xml',
        'views/invoice_views.xml',
        'views/hostel_management_menu.xml',
        'security/ir.model.access.csv',
        'data/facilities_data.xml'
    ]
}