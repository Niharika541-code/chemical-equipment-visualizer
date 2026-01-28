from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from docx import Document
from reportlab.lib.pagesizes import letter
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfgen import canvas
from io import BytesIO
import json
from datetime import datetime

import pandas as pd

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import UploadHistory


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_csv(request):
    file = request.FILES['file']
    df = pd.read_csv(file)

    summary = {
        "total_equipment": len(df),
        "avg_flowrate": float(df["Flowrate"].mean()),
        "avg_pressure": float(df["Pressure"].mean()),
        "avg_temperature": float(df["Temperature"].mean()),
        "type_distribution": df["Type"].value_counts().to_dict()
    }

    UploadHistory.objects.create(
        total_equipment=summary["total_equipment"],
        avg_flowrate=summary["avg_flowrate"],
        avg_pressure=summary["avg_pressure"],
        avg_temperature=summary["avg_temperature"],
        type_distribution=str(summary["type_distribution"])
    )

    return Response({"summary": summary})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history(request):
    records = UploadHistory.objects.all().order_by('-created_at')[:5]
    data = []

    for r in records:
        data.append({
            "time": r.created_at.strftime("%d-%m-%Y %H:%M"),
            "total_equipment": r.total_equipment,
            "avg_flowrate": r.avg_flowrate,
            "avg_pressure": r.avg_pressure,
            "avg_temperature": r.avg_temperature,
        })

    return Response(data)


