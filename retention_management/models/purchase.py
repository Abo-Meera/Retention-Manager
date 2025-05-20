# models/purchase.py - Update to show retention as a line item

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    retention_line_id = fields.Many2one(
        'retention.line',
        string='Retention',
        copy=False,
        readonly=True
    )
    retention_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('amount', 'Fixed Amount')
    ], string='Retention Calculation', default='percentage')
    retention_direction = fields.Selection([
        ('customer', 'Customer Retention (We withhold)'),
        ('vendor', 'Vendor Retention (They withhold)')
    ], string='Retention Direction', default='customer')  # Default for purchase is customer - we withhold from vendor
    retention_percentage = fields.Float(
        string='Retention Percentage',
        default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param(
            'retention_management.default_retention_percentage', '5.0'))
    )
    retention_amount = fields.Monetary(
        string='Retention Amount',
        currency_field='currency_id',
        compute='_compute_retention_amount',
        store=True,
        readonly=False
    )
    retention_product_id = fields.Many2one(
        'product.product',
        string='Retention Product',
        domain=[('default_code', '=', 'RETENTION')],
        default=lambda self: self.env['product.product'].search([('default_code', '=', 'RETENTION')], limit=1).id
    )
    retention_line_created = fields.Boolean(string="Retention Line Created", default=False)
    
    @api.depends('amount_total', 'retention_type', 'retention_percentage')
    def _compute_retention_amount(self):
        for order in self:
            if order.retention_type == 'percentage' and order.amount_total:
                order.retention_amount = order.amount_total * (order.retention_percentage / 100)
            elif not order.retention_type == 'amount':
                order.retention_amount = 0
                
    @api.onchange('retention_type', 'retention_amount', 'amount_total')
    def _onchange_retention_amount(self):
        if self.retention_type == 'amount' and self.amount_total:
            self.retention_percentage = (self.retention_amount / self.amount_total) * 100 if self.amount_total else 0
        self._create_retention_line_item()

    @api.onchange('retention_percentage', 'retention_direction')
    def _onchange_retention(self):
        self._compute_retention_amount()
        self._create_retention_line_item()

    def _create_retention_line(self):
        """Create the retention record in the system"""
        self.ensure_one()
        if self.retention_amount > 0:
            retention = self.env['retention.line'].create({
                'partner_id': self.partner_id.id,
                'source_document': f'{self._name},{self.id}',
                'retention_direction': self.retention_direction,
                'retention_type': self.retention_type,
                'retention_percentage': self.retention_percentage,
                'base_amount': self.amount_total,  # Including taxes
                'retention_amount': self.retention_amount,
                'currency_id': self.currency_id.id,
                'date': fields.Date.today(),
            })
            self.retention_line_id = retention.id
            retention.action_confirm()
            return retention
        return False

    def _create_retention_line_item(self):
        """Create or update a line item in the order to show retention"""
        self.ensure_one()
        
        retention_value = self.retention_amount if self.retention_amount else 0.0
        
        # Only process if there's a retention amount and we're in edit mode
        if not retention_value or not self.env.context.get('create_retention_line', True):
            return
            
        # Find existing retention line
        retention_line = self.order_line.filtered(lambda line: 
            line.product_id.id == self.retention_product_id.id)
            
        if retention_line:
            # Update existing line
            retention_line.with_context(force_compute=True).write({
                'price_unit': -retention_value,  # Negative value to reduce total
                'name': f'Retention ({self.retention_percentage}%)' if self.retention_type == 'percentage' 
                        else 'Retention (Fixed Amount)',
                'product_qty': 1,
            })
        else:
            # Create new line
            line_vals = {
                'order_id': self.id,
                'product_id': self.retention_product_id.id,
                'name': f'Retention ({self.retention_percentage}%)' if self.retention_type == 'percentage' 
                        else 'Retention (Fixed Amount)',
                'product_qty': 1,
                'price_unit': -retention_value,  # Negative value to reduce total
                'taxes_id': [(6, 0, [])],  # No taxes on retention
                'is_retention_line': True,
                'date_planned': fields.Date.today(),
                'product_uom': self.env.ref('uom.product_uom_unit').id,
            }
            self.env['purchase.order.line'].with_context(force_compute=True).create(line_vals)
            
        self.retention_line_created = True

    def button_confirm(self):
        """On confirm, make sure to update retention line and create retention record"""
        for order in self:
            order._create_retention_line_item()
        
        res = super().button_confirm()
        
        for order in self:
            order._create_retention_line()
        
        return res
        
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.retention_line_id:
            invoice_vals.update({
                'retention_direction': self.retention_direction,
                'retention_type': self.retention_type,
                'retention_percentage': self.retention_percentage,
                'retention_amount': self.retention_amount,
                'related_retention_id': self.retention_line_id.id,
            })
        return invoice_vals

# Add feature to the purchase order line model
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    is_retention_line = fields.Boolean(string="Is Retention Line", default=False)