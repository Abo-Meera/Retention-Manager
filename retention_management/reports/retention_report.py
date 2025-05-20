# reports/retention_report.py
from odoo import models, api, _
from datetime import datetime
import io
import xlsxwriter

class RetentionReport(models.AbstractModel):
    _name = 'report.retention_management.retention_report'
    _description = 'Retention Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            return {}
            
        wizard_id = data.get('wizard_id')
        wizard = self.env['retention.report.wizard'].browse(wizard_id)
        retention_ids = data.get('retention_ids', [])
        retentions = self.env['retention.line'].browse(retention_ids)
        
        return {
            'doc_ids': docids,
            'doc_model': 'retention.report.wizard',
            'docs': wizard,
            'retentions': retentions,
            'date_from': data.get('date_from'),
            'date_to': data.get('date_to'),
            'report_type': data.get('report_type'),
        }

class RetentionReportXlsx(models.AbstractModel):
    _name = 'report.retention_management.retention_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Retention Report XLSX'
    
    def generate_xlsx_report(self, workbook, data, objects):
        wizard = self.env['retention.report.wizard'].browse(data.get('wizard_id'))
        retention_ids = data.get('retention_ids', [])
        retentions = self.env['retention.line'].browse(retention_ids)
        report_type = data.get('report_type')
        
        # Create worksheet
        sheet = workbook.add_worksheet('Retention Report')
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'border': 1,
            'bg_color': '#D3D3D3',
        })
        
        subheader_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 12,
            'border': 1,
            'bg_color': '#E8E8E8',
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
        })
        
        amount_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
        })
        
        date_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd',
        })
        
        # Set column widths
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 15)
        
        # Add title
        sheet.merge_range('A1:G1', 'Retention Report', header_format)
        sheet.merge_range('A2:G2', f'Period: {wizard.date_from} to {wizard.date_to}', subheader_format)

        # Write column headers
        row = 3
        if report_type == 'summary':
            headers = ['Partner', 'Total Retention', 'Released Amount', 'Remaining Amount', 'Status']
            sheet.write(row, 0, headers[0], subheader_format)
            sheet.write(row, 1, headers[1], subheader_format)
            sheet.write(row, 2, headers[2], subheader_format)
            sheet.write(row, 3, headers[3], subheader_format)
            sheet.write(row, 4, headers[4], subheader_format)
            
            # Group by partner
            partner_data = {}
            for retention in retentions:
                partner_id = retention.partner_id.id
                if partner_id not in partner_data:
                    partner_data[partner_id] = {
                        'name': retention.partner_id.name,
                        'retention_amount': 0.0,
                        'released_amount': 0.0,
                        'remaining_amount': 0.0,
                        'states': set(),
                    }
                
                partner_data[partner_id]['retention_amount'] += retention.retention_amount
                partner_data[partner_id]['released_amount'] += retention.released_amount
                partner_data[partner_id]['remaining_amount'] += retention.remaining_amount
                partner_data[partner_id]['states'].add(retention.state)
            
            # Write partner summary data
            row = 4
            for partner_id, data in partner_data.items():
                sheet.write(row, 0, data['name'], cell_format)
                sheet.write(row, 1, data['retention_amount'], amount_format)
                sheet.write(row, 2, data['released_amount'], amount_format)
                sheet.write(row, 3, data['remaining_amount'], amount_format)
                sheet.write(row, 4, ', '.join(data['states']), cell_format)
                row += 1
                
            # Write totals
            total_retention = sum(retentions.mapped('retention_amount'))
            total_released = sum(retentions.mapped('released_amount'))
            total_remaining = sum(retentions.mapped('remaining_amount'))
            
            row += 1
            sheet.write(row, 0, 'TOTAL', subheader_format)
            sheet.write(row, 1, total_retention, amount_format)
            sheet.write(row, 2, total_released, amount_format)
            sheet.write(row, 3, total_remaining, amount_format)
            sheet.write(row, 4, '', cell_format)
            
        else:  # Detailed report
            headers = ['Reference', 'Partner', 'Date', 'Retention Amount', 'Released Amount', 'Remaining Amount', 'Status']
            sheet.write(row, 0, headers[0], subheader_format)
            sheet.write(row, 1, headers[1], subheader_format)
            sheet.write(row, 2, headers[2], subheader_format)
            sheet.write(row, 3, headers[3], subheader_format)
            sheet.write(row, 4, headers[4], subheader_format)
            sheet.write(row, 5, headers[5], subheader_format)
            sheet.write(row, 6, headers[6], subheader_format)
            
            row = 4
            for retention in retentions:
                sheet.write(row, 0, retention.name, cell_format)
                sheet.write(row, 1, retention.partner_id.name, cell_format)
                sheet.write(row, 2, retention.date, date_format)
                sheet.write(row, 3, retention.retention_amount, amount_format)
                sheet.write(row, 4, retention.released_amount, amount_format)
                sheet.write(row, 5, retention.remaining_amount, amount_format)
                sheet.write(row, 6, dict(retention._fields['state'].selection).get(retention.state), cell_format)
                row += 1
                
            # Write totals
            total_retention = sum(retentions.mapped('retention_amount'))
            total_released = sum(retentions.mapped('released_amount'))
            total_remaining = sum(retentions.mapped('remaining_amount'))
            
            row += 1
            sheet.write(row, 0, 'TOTAL', subheader_format)
            sheet.write(row, 1, '', cell_format)
            sheet.write(row, 2, '', cell_format)
            sheet.write(row, 3, total_retention, amount_format)
            sheet.write(row, 4, total_released, amount_format)
            sheet.write(row, 5, total_remaining, amount_format)
            sheet.write(row, 6, '', cell_format)