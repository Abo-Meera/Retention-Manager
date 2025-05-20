# wizards/retention_report_wizard.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class RetentionReportWizard(models.TransientModel):
    _name = 'retention.report.wizard'
    _description = 'Retention Report Wizard'

    date_from = fields.Date(
        string='Date From',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1)
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
        default=lambda self: fields.Date.today()
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner'
    )
    state = fields.Selection([
        ('all', 'All'),
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('held', 'Held'),
        ('partially_released', 'Partially Released'),
        ('released', 'Released'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='all')
    report_type = fields.Selection([
        ('summary', 'Summary'),
        ('detailed', 'Detailed')
    ], string='Report Type', default='detailed')
    include_released = fields.Boolean(
        string='Include Released',
        default=False
    )

    def action_generate_report(self):
        self.ensure_one()
        
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]
        
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
            
        if self.state != 'all':
            domain.append(('state', '=', self.state))
        elif not self.include_released:
            domain.append(('state', 'not in', ['released', 'cancelled']))
            
        retentions = self.env['retention.line'].search(domain)
        if not retentions:
            raise UserError(_("No retention records found for the selected criteria."))
            
        if self.report_type == 'summary':
            return self._generate_summary_report(retentions)
        else:
            return self._generate_detailed_report(retentions)
            
    def _generate_summary_report(self, retentions):
        data = {
            'wizard_id': self.id,
            'retention_ids': retentions.ids,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'report_type': 'summary'
        }
        return self.env.ref('retention_management.action_retention_summary_report').report_action(self, data=data)
        
    def _generate_detailed_report(self, retentions):
        data = {
            'wizard_id': self.id,
            'retention_ids': retentions.ids,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'report_type': 'detailed'
        }
        return self.env.ref('retention_management.action_retention_detailed_report').report_action(self, data=data)