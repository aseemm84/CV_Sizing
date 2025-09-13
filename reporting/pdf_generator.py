"""
Enhanced PDF Report Generator for Valve Sizing Application
Supports both fpdf2 and ReportLab, with comprehensive reporting capabilities
"""
from datetime import datetime
import io
import base64

def create_pdf_report(report_data):
    """
    Create comprehensive PDF report of valve sizing calculation

    Args:
        report_data: Dictionary containing inputs, results, and metadata

    Returns:
        Tuple of (filename, pdf_bytes)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"valve_sizing_report_{timestamp}.pdf"

    # Try fpdf2 first (preferred)
    try:
        pdf_bytes = create_pdf_with_fpdf2(report_data)
        return filename, pdf_bytes
    except ImportError:
        print("fpdf2 not available, trying ReportLab...")

    # Try ReportLab as second option
    try:
        pdf_bytes = create_pdf_with_reportlab(report_data)
        return filename, pdf_bytes
    except ImportError:
        print("ReportLab not available, trying weasyprint...")

    # Try weasyprint as third option
    try:
        pdf_bytes = create_pdf_with_weasyprint(report_data)
        return filename, pdf_bytes
    except ImportError:
        print("No PDF libraries available, creating enhanced text report...")

    # Enhanced text fallback
    content = create_enhanced_text_report(report_data)
    return filename.replace('.pdf', '.txt'), content.encode('utf-8')

def create_pdf_with_fpdf2(report_data):
    """Create PDF using fpdf2 library"""
    from fpdf import FPDF

    class ValveSizingPDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'CONTROL VALVE SIZING REPORT', 0, 1, 'C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    pdf = ValveSizingPDF()
    pdf.add_page()

    inputs = report_data['inputs']
    results = report_data['results']

    # Report Information
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Generated: {report_data['report_date']}", 0, 1)
    pdf.cell(0, 8, f"Software: {report_data.get('software_version', 'Enhanced Valve Sizing Application v2.0')}", 0, 1)

    # Standards compliance
    if 'standards_compliance' in report_data:
        pdf.cell(0, 8, f"Standards: {', '.join(report_data['standards_compliance'])}", 0, 1)

    pdf.ln(8)

    # Process Conditions Section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'PROCESS CONDITIONS', 0, 1)
    pdf.set_font('Arial', '', 10)

    process_info = [
        f"Fluid Type: {inputs.get('fluid_type', 'N/A')}",
        f"Fluid Name: {inputs.get('fluid_name', 'N/A')}",
        f"Fluid Nature: {inputs.get('fluid_nature', 'N/A')}",
        f"Flow Rate: {inputs.get('flow_rate', 'N/A')} {get_flow_unit(inputs)}",
        f"Inlet Pressure (P1): {inputs.get('p1', 'N/A')} {get_pressure_unit(inputs)}",
        f"Outlet Pressure (P2): {inputs.get('p2', 'N/A')} {get_pressure_unit(inputs)}",
        f"Differential Pressure: {inputs.get('dp', 'N/A')} {get_pressure_unit(inputs)}",
        f"Temperature (T1): {inputs.get('t1', 'N/A')} {get_temp_unit(inputs)}",
    ]

    # Add fluid-specific properties
    if inputs.get('fluid_type') == 'Liquid':
        process_info.extend([
            f"Density/SG: {inputs.get('rho', 'N/A')} {get_density_unit(inputs)}",
            f"Vapor Pressure: {inputs.get('pv', 'N/A')} {get_pressure_unit(inputs)}",
            f"Critical Pressure: {inputs.get('pc', 'N/A')} {get_pressure_unit(inputs)}",
            f"Viscosity: {inputs.get('vc', 'N/A')} cP"
        ])
    else:
        process_info.extend([
            f"Molecular Weight: {inputs.get('mw', 'N/A')}",
            f"Specific Heat Ratio (k): {inputs.get('k', 'N/A')}",
            f"Compressibility Factor (Z): {inputs.get('z', 'N/A')}"
        ])

    for item in process_info:
        pdf.cell(0, 6, item, 0, 1)

    pdf.ln(8)

    # Valve Selection Section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'VALVE SELECTION', 0, 1)
    pdf.set_font('Arial', '', 10)

    valve_info = [
        f"Valve Type: {inputs.get('valve_type', 'N/A')}",
        f"Valve Style: {inputs.get('valve_style', 'N/A')}",
        f"Valve Size: {inputs.get('valve_size_nominal', 'N/A')} inches",
        f"Valve Characteristic: {inputs.get('valve_char', 'N/A')}",
        f"Expected Opening: {inputs.get('valve_opening_percent', 70)}%",
        f"Actuator Type: {format_actuator_type(inputs.get('actuator_type', 'N/A'))}",
        f"Fail-Safe Position: {inputs.get('fail_position', 'N/A')}"
    ]

    for item in valve_info:
        pdf.cell(0, 6, item, 0, 1)

    pdf.ln(8)

    # Sizing Results Section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'SIZING RESULTS', 0, 1)
    pdf.set_font('Arial', '', 10)

    # Main results
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, f"Required Flow Coefficient (Cv): {results.get('cv', 0):.2f}", 0, 1)
    pdf.set_font('Arial', '', 10)

    # Enhanced results if available
    sizing_results = []

    if 'reynolds_factor' in results:
        sizing_results.append(f"Reynolds Correction Factor (FR): {results['reynolds_factor']:.3f}")

    if 'ff_factor' in results:
        sizing_results.append(f"Liquid Critical Pressure Ratio Factor (FF): {results['ff_factor']:.3f}")

    sizing_results.extend([
        f"Rated Cv for Selected Valve: {results.get('rated_cv', 'N/A')}",
        f"Valve Opening at Design Flow: {(results.get('cv', 0)/results.get('rated_cv', 1)*100):.1f}%",
        f"Inherent Rangeability: {results.get('inherent_rangeability', 'N/A')}:1"
    ])

    for item in sizing_results:
        pdf.cell(0, 6, item, 0, 1)

    pdf.ln(5)

    # Cavitation Analysis
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'CAVITATION ANALYSIS', 0, 1)
    pdf.set_font('Arial', '', 10)

    if 'sigma_analysis' in results:
        sigma_data = results['sigma_analysis']
        cavitation_info = [
            f"Sigma Value: {sigma_data.get('sigma', 'N/A'):.2f}",
            f"Cavitation Level: {sigma_data.get('level', 'N/A')}",
            f"Risk Assessment: {sigma_data.get('risk', 'N/A')}",
            f"Status: {sigma_data.get('status', 'N/A')}",
            f"Recommendation: {sigma_data.get('recommendation', 'N/A')}"
        ]
    else:
        cavitation_info = [
            f"Cavitation Index: {results.get('cavitation_index', 'N/A'):.2f}",
            f"Status: {results.get('cavitation_status', 'N/A')}",
            f"Flashing: {'Yes' if results.get('is_flashing', False) else 'No'}"
        ]

    for item in cavitation_info:
        pdf.cell(0, 6, item, 0, 1)

    pdf.ln(5)

    # Noise Analysis
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'NOISE ANALYSIS', 0, 1)
    pdf.set_font('Arial', '', 10)

    noise_info = [
        f"Predicted Noise Level: {results.get('total_noise_dba', 'N/A'):.1f} dBA at 1m",
        f"Prediction Method: {results.get('method', 'Standard Calculation')}",
        f"Recommendation: {results.get('noise_recommendation', 'Standard trim acceptable')}"
    ]

    for item in noise_info:
        pdf.cell(0, 6, item, 0, 1)

    pdf.ln(5)

    # Actuator Requirements
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'ACTUATOR REQUIREMENTS', 0, 1)
    pdf.set_font('Arial', '', 10)

    if inputs.get('valve_type') == 'Globe':
        pdf.cell(0, 6, f"Required Thrust: {results.get('required_force', 0):.0f} {get_force_unit(inputs)}", 0, 1)
    else:
        pdf.cell(0, 6, f"Required Torque: {results.get('required_torque', 0):.0f} {get_torque_unit(inputs)}", 0, 1)

    pdf.cell(0, 6, f"Safety Factor Applied: {results.get('safety_factor_used', 1.5):.1f}", 0, 1)
    pdf.cell(0, 6, f"Recommendation: {results.get('actuator_recommendation', 'Consult manufacturer')}", 0, 1)

    pdf.ln(5)

    # Material Recommendations
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'MATERIAL RECOMMENDATIONS', 0, 1)
    pdf.set_font('Arial', '', 10)

    if 'recommendations' in results:
        materials = results['recommendations']
        material_info = [
            f"Body Material: {materials.get('Body Material', 'N/A')}",
            f"Trim Material: {materials.get('Trim Material', 'N/A')}",
            f"Bolting: {materials.get('Bolting', 'N/A')}",
            f"Gasket: {materials.get('Gasket', 'N/A')}"
        ]

        for item in material_info:
            pdf.cell(0, 6, item, 0, 1)

    if 'service_category' in results:
        pdf.cell(0, 6, f"Service Category: {results['service_category']}", 0, 1)

    if 'compliance_check' in results:
        pdf.ln(3)
        pdf.set_font('Arial', 'I', 9)
        pdf.multi_cell(0, 5, f"Compliance: {results['compliance_check']}")

    # Add new page for detailed analysis if requested
    if report_data.get('include_detailed_analysis', False):
        pdf.add_page()
        add_detailed_analysis_section(pdf, inputs, results)

    # Footer information
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 8)
    pdf.multi_cell(0, 4, "DISCLAIMER: This report is generated for preliminary valve sizing purposes. Final valve selection should be verified with manufacturer-specific software and confirmed against actual service conditions. All calculations follow industry standards but require engineering judgment for final application.")

    return bytes(pdf.output(dest='S'), 'latin1')

def create_pdf_with_reportlab(report_data):
    """Create PDF using ReportLab library"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph("CONTROL VALVE SIZING REPORT", title_style))

    # Report info
    info_data = [
        [f"Generated: {report_data['report_date']}"],
        [f"Software: {report_data.get('software_version', 'Enhanced Valve Sizing v2.0')}"]
    ]

    story.append(Table(info_data, colWidths=[6*inch]))
    story.append(Spacer(1, 20))

    # Process Conditions
    story.append(Paragraph("PROCESS CONDITIONS", styles['Heading2']))

    inputs = report_data['inputs']
    results = report_data['results']

    process_data = [
        ['Parameter', 'Value', 'Units'],
        ['Fluid Type', inputs.get('fluid_type', 'N/A'), ''],
        ['Fluid Name', inputs.get('fluid_name', 'N/A'), ''],
        ['Flow Rate', f"{inputs.get('flow_rate', 'N/A')}", get_flow_unit(inputs)],
        ['Inlet Pressure', f"{inputs.get('p1', 'N/A')}", get_pressure_unit(inputs)],
        ['Outlet Pressure', f"{inputs.get('p2', 'N/A')}", get_pressure_unit(inputs)],
        ['Temperature', f"{inputs.get('t1', 'N/A')}", get_temp_unit(inputs)],
    ]

    process_table = Table(process_data, colWidths=[2*inch, 2*inch, 1*inch])
    process_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(process_table)
    story.append(Spacer(1, 20))

    # Sizing Results
    story.append(Paragraph("SIZING RESULTS", styles['Heading2']))
    story.append(Paragraph(f"<b>Required Cv: {results.get('cv', 0):.2f}</b>", styles['Normal']))
    story.append(Spacer(1, 10))

    # Build and return PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def create_pdf_with_weasyprint(report_data):
    """Create PDF using WeasyPrint (HTML to PDF)"""
    import weasyprint

    html_content = create_html_report(report_data)
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    return pdf_bytes

