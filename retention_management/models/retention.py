# models/retention.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class RetentionLine(models.Model):
    _name = 'retention.line'
    _description = 'Retention Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default='New',
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        tracking=True
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    source_document = fields.Reference(
        selection=[
            ('sale.order', 'Sale Order'),
            ('account.move', 'Invoice'),
            ('purchase.order', 'Purchase Order')
        ],
        string='Source Document'
    )
    # Retention direction field to distinguish between customer and vendor retentions
    retention_direction = fields.Selection([
        ('customer', 'Customer Retention (We withhold)'),
        ('vendor', 'Vendor Retention (They withhold)')
    ], string='Retention Direction', required=True, default='customer', tracking=True)
    
    retention_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('amount', 'Fixed Amount')
    ], string='Retention Calculation', required=True, default='percentage', tracking=True)
    
    retention_percentage = fields.Float(
        string='Retention Percentage',
        tracking=True
    )
    base_amount = fields.Monetary(
        string='Base Amount (Inc. Tax)',
        currency_field='currency_id',
        tracking=True,
        help="The total amount including taxes on which retention is calculated"
    )
    retention_amount = fields.Monetary(
        string='Retention Amount',
        currency_field='currency_id',
        tracking=True
    )
    released_amount = fields.Monetary(
        string='Released Amount',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )
    remaining_amount = fields.Monetary(
        string='Remaining Amount',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('held', 'Held'),
        ('partially_released', 'Partially Released'),
        ('released', 'Released'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    release_date = fields.Date(
        string='Expected Release Date',
        tracking=True
    )
    release_ids = fields.One2many(
        'retention.release.line',
        'retention_id',
        string='Release Lines'
    )
    move_ids = fields.One2many(
        'account.move',
        'retention_id',
        string='Journal Entries'
    )
    notes = fields.Text(string='Notes')
    move_count = fields.Integer(
        string='Journal Entry Count',
        compute='_compute_move_count'
    )
    has_source_access = fields.Boolean(
        compute='_compute_has_source_access'
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('retention.line')
        return super().create(vals)

    @api.depends('retention_amount', 'release_ids.amount', 'release_ids.state')
    def _compute_amounts(self):
        for record in self:
            released = sum(record.release_ids.filtered(
                lambda r: r.state == 'posted').mapped('amount'))
            record.released_amount = released
            record.remaining_amount = record.retention_amount - released

    @api.depends('move_ids')
    def _compute_move_count(self):
        for record in self:
            record.move_count = len(record.move_ids)
    
    @api.depends('source_document')
    def _compute_has_source_access(self):
        for record in self:
            has_access = False
            if record.source_document:
                model, res_id = record.source_document.split(',')
                try:
                    self.env[model].browse(int(res_id)).check_access_rights('read')
                    has_access = True
                except (ValueError, AccessError):
                    has_access = False
            record.has_source_access = has_access

    @api.onchange('retention_type', 'retention_percentage', 'base_amount')
    def _onchange_retention_calculation(self):
        if self.retention_type == 'percentage' and self.base_amount:
            self.retention_amount = self.base_amount * (self.retention_percentage / 100)

    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft retentions can be confirmed."))
        self.state = 'confirmed'

    def action_hold(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed retentions can be held."))
            
        # Create journal entry for retention hold
        move = self._create_retention_hold_move()
        move.action_post()
        
        self.write({
            'state': 'held',
            'release_date': fields.Date.today() + relativedelta(days=int(
                self.env['ir.config_parameter'].sudo().get_param(
                    'retention_management.retention_release_days', '30')))
        })

    def _create_retention_hold_move(self):
        self.ensure_one()
        journal_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'retention_management.retention_journal_id'))
        if not journal_id:
            raise UserError(_("Please configure retention journal in settings."))
            
        retention_account_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'retention_management.retention_account_id'))
        if not retention_account_id:
            raise UserError(_("Please configure retention account in settings."))

        # Different accounting treatment based on retention direction
        if self.retention_direction == 'customer':
            # We are withholding from vendor
            debit_account_id = self.partner_id.property_account_payable_id.id
            credit_account_id = retention_account_id
            
            # Prepare line values
            debit_line = {
                'name': f'Retention Hold - {self.partner_id.name}',
                'account_id': debit_account_id,
                'partner_id': self.partner_id.id,
                'debit': self.retention_amount,
                'credit': 0.0,
            }
            
            credit_line = {
                'name': f'Retention Hold - {self.partner_id.name}',
                'account_id': credit_account_id,
                'partner_id': self.partner_id.id,
                'debit': 0.0,
                'credit': self.retention_amount,
            }
        else:
            # Vendor is withholding from us
            debit_account_id = retention_account_id
            credit_account_id = self.partner_id.property_account_receivable_id.id
            
            # Prepare line values
            debit_line = {
                'name': f'Retention Hold - {self.partner_id.name}',
                'account_id': debit_account_id,
                'partner_id': self.partner_id.id,
                'debit': self.retention_amount,
                'credit': 0.0,
            }
            
            credit_line = {
                'name': f'Retention Hold - {self.partner_id.name}',
                'account_id': credit_account_id,
                'partner_id': self.partner_id.id,
                'debit': 0.0,
                'credit': self.retention_amount,
            }
        
        # Add date_maturity for receivable/payable accounts - Updated for Odoo 16
        debit_account = self.env['account.account'].browse(debit_account_id)
        if debit_account.account_type in ('asset_receivable', 'liability_payable'):
            debit_line['date_maturity'] = self.release_date or self.date
        
        # Check if retention account is receivable/payable - Updated for Odoo 16
        credit_account = self.env['account.account'].browse(credit_account_id)
        if credit_account.account_type in ('asset_receivable', 'liability_payable'):
            credit_line['date_maturity'] = self.release_date or self.date

        move_vals = {
            'journal_id': journal_id,
            'date': self.date,
            'ref': f'Retention Hold - {self.name}',
            'retention_id': self.id,
            'line_ids': [
                (0, 0, debit_line),
                (0, 0, credit_line)
            ]
        }
        return self.env['account.move'].create(move_vals)

    def action_release(self, amount=None, date=None):
        self.ensure_one()
        if self.state not in ['held', 'partially_released']:
            raise UserError(_("Only held or partially released retentions can be released."))
            
        if not amount:
            amount = self.remaining_amount
        if amount > self.remaining_amount:
            raise UserError(_("Cannot release more than the remaining amount."))
            
        if not date:
            date = fields.Date.today()
        
        notes = False
        if self.env.context.get('auto_release'):
            notes = _("Automatically released on %s by the system.") % fields.Date.to_string(date)

        # Create release line
        release_line = self.env['retention.release.line'].create({
            'retention_id': self.id,
            'date': date,
            'amount': amount,
            'state': 'draft',
            'notes': notes,
        })
        
        # Create and post journal entry
        move = release_line._create_release_move()
        move.action_post()
        release_line.state = 'posted'
        
        # Update retention state
        if self.remaining_amount == 0:
            self.state = 'released'
        else:
            self.state = 'partially_released'
            
        # Post a message in the chatter
        if notes:
            self.message_post(body=notes)

    def action_cancel(self):
        self.ensure_one()
        if self.state in ['held', 'partially_released']:
            raise UserError(_("Cannot cancel retention with held amounts."))
        self.state = 'cancelled'
        
    def action_view_source(self):
        self.ensure_one()
        if not self.source_document:
            raise UserError(_("No source document found."))
            
        model, res_id = self.source_document.split(',')
        
        if model == 'sale.order':
            return {
                'name': _('Sale Order'),
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': int(res_id),
                'type': 'ir.actions.act_window',
            }
        elif model == 'account.move':
            return {
                'name': _('Invoice'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': int(res_id),
                'type': 'ir.actions.act_window',
            }
        elif model == 'purchase.order':
            return {
                'name': _('Purchase Order'),
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'res_id': int(res_id),
                'type': 'ir.actions.act_window',
            }
        else:
            return {'type': 'ir.actions.act_window_close'}
    
    def action_view_journal_entries(self):
        self.ensure_one()
        return {
            'name': _('Journal Entries'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.move_ids.ids)],
            'type': 'ir.actions.act_window',
        }

    @api.model
    def _auto_release_retentions(self):
        """Scheduled action to automatically release retentions that have reached their release date."""
        auto_release = self.env['ir.config_parameter'].sudo().get_param(
            'retention_management.auto_retention_release', 'False').lower() == 'true'
            
        if not auto_release:
            _logger.info("Auto-release of retentions is disabled.")
            return
            
        today = fields.Date.today()
        retentions_to_release = self.search([
            ('state', 'in', ['held', 'partially_released']),
            ('release_date', '<=', today),
            ('remaining_amount', '>', 0)
        ])
        
        _logger.info("Found %s retentions eligible for auto-release", len(retentions_to_release))
        
        for retention in retentions_to_release:
            try:
                retention.with_context(auto_release=True).action_release()
                self.env.cr.commit()  # Commit after each successful release
                _logger.info("Auto-released retention %s for partner %s", 
                             retention.name, retention.partner_id.name)
            except Exception as e:
                self.env.cr.rollback()
                _logger.error("Failed to auto-release retention %s: %s", retention.name, str(e))

