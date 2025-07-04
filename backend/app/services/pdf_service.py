import io
import os
from datetime import datetime
from typing import Dict, List, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import logging

logger = logging.getLogger(__name__)


class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=12
        ))
        
        # Company info style
        self.styles.add(ParagraphStyle(
            name='CompanyInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#333333')
        ))
        
        # Terms style
        self.styles.add(ParagraphStyle(
            name='Terms',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            spaceAfter=6
        ))
    
    def generate_quotation_pdf(self, quotation_data: Dict[str, Any]) -> bytes:
        """Generate a quotation PDF and return as bytes"""
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30*mm,
            leftMargin=30*mm,
            topMargin=30*mm,
            bottomMargin=30*mm
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add company header
        elements.extend(self._create_header())
        
        # Add quotation title
        elements.append(Paragraph(f"QUOTATION", self.styles['CustomTitle']))
        elements.append(Spacer(1, 12))
        
        # Add quotation info table
        elements.append(self._create_quotation_info(quotation_data))
        elements.append(Spacer(1, 20))
        
        # Add customer info
        elements.append(self._create_customer_info(quotation_data))
        elements.append(Spacer(1, 20))
        
        # Add items table
        elements.append(self._create_items_table(quotation_data))
        elements.append(Spacer(1, 20))
        
        # Add totals
        elements.append(self._create_totals_table(quotation_data))
        elements.append(Spacer(1, 30))
        
        # Add terms and conditions
        elements.extend(self._create_terms_section(quotation_data))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        buffer.seek(0)
        pdf_data = buffer.read()
        buffer.close()
        
        return pdf_data
    
    def _create_header(self) -> List:
        """Create company header"""
        elements = []
        
        # Company name and info
        company_info = """
        <para align="right">
        <b>BMA Social Co., Ltd.</b><br/>
        123 Business Tower, Bangkok 10110<br/>
        Tel: +66 2 123 4567<br/>
        Email: info@bmasocial.com<br/>
        Tax ID: 0123456789012
        </para>
        """
        elements.append(Paragraph(company_info, self.styles['CompanyInfo']))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_quotation_info(self, data: Dict[str, Any]) -> Table:
        """Create quotation info table"""
        quote_date = datetime.fromisoformat(data['created_at']).strftime('%B %d, %Y')
        valid_until = datetime.fromisoformat(data['valid_until']).strftime('%B %d, %Y')
        
        info_data = [
            ['Quote Number:', data['quote_number']],
            ['Date:', quote_date],
            ['Valid Until:', valid_until],
        ]
        
        table = Table(info_data, colWidths=[100, 200])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
        ]))
        
        return table
    
    def _create_customer_info(self, data: Dict[str, Any]) -> Table:
        """Create customer info section"""
        customer_data = []
        
        # Add "To:" header
        customer_data.append(['To:', ''])
        
        # Company name
        if data.get('company_name'):
            customer_data.append(['', data['company_name']])
        
        # Customer name
        customer_data.append(['', data['customer_name']])
        
        # Address
        if data.get('company_address'):
            customer_data.append(['', data['company_address']])
        
        # Tax ID
        if data.get('company_tax_id'):
            customer_data.append(['', f"Tax ID: {data['company_tax_id']}"])
        
        table = Table(customer_data, colWidths=[50, 450])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        return table
    
    def _create_items_table(self, data: Dict[str, Any]) -> Table:
        """Create items table"""
        # Get currency symbol
        currency = data.get('currency', 'THB')
        currency_symbol = '฿' if currency == 'THB' else '$'
        
        # Table headers
        headers = ['#', 'Description', 'Qty', 'Unit Price', 'Total']
        
        # Prepare table data
        table_data = [headers]
        
        for idx, item in enumerate(data.get('items', []), 1):
            row = [
                str(idx),
                item['description'],
                str(item['quantity']),
                f"{currency_symbol}{item['unit_price']:,.2f}",
                f"{currency_symbol}{item['total']:,.2f}"
            ]
            table_data.append(row)
        
        # Create table
        table = Table(table_data, colWidths=[30, 280, 50, 70, 70])
        
        # Apply table style
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Item number
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Quantity
            ('ALIGN', (3, 1), (4, -1), 'RIGHT'),   # Prices
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1976d2')),
            
            # Row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        
        return table
    
    def _create_totals_table(self, data: Dict[str, Any]) -> Table:
        """Create totals section"""
        # Get currency symbol
        currency = data.get('currency', 'THB')
        currency_symbol = '฿' if currency == 'THB' else '$'
        
        totals_data = [
            ['Subtotal:', f"{currency_symbol}{data['subtotal']:,.2f}"],
        ]
        
        if data.get('discount_amount', 0) > 0:
            totals_data.append([f"Discount ({data['discount_percent']}%):", f"-{currency_symbol}{data['discount_amount']:,.2f}"])
        
        if data.get('tax_amount', 0) > 0:
            totals_data.append([f"VAT ({data['tax_percent']}%):", f"{currency_symbol}{data['tax_amount']:,.2f}"])
        
        totals_data.append(['Total:', f"{currency_symbol}{data['total_amount']:,.2f} {currency}"])
        
        table = Table(totals_data, colWidths=[400, 100])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1976d2')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ]))
        
        return table
    
    def _create_terms_section(self, data: Dict[str, Any]) -> List:
        """Create terms and conditions section"""
        elements = []
        
        # Payment terms
        elements.append(Paragraph("<b>Payment Terms:</b>", self.styles['Terms']))
        elements.append(Paragraph(data.get('payment_terms', '50% deposit, 50% on completion'), self.styles['Terms']))
        elements.append(Spacer(1, 10))
        
        # Notes
        if data.get('notes'):
            elements.append(Paragraph("<b>Notes:</b>", self.styles['Terms']))
            elements.append(Paragraph(data['notes'], self.styles['Terms']))
            elements.append(Spacer(1, 10))
        
        # Signature section
        elements.append(Spacer(1, 30))
        
        sig_data = [
            ['_' * 40, '', '_' * 40],
            ['Authorized Signature', '', 'Customer Signature'],
            ['Date: _______________', '', 'Date: _______________']
        ]
        
        sig_table = Table(sig_data, colWidths=[200, 100, 200])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        
        elements.append(sig_table)
        
        return elements
    
    def generate_invoice_pdf(self, invoice_data: Dict[str, Any]) -> bytes:
        """Generate an invoice PDF (similar to quotation but with different title and fields)"""
        # Similar implementation to quotation
        # Will implement when needed
        pass
    
    def generate_contract_pdf(self, contract_data: Dict[str, Any]) -> bytes:
        """Generate a contract PDF"""
        # Will implement when needed
        pass


# Singleton instance
pdf_service = PDFService()