# models/retention_settings.py
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Remove the 'default_' prefix from field names
    retention_percentage = fields.Float(
        string='Default Retention Percentage',
        config_parameter='retention_management.default_retention_percentage',
        default=5.0
    )
    retention_account_id = fields.Many2one(
        'account.account',
        string='Retention Account',
        config_parameter='retention_management.retention_account_id',
        domain=[('deprecated', '=', False)]
    )
    retention_journal_id = fields.Many2one(
        'account.journal',
        string='Retention Journal',
        config_parameter='retention_management.retention_journal_id'
    )
    auto_retention_release = fields.Boolean(
        string='Auto Release Retentions',
        config_parameter='retention_management.auto_retention_release'
    )
    retention_release_days = fields.Integer(
        string='Days Before Auto Release',
        config_parameter='retention_management.retention_release_days',
        default=30
    )