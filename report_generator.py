import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf_report(data):
    """
    Generates a clean clinical summary PDF report for the user assessment.
    data dict contains:
      name, age, gender, bmi, bmi_category, score, risk_level,
      factors, top_factors (list of dicts with name & explanation),
      tips, timestamp, assessment_type
    Returns bytes of PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0d6efd'),
        spaceAfter=4,
        alignment=1 # Center
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#6c757d'),
        alignment=1,
        spaceAfter=15
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#212529'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#333333')
    )
    bold_style = ParagraphStyle(
        'BoldDark',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#842029'),
        alignment=1
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("DiaGuard.ai - Diabetes Risk Assessment Report", title_style))
    story.append(Paragraph(f"Generated on {data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M'))} &bull; Mode: {data.get('assessment_type', 'Screening')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0d6efd'), spaceAfter=12))

    # Patient & Assessment Overview Table
    risk_level = data.get('risk_level', 'Low')
    risk_color_hex = "#198754" if risk_level == "Low" else ("#ffc107" if risk_level == "Medium" else "#dc3545")
    
    overview_data = [
        [
            Paragraph("<b>Patient Name:</b>", body_style),
            Paragraph(str(data.get('name', 'Guest')), body_style),
            Paragraph("<b>Assessment Date:</b>", body_style),
            Paragraph(str(data.get('timestamp', datetime.now().strftime('%Y-%m-%d'))), body_style)
        ],
        [
            Paragraph("<b>Age / Gender:</b>", body_style),
            Paragraph(f"{data.get('age', '--')} yrs / {data.get('gender', '--')}", body_style),
            Paragraph("<b>Body Mass Index (BMI):</b>", body_style),
            Paragraph(f"{data.get('bmi', '--')} ({data.get('bmi_category', 'Normal')})", body_style)
        ],
        [
            Paragraph("<b>Assessed Risk Level:</b>", body_style),
            Paragraph(f"<font color='{risk_color_hex}'><b>{risk_level} Risk</b></font>", bold_style),
            Paragraph("<b>Calculated Probability:</b>", body_style),
            Paragraph(f"<b>{data.get('score', 0)}%</b>", bold_style)
        ]
    ]

    t_overview = Table(overview_data, colWidths=[1.5*inch, 2.0*inch, 1.8*inch, 2.2*inch])
    t_overview.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#dee2e6')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e9ecef')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_overview)
    story.append(Spacer(1, 14))

    # Top Contributing Risk Factors Section
    story.append(Paragraph("Key Contributing Risk Factors (Top Drivers)", heading_style))
    top_factors = data.get('top_factors', [])
    if top_factors:
        factor_rows = [[Paragraph("<b>Risk Factor</b>", bold_style), Paragraph("<b>Clinical Impact / Explanation</b>", bold_style)]]
        for tf in top_factors:
            factor_rows.append([
                Paragraph(f"&bull; <b>{tf.get('name', '')}</b>", body_style),
                Paragraph(tf.get('explanation', ''), body_style)
            ])
        t_factors = Table(factor_rows, colWidths=[2.5*inch, 5.0*inch])
        t_factors.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e7f1ff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#b6d4fe')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d0e2ff')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_factors)
    else:
        story.append(Paragraph("No major elevated risk indicators reported. Metabolic markers are in healthy ranges.", body_style))
    story.append(Spacer(1, 14))

    # Recommended Action Items & Tips
    story.append(Paragraph("Personalized Action Plan & Clinical Recommendations", heading_style))
    tips = data.get('tips', [])
    if tips:
        for i, tip in enumerate(tips, 1):
            story.append(Paragraph(f"<b>{i}.</b> {tip}", body_style))
            story.append(Spacer(1, 4))
    story.append(Spacer(1, 14))

    # Clinical Medical Disclaimer Box
    disclaimer_text = (
        "<b>CLINICAL DISCLAIMER:</b> This report is generated by a computer-based early risk screening system "
        "and is strictly for educational guidance and awareness. This is NOT a medical diagnosis. "
        "Please consult a certified medical practitioner or diabetologist for official diagnostic tests (e.g. HbA1c, Fasting Plasma Glucose)."
    )
    t_disc = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[7.5*inch])
    t_disc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8d7da')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#f5c2c7')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(Spacer(1, 10))
    story.append(t_disc)

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
