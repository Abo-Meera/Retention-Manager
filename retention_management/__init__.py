# __init__.py
from . import models
from . import wizards
from . import reports

def post_init_hook(cr, registry):
    """Post init hook for creating retention product"""
    # Use a simpler approach to call the function directly
    from odoo import api, SUPERUSER_ID
    
    # Create a new Environment with SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Call the function to create the retention product
    product_model = env['product.product']
    if hasattr(product_model, 'create_retention_product'):
        product_model.create_retention_product()

def pre_init_hook(cr):
    pass

def uninstall_hook(cr, registry):
    pass