class RetentionReleaseLine(models.Model):
    _name = 'retention.release.line'
    _description = 'Retention Release Line'
    _order = 'date desc, id desc'

    retention_id = fields.Many2one(
        'retention.line',
        string='Retention',
        required=True,
        ondelete='cascade'
    )
    date = fields.Date(
        string='Release Date',
        required=True,
        default=fields.Date.context_today
    )
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        required=True
    )
    currency_id = fields.Many2one(
        related='retention_id.currency_id',
        store=True
    )
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    notes = fields.Text(string='Notes')

    def _create_release_move(self):
        self.ensure_one()
        journal_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'retention_management.retention_journal_id'))
        retention_account_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'retention_management.retention_account_id'))

        # Different accounting treatment based on retention direction
        if self.retention_id.retention_direction == 'customer':
            # We are releasing withheld amount to vendor
            debit_account_id = retention_account_id
            credit_account_id = self.retention_id.partner_id.property_account_payable_id.id
            
            # Prepare line values
            debit_line = {
                'name': f'Retention Release - {self.retention_id.partner_id.name}',
                'account_id': debit_account_id,
                'partner_id': self.retention_id.partner_id.id,
                'debit': self.amount,
                'credit': 0.0,
            }
            
            credit_line = {
                'name': f'Retention Release - {self.retention_id.partner_id.name}',
                'account_id': credit_account_id,
                'partner_id': self.retention_id.partner_id.id,
                'debit': 0.0,
                'credit': self.amount,
            }
        else:
            # Vendor is releasing withheld amount to us
            debit_account_id = self.retention_id.partner_id.property_account_receivable_id.id
            credit_account_id = retention_account_id
            
            # Prepare line values
            debit_line = {
                'name': f'Retention Release - {self.retention_id.partner_id.name}',
                'account_id': debit_account_id,
                'partner_id': self.retention_id.partner_id.id,
                'debit': self.amount,
                'credit': 0.0,
            }
            
            credit_line = {
                'name': f'Retention Release - {self.retention_id.partner_id.name}',
                'account_id': credit_account_id,
                'partner_id': self.retention_id.partner_id.id,
                'debit': 0.0,
                'credit': self.amount,
            }
        
        # Check if accounts are receivable/payable - Updated for Odoo 16
        debit_account = self.env['account.account'].browse(debit_account_id)
        if debit_account.account_type in ('asset_receivable', 'liability_payable'):
            debit_line['date_maturity'] = self.date
        
        credit_account = self.env['account.account'].browse(credit_account_id)
        if credit_account.account_type in ('asset_receivable', 'liability_payable'):
            credit_line['date_maturity'] = self.date

        move_vals = {
            'journal_id': journal_id,
            'date': self.date,
            'ref': f'Retention Release - {self.retention_id.name}',
            'retention_id': self.retention_id.id,
            'line_ids': [
                (0, 0, debit_line),
                (0, 0, credit_line)
            ]
        }
        move = self.env['account.move'].create(move_vals)
        self.move_id = move.id
        return move

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    @api.model
    def create_retention_product(self):
        """Create the retention product if it doesn't exist."""
        retention_product = self.env['product.product'].search([
            ('default_code', '=', 'RETENTION')
        ], limit=1)
        
        if not retention_product:
            # Get default account for retention
            retention_account_id = int(self.env['ir.config_parameter'].sudo().get_param(
                'retention_management.retention_account_id', '0'))
                
            # Get income account
            income_account = False
            if retention_account_id:
                income_account = retention_account_id
            else:
                categ = self.env.ref('product.product_category_all', raise_if_not_found=False)
                if categ and categ.property_account_income_categ_id:
                    income_account = categ.property_account_income_categ_id.id
            
            retention_product = self.env['product.product'].create({
                'name': 'Retention',
                'type': 'service',
                'default_code': 'RETENTION',
                'categ_id': self.env.ref('product.product_category_all').id,
                'taxes_id': [(6, 0, [])],  # No taxes on retention
                'supplier_taxes_id': [(6, 0, [])],
                'sale_ok': True,
                'purchase_ok': False,
                'invoice_policy': 'order',
                'property_account_income_id': income_account or False,
            })
            _logger.info('Retention product created with ID: %s', retention_product.id)
            
        return retention_product