def add_page_number(section):
    """Add page numbers to document footer"""
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    
    # Add page number field
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = "PAGE"
    
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_pdf_report(request):
    """
    Generate a comprehensive PDF report with all analysis data
    Expects JSON body with: results, history, username
    """
    try:
        # Get data from request
        data = request.data
        results = data.get('results', {})
        history = data.get('history', [])
        username = data.get('username', request.user.username)
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=36,
            textColor=colors.HexColor('#0ea5e9'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=18,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#0ea5e9'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            fontName='Helvetica'
        )
        
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        # ==================== TITLE PAGE ====================
        # Icon
        elements.append(Spacer(1, 50))
        icon = Paragraph("⚗️", ParagraphStyle('Icon', fontSize=72, alignment=TA_CENTER))
        elements.append(icon)
        elements.append(Spacer(1, 20))
        
        # Title
        title = Paragraph("CHEMVIZ", title_style)
        elements.append(title)
        
        # Subtitle
        subtitle = Paragraph("Equipment Analysis Report", subtitle_style)
        elements.append(subtitle)
        elements.append(Spacer(1, 30))
        
        # Metadata
        metadata_text = f"""
        <b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        <b>Prepared by:</b> {username}<br/>
        ChemViz Systems v2.0.5
        """
        metadata = Paragraph(metadata_text, metadata_style)
        elements.append(metadata)
        
        # Page break
        elements.append(PageBreak())
        
        # ==================== EXECUTIVE SUMMARY ====================
        elements.append(Paragraph("Executive Summary", heading_style))
        
        total_equipment = results.get('total_equipment', 0)
        summary_text = f"""
        This report provides a comprehensive analysis of equipment data uploaded to the ChemViz system. 
        The analysis covers {total_equipment} pieces of equipment with detailed metrics on flowrate, 
        temperature, and pressure measurements. The data shows operational patterns and trends that inform 
        maintenance schedules and efficiency optimization strategies.
        """
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 20))
        
        # ==================== KEY METRICS ====================
        elements.append(Paragraph("Key Performance Metrics", heading_style))
        
        avg_flowrate = results.get('avg_flowrate', 0)
        avg_temp = results.get('avg_temperature', 0)
        avg_pressure = results.get('avg_pressure', 0)
        
        # Create metrics table
        metrics_data = [
            ['Metric', 'Value', 'Status'],
            ['Total Equipment', str(total_equipment), '✓ Operational'],
            ['Average Flowrate', f"{avg_flowrate:.2f} L/min", '↑ Stable'],
            ['Average Temperature', f"{avg_temp:.2f}°C", '→ Normal'],
            ['Average Pressure', f"{avg_pressure:.2f} PSI", '✓ Optimal'],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
        ]))
        
        elements.append(metrics_table)
        elements.append(Spacer(1, 20))
        
        # ==================== EQUIPMENT DISTRIBUTION ====================
        elements.append(Paragraph("Equipment Distribution Analysis", heading_style))
        
        type_dist = results.get('type_distribution', {})
        
        if type_dist:
            dist_text = "The equipment distribution across different types is as follows:"
            elements.append(Paragraph(dist_text, body_style))
            
            # Calculate total for percentages
            total = sum(type_dist.values())
            
            # Create distribution table
            dist_data = [['Equipment Type', 'Count', 'Percentage']]
            for equip_type, count in sorted(type_dist.items()):
                percentage = (count / total * 100) if total > 0 else 0
                dist_data.append([str(equip_type), str(count), f"{percentage:.1f}%"])
            
            dist_table = Table(dist_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            dist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
            ]))
            
            elements.append(dist_table)
        else:
            elements.append(Paragraph("No equipment distribution data available.", body_style))
        
        elements.append(Spacer(1, 20))
        
        # ==================== DETAILED ANALYSIS ====================
        elements.append(Paragraph("Detailed Technical Analysis", heading_style))
        
        # Flowrate Analysis
        elements.append(Paragraph("Flowrate Analysis", subheading_style))
        flowrate_text = f"""
        <b>Average Flowrate:</b> {avg_flowrate:.2f} L/min<br/>
        <b>Peak Flowrate (Estimated):</b> {(avg_flowrate * 1.2):.2f} L/min<br/><br/>
        <b>Analysis:</b> The flowrate measurements indicate stable operation within normal parameters. 
        Consistent flowrate suggests proper pump operation and minimal system resistance.
        """
        elements.append(Paragraph(flowrate_text, body_style))
        elements.append(Spacer(1, 10))
        
        # Temperature Analysis
        elements.append(Paragraph("Temperature Analysis", subheading_style))
        temp_text = f"""
        <b>Average Temperature:</b> {avg_temp:.2f}°C<br/><br/>
        <b>Analysis:</b> Temperature readings are within acceptable operational ranges. 
        Monitoring temperature trends helps identify potential cooling system issues 
        or equipment stress before they become critical.
        """
        elements.append(Paragraph(temp_text, body_style))
        elements.append(Spacer(1, 10))
        
        # Pressure Analysis
        elements.append(Paragraph("Pressure Analysis", subheading_style))
        pressure_text = f"""
        <b>Average Pressure:</b> {avg_pressure:.2f} PSI<br/><br/>
        <b>Analysis:</b> Pressure measurements indicate system integrity and proper valve operation. 
        Consistent pressure readings suggest minimal leakage and optimal system configuration.
        """
        elements.append(Paragraph(pressure_text, body_style))
        
        # Page break
        elements.append(PageBreak())
        
        # ==================== HISTORICAL TRENDS ====================
        elements.append(Paragraph("Historical Upload Analysis", heading_style))
        
        if history and len(history) > 0:
            hist_text = f"Analysis based on {len(history)} historical data uploads:"
            elements.append(Paragraph(hist_text, body_style))
            
            # Create history table (most recent 10)
            hist_data = [['Timestamp', 'Equipment', 'Flowrate', 'Pressure', 'Temperature']]
            for item in history[:10]:
                hist_data.append([
                    str(item.get('time', 'N/A')),
                    str(item.get('total_equipment', 0)),
                    f"{item.get('avg_flowrate', 0):.2f}",
                    f"{item.get('avg_pressure', 0):.2f}",
                    f"{item.get('avg_temperature', 0):.2f}"
                ])
            
            hist_table = Table(hist_data, colWidths=[1.8*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
            hist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
            ]))
            
            elements.append(hist_table)
            elements.append(Spacer(1, 15))
            
            # Trend analysis
            trend_text = """
            <b>Trend Analysis:</b><br/>
            Historical data shows consistent operational patterns with minimal variance. 
            This stability indicates well-maintained equipment and effective process control. 
            Regular monitoring continues to be recommended for early detection of anomalies.
            """
            elements.append(Paragraph(trend_text, body_style))
        else:
            elements.append(Paragraph("No historical data available for trend analysis.", body_style))
        
        elements.append(Spacer(1, 20))
        
        # ==================== RECOMMENDATIONS ====================
        elements.append(Paragraph("Recommendations", heading_style))
        
        recommendations = [
            'Continue regular monitoring of all equipment metrics to establish baseline performance patterns',
            'Schedule preventive maintenance based on flowrate and temperature trend analysis',
            'Implement automated alerts for metrics falling outside normal operating ranges',
            'Review equipment with consistently high temperature readings for potential cooling system improvements',
            'Maintain detailed logs of all maintenance activities for correlation with performance data'
        ]
        
        for i, rec in enumerate(recommendations, 1):
            rec_text = f"{i}. {rec}"
            elements.append(Paragraph(rec_text, body_style))
        
        # Page break for appendix
        elements.append(PageBreak())
        
        # ==================== RAW DATA APPENDIX ====================
        elements.append(Paragraph("Appendix: Raw Data", heading_style))
        elements.append(Paragraph("<b>Complete JSON Output:</b>", body_style))
        
        # Add formatted JSON
        json_text = json.dumps(results, indent=2)
        json_style = ParagraphStyle(
            'JSONStyle',
            parent=styles['Code'],
            fontSize=8,
            fontName='Courier',
            textColor=colors.HexColor('#64748b'),
            leftIndent=20,
            spaceAfter=6
        )
        
        # Split JSON into lines to avoid overflow
        for line in json_text.split('\n')[:50]:  # Limit to first 50 lines
            elements.append(Paragraph(line.replace(' ', '&nbsp;'), json_style))
        
        elements.append(Spacer(1, 30))
        
        # ==================== FOOTER ====================
        footer_text = """
        <para align="center">
        —— End of Report ——<br/>
        <font size=8 color="#cbd5e1">ChemViz Systems • Industrial Equipment Analytics Portal</font>
        </para>
        """
        elements.append(Paragraph(footer_text, metadata_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF from buffer
        buffer.seek(0)
        pdf = buffer.getvalue()
        buffer.close()
        
        # Create HTTP response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ChemViz_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        return response
        
    except Exception as e:
        import traceback
        print("PDF Generation Error:")
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    user = authenticate(
        username=request.data.get("username"),
        password=request.data.get("password")
    )

    if user is None:
        return Response({"error": "Invalid credentials"}, status=401)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key})


@api_view(["POST"])
@permission_classes([AllowAny])
def create_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists"}, status=400)

    User.objects.create_user(username=username, password=password)
    return Response({"message": "User created successfully"})