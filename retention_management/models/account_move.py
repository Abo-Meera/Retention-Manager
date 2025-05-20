# models/account_move.py
# This file should be created or updated in your module

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    # Add this field to match the One2many relationship in RetentionLine
    retention_id = fields.Many2one(
        'retention.line',
        string='Retention Record',
        copy=False,
        help="Retention record if this move is a retention journal entry"
    )
    
    # Keep your other retention-related fields
    retention_line_id = fields.Many2one(
        'retention.line',
        string='Retention',
        copy=False,
        readonly=True
    )
    related_retention_id = fields.Many2one(
        'retention.line',
        string='Related Retention',
        help="Retention created from the sales/purchase order"
    )
    retention_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('amount', 'Fixed Amount')
    ], string='Retention Calculation', default='percentage')
    retention_direction = fields.Selection([
        ('customer', 'Customer Retention (We withhold)'),
        ('vendor', 'Vendor Retention (They withhold)')
    ], string='Retention Direction')
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
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
                move.retention_amount = 0
                continue
                
            if move.retention_type == 'percentage' and move.amount_total:
                move.retention_amount = move.amount_total * (move.retention_percentage / 100)
            elif not move.retention_type == 'amount':
                move.retention_amount = 0
                
    @api.onchange('retention_type', 'retention_amount', 'amount_total')
    def _onchange_retention_amount(self):
        if self.retention_type == 'amount' and self.amount_total:
            self.retention_percentage = (self.retention_amount / self.amount_total) * 100 if self.amount_total else 0
            
    @api.onchange('move_type')
    def _onchange_move_type(self):
        # Set the appropriate retention direction based on the invoice type
        if self.move_type in ('out_invoice', 'out_refund'):
            self.retention_direction = 'vendor'  # Customer withholding from us
        elif self.move_type in ('in_invoice', 'in_refund'):
            self.retention_direction = 'customer'  # We withholding from vendor

    def _create_retention_line(self):
        self.ensure_one()
        if self.retention_amount > 0 and self.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
            retention = self.env['retention.line'].create({
                'partner_id': self.partner_id.id,
                'source_document': f'{self._name},{self.id}',
                'retention_direction': self.retention_direction,
                'retention_type': self.retention_type,
                'retention_percentage': self.retention_percentage,
                'base_amount': self.amount_total,
                'retention_amount': self.retention_amount,
                'currency_id': self.currency_id.id,
                'date': self.invoice_date or fields.Date.today(),
            })
            self.retention_line_id = retention.id
            retention.action_confirm()
            return retention
        return False

    def action_post(self):
        result = super().action_post()
        for move in self:
            # Process any invoice with retention
            if move.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund') and move.retention_amount > 0:
                # If there's already a related retention from SO/PO, don't create a new one
                if move.related_retention_id:
                    move.retention_line_id = move.related_retention_id
                    if move.related_retention_id.state == 'confirmed':
                        move.related_retention_id.action_hold()
                else:
                    retention = move._create_retention_line()
                    if retention:
                        retention.action_hold()
        return result
        
    def _reverse_moves(self, default_values_list=None, cancel=False):
        if default_values_list is None:
            default_values_list = [{} for move in self]
            
        for move, default_values in zip(self, default_values_list):
            # Only block reversals for retentions that still have held amounts
            # Released or cancelled retentions should allow reversal
            if move.retention_line_id and move.retention_line_id.state in ['held', 'partially_released']:
                raise UserError(_(
                    "You cannot reverse invoice %s as it has a retention in state %s. "
                    "Please release the retention first.", 
                    move.name, move.retention_line_id.state
                ))
                
        result = super()._reverse_moves(default_values_list=default_values_list, cancel=cancel)
        return result
        
    def button_draft(self):
        for move in self:
            # Only block reset to draft for retentions that still have held amounts
            if move.retention_line_id and move.retention_line_id.state in ['held', 'partially_released']:
                raise UserError(_(
                    "You cannot reset to draft invoice %s as it has a retention in state %s. "
                    "Please release the retention first.", 
                    move.name, move.retention_line_id.state
                ))
                
        result = super().button_draft()
        return result
        
    def action_view_retention(self):
        self.ensure_one()
        if not self.retention_line_id:
            raise UserError(_("No retention exists for this invoice."))
            
        return {
            'name': _('Retention'),
            'view_mode': 'form',
            'res_model': 'retention.line',
            'res_id': self.retention_line_id.id,
            'type': 'ir.actions.act_window',
        }