# models/sale.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
    ], string='Retention Direction', default='vendor')  # Default for sales is vendor - they withhold from us
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

    def _create_retention_line(self):
        self.ensure_one()
        if self.retention_amount > 0:
            retention = self.env['retention.line'].create({
                'partner_id': self.partner_id.id,
                'source_document': f'{self._name},{self.id}',
                'retention_direction': self.retention_direction,
                'retention_type': self.retention_type,
                'retention_percentage': self.retention_percentage,
                'base_amount': self.amount_total,
                'retention_amount': self.retention_amount,
                'currency_id': self.currency_id.id,
                'date': fields.Date.today(),
            })
            self.retention_line_id = retention.id
            retention.action_confirm()