def create_html_report(report_data):
    """Create HTML report for WeasyPrint conversion"""
    inputs = report_data['inputs']
    results = report_data['results']

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Valve Sizing Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .section {{ margin-bottom: 25px; }}
            .section h2 {{ color: #333; border-bottom: 2px solid #333; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .highlight {{ background-color: #ffffcc; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>CONTROL VALVE SIZING REPORT</h1>
            <p>Generated: {report_data['report_date']}</p>
            <p>Software: {report_data.get('software_version', 'Enhanced Valve Sizing v2.0')}</p>
        </div>

        <div class="section">
            <h2>Process Conditions</h2>
            <table>
                <tr><th>Parameter</th><th>Value</th><th>Units</th></tr>
                <tr><td>Fluid Type</td><td>{inputs.get('fluid_type', 'N/A')}</td><td></td></tr>
                <tr><td>Flow Rate</td><td>{inputs.get('flow_rate', 'N/A')}</td><td>{get_flow_unit(inputs)}</td></tr>
                <tr><td>Inlet Pressure</td><td>{inputs.get('p1', 'N/A')}</td><td>{get_pressure_unit(inputs)}</td></tr>
                <tr><td>Outlet Pressure</td><td>{inputs.get('p2', 'N/A')}</td><td>{get_pressure_unit(inputs)}</td></tr>
                <tr><td>Temperature</td><td>{inputs.get('t1', 'N/A')}</td><td>{get_temp_unit(inputs)}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>Sizing Results</h2>
            <p class="highlight">Required Cv: {results.get('cv', 0):.2f}</p>
            <table>
                <tr><td>Valve Type</td><td>{inputs.get('valve_type', 'N/A')}</td></tr>
                <tr><td>Valve Size</td><td>{inputs.get('valve_size_nominal', 'N/A')} inches</td></tr>
                <tr><td>Cavitation Status</td><td>{results.get('cavitation_status', 'N/A')}</td></tr>
                <tr><td>Noise Level</td><td>{results.get('total_noise_dba', 'N/A'):.1f} dBA</td></tr>
            </table>
        </div>
    </body>
    </html>
    """
    return html

def create_enhanced_text_report(report_data):
    """Create comprehensive text report as fallback"""
    inputs = report_data['inputs']
    results = report_data['results']

    report = f"""
===============================
CONTROL VALVE SIZING REPORT
===============================
Generated: {report_data['report_date']}
Software: {report_data.get('software_version', 'Enhanced Valve Sizing Application v2.0')}
Standards: {', '.join(report_data.get('standards_compliance', ['ISA S75.01', 'IEC 60534']))}

PROCESS CONDITIONS:
==================
Fluid Type:           {inputs.get('fluid_type', 'N/A')}
Fluid Name:           {inputs.get('fluid_name', 'N/A')}
Fluid Nature:         {inputs.get('fluid_nature', 'N/A')}
Service Criticality:  {inputs.get('service_criticality', 'N/A')}

Flow Conditions:
Flow Rate:            {inputs.get('flow_rate', 'N/A')} {get_flow_unit(inputs)}
Inlet Pressure (P1):  {inputs.get('p1', 'N/A')} {get_pressure_unit(inputs)}
Outlet Pressure (P2): {inputs.get('p2', 'N/A')} {get_pressure_unit(inputs)}
Differential Pressure: {inputs.get('dp', 'N/A')} {get_pressure_unit(inputs)}
Temperature (T1):     {inputs.get('t1', 'N/A')} {get_temp_unit(inputs)}
"""

    # Add fluid-specific properties
    if inputs.get('fluid_type') == 'Liquid':
        report += f"""
Liquid Properties:
Density/Specific Gravity: {inputs.get('rho', 'N/A')} {get_density_unit(inputs)}
Vapor Pressure (Pv):      {inputs.get('pv', 'N/A')} {get_pressure_unit(inputs)}
Critical Pressure (Pc):   {inputs.get('pc', 'N/A')} {get_pressure_unit(inputs)}
Viscosity:                {inputs.get('vc', 'N/A')} cP
"""
    else:
        report += f"""
Gas Properties:
Molecular Weight (MW):     {inputs.get('mw', 'N/A')}
Specific Heat Ratio (k):   {inputs.get('k', 'N/A')}
Compressibility Factor (Z): {inputs.get('z', 'N/A')}
Gas Viscosity:            {inputs.get('gas_viscosity', 'N/A')} cP
"""

    report += f"""
VALVE SELECTION:
================
Valve Type:           {inputs.get('valve_type', 'N/A')}
Valve Style:          {inputs.get('valve_style', 'N/A')}
Nominal Size:         {inputs.get('valve_size_nominal', 'N/A')} inches
Valve Characteristic: {inputs.get('valve_char', 'N/A')}
Expected Opening:     {inputs.get('valve_opening_percent', 70)}%

Actuator Configuration:
Actuator Type:        {format_actuator_type(inputs.get('actuator_type', 'N/A'))}
Fail-Safe Position:   {inputs.get('fail_position', 'N/A')}

Vendor Information:
Manufacturer:         {inputs.get('vendor', 'Generic')}
Series/Model:         {inputs.get('series', 'Standard')}

SIZING RESULTS:
===============
PRIMARY RESULTS:
Required Flow Coefficient (Cv): {results.get('cv', 0):.2f}
"""

    # Enhanced calculations if available
    if 'cv_basic' in results:
        report += f"Basic Cv (before corrections):  {results['cv_basic']:.2f}"

    if 'reynolds_factor' in results:
        report += f"Reynolds Correction Factor (FR): {results['reynolds_factor']:.3f}"

    if 'ff_factor' in results:
        report += f"FF Factor (Liquid Critical Ratio): {results['ff_factor']:.3f}"

    # Valve performance
    report += f"""
VALVE PERFORMANCE:
Rated Cv (Selected Valve):    {results.get('rated_cv', 'N/A')}
Valve Opening at Design Flow: {(results.get('cv', 0)/results.get('rated_cv', 1)*100) if results.get('rated_cv', 0) > 0 else 'N/A'}%
Inherent Rangeability:        {results.get('inherent_rangeability', 'N/A')}:1
Minimum Controllable Cv:      {results.get('min_controllable_cv', 'N/A')}
"""

    # Rangeability validation
    if 'rangeability_validation' in results:
        validation = results['rangeability_validation']
        report += f"""
FLOW SCENARIO VALIDATION:
Overall Status:          {'✓ ACCEPTABLE' if validation.get('overall_valid', False) else '⚠ REQUIRES REVIEW'}
Summary:                 {validation.get('summary', 'N/A')}

Individual Scenarios:
"""
        for scenario, result in validation.items():
            if scenario not in ['overall_valid', 'summary']:
                report += f"  {scenario.title()}: {result.get('opening_percent', 0):.1f}% - {result.get('status', 'N/A')}"

    # Cavitation analysis
    report += f"""
CAVITATION ANALYSIS:
====================
"""
    if 'sigma_analysis' in results:
        sigma_data = results['sigma_analysis']
        report += f"""Enhanced ISA RP75.23 Analysis:
Sigma Value:               {sigma_data.get('sigma', 'N/A'):.2f}
Cavitation Level:          {sigma_data.get('level', 'N/A')}
Risk Assessment:           {sigma_data.get('risk', 'N/A')}
Status:                    {sigma_data.get('status', 'N/A')}
Damage Potential:          {sigma_data.get('damage_potential', 'N/A')}
Margin to Damage:          {sigma_data.get('margin_to_damage', 'N/A')}

Trim Recommendation:       {sigma_data.get('recommendation', 'N/A')}
"""
    else:
        report += f"""Basic Analysis:
Cavitation Index (Sigma):  {results.get('cavitation_index', 'N/A'):.2f}
Cavitation Status:         {results.get('cavitation_status', 'N/A')}
Flashing Occurrence:       {'Yes' if results.get('is_flashing', False) else 'No'}
Trim Recommendation:       {results.get('trim_recommendation', 'N/A')}
"""

    # Gas-specific analysis
    if inputs.get('fluid_type') == 'Gas/Vapor' and 'flow_regime' in results:
        report += f"""
GAS FLOW ANALYSIS:
==================
Flow Regime:              {results.get('flow_regime', 'N/A')}
Expansion Factor (Y):     {results.get('expansion_factor_y', 'N/A'):.3f}
Pressure Drop Ratio (x):  {results.get('pressure_drop_ratio_x', 'N/A'):.3f}
Critical Pressure Ratio:  {results.get('choked_pressure_drop_ratio', 'N/A'):.3f}
Choked Flow:              {'Yes' if results.get('is_choked', False) else 'No'}

Performance Metrics:
Mach Number:              {results.get('mach_number', 'N/A'):.3f}
Gas Velocity:             {results.get('gas_velocity', 'N/A'):.1f} ft/s
Gas Density:              {results.get('gas_density', 'N/A'):.3f} lb/ft³
Reynolds Number:          {results.get('reynolds_number', 'N/A'):.0f}
"""
        if results.get('choking_warning'):
            report += f"⚠ WARNING: {results['choking_warning']}"
        if results.get('velocity_warning'):
            report += f"⚠ WARNING: {results['velocity_warning']}"

    # Noise analysis
    report += f"""
NOISE ANALYSIS:
===============
Predicted Noise Level:    {results.get('total_noise_dba', 'N/A'):.1f} dBA (at 1m distance)
Prediction Method:         {results.get('method', 'Standard Calculation')}
Noise Recommendation:      {results.get('noise_recommendation', 'Standard trim acceptable')}
"""

    # IEC 60534-8-3 details if available
    if 'mechanical_stream_power' in results:
        report += f"""
IEC 60534-8-3 Details:
Mechanical Stream Power:   {results.get('mechanical_stream_power', 'N/A'):.1f} W
Acoustic Efficiency:       {results.get('acoustic_efficiency', 'N/A'):.6f}
Sound Power Level:         {results.get('sound_power_level', 'N/A'):.1f} dB
Peak Frequency:           {results.get('peak_frequency', 'N/A'):.0f} Hz
Transmission Loss:         {results.get('transmission_loss', 'N/A'):.1f} dB
"""

    # Actuator requirements
    report += f"""
ACTUATOR REQUIREMENTS:
======================
"""
    if inputs.get('valve_type') == 'Globe':
        report += f"Required Thrust:           {results.get('required_force', 0):.0f} {get_force_unit(inputs)}"
    else:
        report += f"Required Torque:           {results.get('required_torque', 0):.0f} {get_torque_unit(inputs)}"

    report += f"""Safety Factor Applied:     {results.get('safety_factor_used', 1.5):.1f}
Actuator Recommendation:   {results.get('actuator_recommendation', 'Consult manufacturer for specific recommendations')}
"""

    # Detailed force/torque breakdown if available
    if 'force_breakdown' in results:
        breakdown = results['force_breakdown']
        report += f"""
Force Analysis Breakdown:
Seat Area:                 {breakdown.get('seat_area', 'N/A'):.2f} in²
Unbalanced Force:          {breakdown.get('unbalanced_force', 'N/A'):.0f} lbf
Stem Force:                {breakdown.get('stem_force', 'N/A'):.0f} lbf
Packing Friction:          {breakdown.get('packing_friction', 'N/A'):.0f} lbf
Seat Load:                 {breakdown.get('seat_load', 'N/A'):.0f} lbf
Operating Force:           {breakdown.get('operating_force', 'N/A'):.0f} lbf
Shutoff Force:             {breakdown.get('shutoff_force', 'N/A'):.0f} lbf
"""

    if 'torque_breakdown' in results:
        breakdown = results['torque_breakdown']
        report += f"""
Torque Analysis Breakdown:
Torque Factor:             {breakdown.get('torque_factor', 'N/A'):.2f}
Operating Torque:          {breakdown.get('operating_torque', 'N/A'):.0f} ft-lbf
Breakaway Torque:          {breakdown.get('breakaway_torque', 'N/A'):.0f} ft-lbf
Bearing Friction:          {breakdown.get('bearing_friction', 'N/A'):.0f} ft-lbf
Total Required Torque:     {breakdown.get('total_torque', 'N/A'):.0f} ft-lbf
"""

    # Material recommendations
    report += f"""
MATERIAL RECOMMENDATIONS:
=========================
"""
    if 'recommendations' in results:
        materials = results['recommendations']
        report += f"""Selected Materials:
Body Material:             {materials.get('Body Material', 'N/A')}
Trim Material:             {materials.get('Trim Material', 'N/A')}
Bolting:                   {materials.get('Bolting', 'N/A')}
Gasket:                    {materials.get('Gasket', 'N/A')}

Service Category:          {results.get('service_category', 'N/A')}
Material Justification:    {results.get('material_justification', 'N/A')}
"""

    if 'testing_requirements' in results:
        report += f"""
Required Testing:
"""
        for test in results['testing_requirements']:
            report += f"• {test}"

    # Compliance information
    if 'compliance_check' in results:
        report += f"""
COMPLIANCE INFORMATION:
=======================
{results['compliance_check']}
"""

    # Safety factor analysis
    if 'safety_factor_rec' in inputs:
        sf_rec = inputs['safety_factor_rec']
        report += f"""
SAFETY FACTOR ANALYSIS:
=======================
Recommended Factor:        {sf_rec.get('recommended_factor', 'N/A')}
Category:                  {sf_rec.get('category', 'N/A')}
Justification:             {sf_rec.get('justification', 'N/A')}
"""

    # Additional recommendations
    if 'additional_recommendations' in results:
        report += f"""
ADDITIONAL RECOMMENDATIONS:
===========================
"""
        for rec in results['additional_recommendations']:
            report += f"• {rec}"

    # Vendor alternatives
    if 'alternative_materials' in results:
        alternatives = results['alternative_materials']
        report += f"""
ALTERNATIVE MATERIALS:
======================
"""
        for component, options in alternatives.items():
            report += f"{component}: {', '.join(options)}"

    # Final disclaimers
    report += f"""

CALCULATION SUMMARY:
====================
Enhanced Features Applied:
✓ ISA RP75.23 Five-Level Sigma Method for cavitation analysis
✓ Reynolds Number Correction for non-turbulent flow (FR factor)
✓ Enhanced actuator sizing with proper safety factors
✓ Industry-standard valve opening validation (20-80% range)
✓ Travel-dependent valve coefficients (FL, Kc, Xt)
✓ Comprehensive material selection with compliance checking
✓ Enhanced noise prediction with {results.get('method', 'standard')} method
✓ Multi-scenario flow validation and safety factor recommendations

IMPORTANT DISCLAIMERS:
======================
1. This report is generated for preliminary valve sizing purposes only.

2. Final valve selection must be verified with manufacturer-specific software 
   and confirmed against actual service conditions.

3. All calculations follow published industry standards (ISA S75.01, 
   ISA RP75.23, IEC 60534-8-3, API 6D, NACE MR0175, ASME B16.34) but 
   require professional engineering judgment for final application.

4. Material selections are based on general service conditions. Specific 
   environmental factors, code requirements, and operational constraints 
   must be considered in final design.

5. Noise predictions are estimates. Actual noise levels may vary based on 
   installation conditions, piping configuration, and downstream equipment.

6. Actuator sizing includes standard safety factors but does not account for 
   all possible operational scenarios. Consult actuator manufacturers for 
   final selection and verification.

7. This analysis assumes steady-state conditions. Dynamic behavior, control 
   response, and system stability should be evaluated separately.

Report generated by Enhanced Valve Sizing Application v2.0
Compliant with international valve sizing standards
Professional engineering review recommended for critical applications

===============================
END OF REPORT
===============================
"""
    return report

# Helper functions for unit formatting
def get_flow_unit(inputs):
    """Get appropriate flow unit based on fluid type and unit system"""
    if inputs.get('fluid_type') == 'Liquid':
        return 'm³/hr' if inputs.get('unit_system') == 'Metric' else 'gpm'
    else:
        return 'Nm³/hr' if inputs.get('unit_system') == 'Metric' else 'scfh'

def get_pressure_unit(inputs):
    """Get pressure unit"""
    return 'bar' if inputs.get('unit_system') == 'Metric' else 'psi'

def get_temp_unit(inputs):
    """Get temperature unit"""
    return '°C' if inputs.get('unit_system') == 'Metric' else '°F'

def get_density_unit(inputs):
    """Get density unit"""
    return 'kg/m³' if inputs.get('unit_system') == 'Metric' else 'SG'

def get_force_unit(inputs):
    """Get force unit"""
    return 'N' if inputs.get('unit_system') == 'Metric' else 'lbf'

def get_torque_unit(inputs):
    """Get torque unit"""
    return 'Nm' if inputs.get('unit_system') == 'Metric' else 'ft-lbf'

def format_actuator_type(actuator_type):
    """Format actuator type for display"""
    type_map = {
        'pneumatic_spring_diaphragm': 'Pneumatic Spring-Diaphragm',
        'pneumatic_piston': 'Pneumatic Piston',
        'electric_linear': 'Electric Linear',
        'pneumatic_rotary': 'Pneumatic Rotary',
        'electric_rotary': 'Electric Rotary'
    }
    return type_map.get(actuator_type, actuator_type)

def add_detailed_analysis_section(pdf, inputs, results):
    """Add detailed technical analysis section to PDF"""
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'DETAILED TECHNICAL ANALYSIS', 0, 1)

    # Add coefficient data
    if 'fl_curve' in inputs or 'kc_curve' in inputs:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Travel-Dependent Coefficients', 0, 1)
        pdf.set_font('Arial', '', 10)

        if 'valve_opening_used' in results:
            pdf.cell(0, 6, f"Analysis performed at {results['valve_opening_used']}% valve opening", 0, 1)

        pdf.cell(0, 6, f"FL coefficient: {inputs.get('fl', 'N/A'):.3f}", 0, 1)
        pdf.cell(0, 6, f"Kc coefficient: {inputs.get('kc', 'N/A'):.3f}", 0, 1)
        pdf.ln(5)

    # Add validation details
    if 'rangeability_validation' in results:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, 'Multi-Scenario Flow Validation', 0, 1)
        pdf.set_font('Arial', '', 10)

        validation = results['rangeability_validation']
        for scenario, result in validation.items():
            if scenario not in ['overall_valid', 'summary']:
                status_symbol = "✓" if result.get('valid', False) else "⚠"
                pdf.cell(0, 6, f"{status_symbol} {scenario.title()}: {result.get('opening_percent', 0):.1f}% ({result.get('status', 'N/A')})", 0, 1)
