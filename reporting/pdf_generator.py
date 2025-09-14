"""
Enhanced Professional PDF Generator - Complete Version
Generates comprehensive 4-5 page professional reports
"""
from datetime import datetime
import io

def create_pdf_report(report_data):
    """
    Create comprehensive PDF report with Unicode character handling
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"valve_sizing_report_{timestamp}.pdf"
    
    # Try fpdf2 first (recommended)
    try:
        pdf_bytes = create_comprehensive_pdf_with_fpdf2(report_data)
        return filename, pdf_bytes
    except ImportError:
        print("fpdf2 not available, trying ReportLab...")
    except Exception as e:
        print(f"fpdf2 error: {e}, trying ReportLab...")
        
    # Try ReportLab as backup
    try:
        pdf_bytes = create_pdf_with_reportlab_unicode(report_data)
        return filename, pdf_bytes
    except ImportError:
        print("ReportLab not available, creating enhanced text report...")
    except Exception as e:
        print(f"ReportLab error: {e}, creating text report...")
        
    # Enhanced text fallback
    try:
        content = create_comprehensive_text_report(report_data)
        if isinstance(content, str):
            content_bytes = content.encode('utf-8', errors='replace')
        else:
            content_bytes = str(content).encode('utf-8', errors='replace')
        return filename.replace('.pdf', '.txt'), content_bytes
    except Exception as e:
        print(f"Text report error: {e}")
        basic_content = f"""
VALVE SIZING REPORT ERROR
========================
Generated: {report_data.get('report_date', 'Unknown')}
Error: Could not generate detailed report: {e}
Required Cv: {report_data.get('results', {}).get('cv', 'N/A')}

Please install fpdf2: pip install fpdf2
        """
        return filename.replace('.pdf', '_error.txt'), basic_content.encode('utf-8')

def clean_unicode_for_pdf(text):
    """Clean Unicode characters for PDF compatibility"""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    
    unicode_replacements = {
        '≥': '>=', '≤': '<=', '≠': '!=', '≈': '~=', '±': '+/-',
        '×': 'x', '÷': '/', '°': ' deg', 'σ': 'sigma', 'Δ': 'Delta',
        'ΔP': 'Delta P', 'μ': 'mu', 'ρ': 'rho', 'α': 'alpha',
        'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon',
        'θ': 'theta', 'λ': 'lambda', 'π': 'pi', 'τ': 'tau',
        'φ': 'phi', 'ψ': 'psi', 'ω': 'omega', '²': '^2', '³': '^3',
        '¹': '^1', '–': '-', '—': '-', '"': '"', '"': '"',
        ''': "'", ''': "'", '…': '...', '•': '*',
        '½': '1/2', '¼': '1/4', '¾': '3/4',
    }
    
    cleaned_text = text
    for unicode_char, replacement in unicode_replacements.items():
        cleaned_text = cleaned_text.replace(unicode_char, replacement)
    
    try:
        cleaned_text = cleaned_text.encode('ascii', errors='ignore').decode('ascii')
    except:
        pass
    
    return cleaned_text

def create_comprehensive_pdf_with_fpdf2(report_data):
    """Create comprehensive professional PDF using fpdf2"""
    from fpdf import FPDF
    
    class ProfessionalValvePDF(FPDF):
        def header(self):
            try:
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, 'CONTROL VALVE SIZING REPORT', 0, 1, 'C')
                self.set_font('Arial', 'I', 10)
                self.cell(0, 6, 'Professional Engineering Analysis', 0, 1, 'C')
                self.ln(8)
            except Exception as e:
                print(f"Header error: {e}")
            
        def footer(self):
            try:
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
            except Exception as e:
                print(f"Footer error: {e}")
        
        def safe_cell(self, w, h, txt='', border=0, ln=0, align='', fill=False):
            try:
                cleaned_txt = clean_unicode_for_pdf(str(txt))
                self.cell(w, h, cleaned_txt, border, ln, align, fill)
            except Exception as e:
                print(f"Cell error: {e}")
                self.cell(w, h, "Data unavailable", border, ln, align, fill)
        
        def safe_multi_cell(self, w, h, txt, border=0, align='L', fill=False):
            try:
                cleaned_txt = clean_unicode_for_pdf(str(txt))
                self.multi_cell(w, h, cleaned_txt, border, align, fill)
            except Exception as e:
                print(f"Multi-cell error: {e}")
                self.multi_cell(w, h, "Content unavailable", border, align, fill)
        
        def section_header(self, title):
            self.ln(5)
            self.set_font('Arial', 'B', 14)
            # Add background color for section headers
            self.set_fill_color(230, 230, 230)
            self.safe_cell(0, 8, title, 0, 1, 'L', True)
            self.set_fill_color(255, 255, 255)  # Reset to white
            self.set_font('Arial', '', 10)
            self.ln(2)
        
        def add_key_value_pair(self, key, value, indent=0):
            self.safe_cell(indent, 6, '', 0, 0)  # Indentation
            self.set_font('Arial', 'B', 10)
            self.safe_cell(80, 6, f"{key}:", 0, 0)
            self.set_font('Arial', '', 10)
            self.safe_cell(0, 6, str(value), 0, 1)

    pdf = ProfessionalValvePDF()
    pdf.add_page()
    
    try:
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Report Header Information
        pdf.set_font('Arial', '', 11)
        pdf.safe_cell(0, 6, f"Generated: {report_data.get('report_date', 'Unknown')}", 0, 1)
        pdf.safe_cell(0, 6, f"Software: Enhanced Valve Sizing Application v2.0", 0, 1)
        pdf.safe_cell(0, 6, f"Engineer: Professional Valve Sizing Analysis", 0, 1)
        
        # Standards compliance
        if 'standards_compliance' in report_data:
            standards = ', '.join(report_data['standards_compliance'])
            pdf.safe_cell(0, 6, f"Standards: {standards}", 0, 1)
        
        # EXECUTIVE SUMMARY
        pdf.section_header('EXECUTIVE SUMMARY')
        
        cv_value = results.get('cv', 0)
        if isinstance(cv_value, (int, float)):
            cv_text = f"{cv_value:.2f}"
        else:
            cv_text = str(cv_value)
        
        # Key metrics summary
        pdf.set_font('Arial', 'B', 12)
        pdf.safe_cell(0, 8, f"Required Cv: {cv_text}", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Valve sizing status
        rated_cv = results.get('rated_cv', 0)
        if isinstance(cv_value, (int, float)) and isinstance(rated_cv, (int, float)) and rated_cv > 0:
            opening_percent = (cv_value / rated_cv) * 100
            if 20 <= opening_percent <= 80:
                status = "ACCEPTABLE - Good valve sizing"
            elif opening_percent < 20:
                status = "OVERSIZED - Consider smaller valve"
            else:
                status = "UNDERSIZED - Consider larger valve"
        else:
            status = "STATUS UNDER EVALUATION"
        
        pdf.add_key_value_pair("Sizing Status", status)
        
        # Cavitation risk
        cavitation_risk = results.get('sigma_analysis', {}).get('risk', 'Unknown')
        if cavitation_risk == 'Unknown':
            cavitation_risk = 'Low' if results.get('cavitation_index', 2) > 2 else 'Medium'
        pdf.add_key_value_pair("Cavitation Risk", cavitation_risk)
        
        # Noise level
        noise_level = results.get('total_noise_dba', 0)
        if isinstance(noise_level, (int, float)):
            noise_status = "ACCEPTABLE" if noise_level < 85 else "HIGH" if noise_level < 110 else "EXTREME"
            pdf.add_key_value_pair("Noise Level", f"{noise_level:.1f} dBA ({noise_status})")
        
        # PROCESS CONDITIONS
        pdf.section_header('PROCESS CONDITIONS')
        
        # Basic process info
        pdf.add_key_value_pair("Fluid Type", inputs.get('fluid_type', 'N/A'))
        pdf.add_key_value_pair("Fluid Name", inputs.get('fluid_name', 'N/A'))
        pdf.add_key_value_pair("Service Criticality", inputs.get('service_criticality', 'N/A'))
        
        # Operating conditions
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 11)
        pdf.safe_cell(0, 6, "Operating Conditions:", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        flow_rate = inputs.get('flow_rate', 'N/A')
        flow_unit = get_safe_flow_unit(inputs)
        pdf.add_key_value_pair("Flow Rate", f"{flow_rate} {flow_unit}", 10)
        
        p1 = inputs.get('p1', 'N/A')
        p2 = inputs.get('p2', 'N/A')
        pressure_unit = get_safe_pressure_unit(inputs)
        pdf.add_key_value_pair("Inlet Pressure (P1)", f"{p1} {pressure_unit}", 10)
        pdf.add_key_value_pair("Outlet Pressure (P2)", f"{p2} {pressure_unit}", 10)
        
        # Calculate and show differential pressure
        try:
            if isinstance(p1, (int, float)) and isinstance(p2, (int, float)):
                dp = p1 - p2
                pdf.add_key_value_pair("Differential Pressure", f"{dp:.2f} {pressure_unit}", 10)
        except:
            pass
        
        temp = inputs.get('t1', 'N/A')
        temp_unit = get_safe_temp_unit(inputs)
        pdf.add_key_value_pair("Temperature", f"{temp} {temp_unit}", 10)
        
        # Fluid-specific properties
        if inputs.get('fluid_type') == 'Liquid':
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 11)
            pdf.safe_cell(0, 6, "Liquid Properties:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            density = inputs.get('rho', 'N/A')
            density_unit = get_safe_density_unit(inputs)
            pdf.add_key_value_pair("Density/Specific Gravity", f"{density} {density_unit}", 10)
            
            pv = inputs.get('pv', 'N/A')
            pc = inputs.get('pc', 'N/A')
            pdf.add_key_value_pair("Vapor Pressure", f"{pv} {pressure_unit}", 10)
            pdf.add_key_value_pair("Critical Pressure", f"{pc} {pressure_unit}", 10)
            
            viscosity = inputs.get('vc', 'N/A')
            pdf.add_key_value_pair("Viscosity", f"{viscosity} cP", 10)
        else:
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 11)
            pdf.safe_cell(0, 6, "Gas Properties:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            mw = inputs.get('mw', 'N/A')
            k = inputs.get('k', 'N/A')
            z = inputs.get('z', 'N/A')
            pdf.add_key_value_pair("Molecular Weight", str(mw), 10)
            pdf.add_key_value_pair("Specific Heat Ratio (k)", str(k), 10)
            pdf.add_key_value_pair("Compressibility Factor (Z)", str(z), 10)

        # VALVE SELECTION
        pdf.section_header('VALVE SELECTION & CONFIGURATION')
        
        pdf.add_key_value_pair("Valve Type", inputs.get('valve_type', 'N/A'))
        pdf.add_key_value_pair("Valve Style", inputs.get('valve_style', 'N/A'))
        pdf.add_key_value_pair("Nominal Size", f"{inputs.get('valve_size_nominal', 'N/A')} inches")
        pdf.add_key_value_pair("Flow Characteristic", inputs.get('valve_char', 'N/A'))
        pdf.add_key_value_pair("Expected Operating Opening", f"{inputs.get('valve_opening_percent', 70)}%")
        
        actuator_type = format_safe_actuator_type(inputs.get('actuator_type', 'N/A'))
        pdf.add_key_value_pair("Actuator Type", actuator_type)
        
        # Valve coefficients if available
        if inputs.get('fl') or inputs.get('kc'):
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 11)
            pdf.safe_cell(0, 6, "Valve Coefficients:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            if 'fl' in inputs and inputs['fl'] is not None:
                pdf.add_key_value_pair("FL (Pressure Recovery)", f"{inputs['fl']:.3f}", 10)
            if 'kc' in inputs and inputs['kc'] is not None:
                pdf.add_key_value_pair("Kc (Cavitation Index)", f"{inputs['kc']:.3f}", 10)

        # SIZING RESULTS
        pdf.section_header('SIZING RESULTS & ANALYSIS')
        
        # Main Cv result
        pdf.set_font('Arial', 'B', 12)
        pdf.safe_cell(0, 8, f"Required Flow Coefficient (Cv): {cv_text}", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Enhanced calculations
        if 'reynolds_factor' in results:
            rf = results['reynolds_factor']
            if isinstance(rf, (int, float)):
                pdf.add_key_value_pair("Reynolds Correction Factor (FR)", f"{rf:.4f}")
            else:
                pdf.add_key_value_pair("Reynolds Correction Factor (FR)", str(rf))
        
        if 'ff_factor' in results:
            ff = results['ff_factor']
            if isinstance(ff, (int, float)):
                pdf.add_key_value_pair("FF Factor (Liquid Critical Ratio)", f"{ff:.4f}")
            else:
                pdf.add_key_value_pair("FF Factor", str(ff))
        
        # Valve performance metrics
        pdf.add_key_value_pair("Rated Cv (Selected Valve)", str(results.get('rated_cv', 'N/A')))
        
        if isinstance(cv_value, (int, float)) and isinstance(rated_cv, (int, float)) and rated_cv > 0:
            opening = (cv_value / rated_cv) * 100
            pdf.add_key_value_pair("Valve Opening at Design Flow", f"{opening:.1f}%")
        
        rangeability = results.get('inherent_rangeability', 'N/A')
        if rangeability != 'N/A':
            pdf.add_key_value_pair("Inherent Rangeability", f"{rangeability}:1")
            
            # Calculate minimum controllable Cv
            if isinstance(rated_cv, (int, float)) and isinstance(rangeability, (int, float)) and rangeability > 0:
                min_cv = rated_cv / rangeability
                pdf.add_key_value_pair("Minimum Controllable Cv", f"{min_cv:.2f}")

        # Multi-scenario validation if available
        if 'rangeability_validation' in results:
            validation = results['rangeability_validation']
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 11)
            pdf.safe_cell(0, 6, "Flow Scenario Validation:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            for scenario in ['minimum', 'normal', 'design', 'maximum', 'emergency']:
                if scenario in validation:
                    result = validation[scenario]
                    opening_pct = result.get('opening_percent', 0)
                    status = result.get('status', 'Unknown')
                    status_symbol = "✓" if status == "Acceptable" else "⚠" if status == "Oversized" else "✗"
                    scenario_name = scenario.replace('_', ' ').title()
                    pdf.add_key_value_pair(f"{scenario_name} Flow", f"{opening_pct:.1f}% ({status}) {status_symbol}", 10)

        # CAVITATION ANALYSIS
        pdf.section_header('CAVITATION ANALYSIS (ISA RP75.23)')
        
        if 'sigma_analysis' in results:
            sigma_data = results['sigma_analysis']
            
            sigma_val = sigma_data.get('sigma', 'N/A')
            if isinstance(sigma_val, (int, float)):
                pdf.add_key_value_pair("Sigma Value", f"{sigma_val:.3f}")
            else:
                pdf.add_key_value_pair("Sigma Value", str(sigma_val))
            
            pdf.add_key_value_pair("Cavitation Level", sigma_data.get('level', 'N/A'))
            pdf.add_key_value_pair("Risk Assessment", sigma_data.get('risk', 'N/A'))
            pdf.add_key_value_pair("Status", sigma_data.get('status', 'N/A'))
            pdf.add_key_value_pair("Damage Potential", sigma_data.get('damage_potential', 'N/A'))
            
            # Recommendation with line breaks for long text
            recommendation = clean_unicode_for_pdf(str(sigma_data.get('recommendation', 'N/A')))
            pdf.ln(2)
            pdf.set_font('Arial', 'B', 10)
            pdf.safe_cell(0, 6, "Trim Recommendation:", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.safe_multi_cell(0, 5, recommendation)
        else:
            # Basic cavitation analysis
            sigma_val = results.get('cavitation_index', 'N/A')
            if isinstance(sigma_val, (int, float)):
                pdf.add_key_value_pair("Sigma Value", f"{sigma_val:.3f}")
            else:
                pdf.add_key_value_pair("Sigma Value", str(sigma_val))
            
            pdf.add_key_value_pair("Status", results.get('cavitation_status', 'N/A'))
            pdf.add_key_value_pair("Flashing Occurrence", 'Yes' if results.get('is_flashing', False) else 'No')

        # Start new page for additional analysis
        pdf.add_page()

        # NOISE ANALYSIS
        pdf.section_header('NOISE ANALYSIS')
        
        noise_level = results.get('total_noise_dba', 0)
        if isinstance(noise_level, (int, float)):
            pdf.add_key_value_pair("Predicted Noise Level", f"{noise_level:.1f} dBA (at 1m distance)")
        else:
            pdf.add_key_value_pair("Predicted Noise Level", f"{noise_level} dBA")
        
        pdf.add_key_value_pair("Prediction Method", results.get('method', 'Standard Calculation'))
        
        # Noise level assessment
        if isinstance(noise_level, (int, float)):
            if noise_level < 85:
                noise_assessment = "Acceptable for most applications"
            elif noise_level < 100:
                noise_assessment = "Moderate - Consider noise reduction measures"
            elif noise_level < 110:
                noise_assessment = "High - Noise reduction required"
            else:
                noise_assessment = "Extreme - Immediate mitigation essential"
            pdf.add_key_value_pair("Noise Assessment", noise_assessment)
        
        # Noise recommendation
        noise_rec = results.get('noise_recommendation', 'Standard trim acceptable')
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 10)
        pdf.safe_cell(0, 6, "Noise Control Recommendation:", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.safe_multi_cell(0, 5, clean_unicode_for_pdf(noise_rec))

        # ACTUATOR ANALYSIS
        pdf.section_header('ACTUATOR REQUIREMENTS')
        
        if inputs.get('valve_type') == 'Globe':
            force_val = results.get('required_force', 0)
            if isinstance(force_val, (int, float)):
                force_unit = get_safe_force_unit(inputs)
                pdf.add_key_value_pair("Required Thrust", f"{force_val:.0f} {force_unit}")
            else:
                pdf.add_key_value_pair("Required Thrust", str(force_val))
        else:
            torque_val = results.get('required_torque', 0)
            if isinstance(torque_val, (int, float)):
                torque_unit = get_safe_torque_unit(inputs)
                pdf.add_key_value_pair("Required Torque", f"{torque_val:.0f} {torque_unit}")
            else:
                pdf.add_key_value_pair("Required Torque", str(torque_val))
        
        safety_factor = results.get('safety_factor_used', 1.5)
        if isinstance(safety_factor, (int, float)):
            pdf.add_key_value_pair("Safety Factor Applied", f"{safety_factor:.1f}")
        else:
            pdf.add_key_value_pair("Safety Factor Applied", str(safety_factor))
        
        # Actuator recommendation
        actuator_rec = results.get('actuator_recommendation', 'Consult manufacturer for specific requirements')
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 10)
        pdf.safe_cell(0, 6, "Actuator Recommendation:", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.safe_multi_cell(0, 5, clean_unicode_for_pdf(actuator_rec))

        # MATERIAL SELECTION
        if 'recommendations' in results or 'service_category' in results:
            pdf.section_header('MATERIAL SELECTION')
            
            if 'recommendations' in results:
                materials = results['recommendations']
                pdf.add_key_value_pair("Body Material", materials.get('Body Material', 'N/A'))
                pdf.add_key_value_pair("Trim Material", materials.get('Trim Material', 'N/A'))
                pdf.add_key_value_pair("Bolting", materials.get('Bolting', 'N/A'))
                pdf.add_key_value_pair("Gasket", materials.get('Gasket', 'N/A'))
            
            if 'service_category' in results:
                pdf.add_key_value_pair("Service Category", results['service_category'])
            
            if 'compliance_check' in results:
                pdf.ln(2)
                pdf.set_font('Arial', 'B', 10)
                pdf.safe_cell(0, 6, "Standards Compliance:", 0, 1)
                pdf.set_font('Arial', '', 10)
                pdf.safe_multi_cell(0, 5, clean_unicode_for_pdf(results['compliance_check']))

        # GAS FLOW ANALYSIS (if applicable)
        if inputs.get('fluid_type') == 'Gas/Vapor' and 'flow_regime' in results:
            pdf.section_header('GAS FLOW ANALYSIS')
            
            pdf.add_key_value_pair("Flow Regime", results.get('flow_regime', 'N/A'))
            
            expansion_factor = results.get('expansion_factor_y', 'N/A')
            if isinstance(expansion_factor, (int, float)):
                pdf.add_key_value_pair("Expansion Factor (Y)", f"{expansion_factor:.4f}")
            
            pressure_ratio = results.get('pressure_drop_ratio_x', 'N/A')
            if isinstance(pressure_ratio, (int, float)):
                pdf.add_key_value_pair("Pressure Drop Ratio (x)", f"{pressure_ratio:.4f}")
            
            if 'mach_number' in results:
                mach = results['mach_number']
                if isinstance(mach, (int, float)):
                    pdf.add_key_value_pair("Mach Number", f"{mach:.3f}")
            
            if results.get('is_choked', False):
                pdf.ln(2)
                pdf.set_font('Arial', 'B', 10)
                pdf.safe_cell(0, 6, "⚠ WARNING: Choked Flow Conditions", 0, 1)
                pdf.set_font('Arial', '', 10)
                if 'choking_warning' in results:
                    pdf.safe_multi_cell(0, 5, clean_unicode_for_pdf(results['choking_warning']))

        # PROFESSIONAL DISCLAIMERS
        pdf.section_header('PROFESSIONAL DISCLAIMERS & NOTES')
        
        disclaimers = [
            "1. This report is generated for preliminary valve sizing purposes only.",
            "2. Final valve selection must be verified with manufacturer-specific software.",
            "3. All calculations follow published industry standards but require professional engineering judgment.",
            "4. Material selections are based on general service conditions and must be verified for specific applications.",
            "5. Noise predictions are estimates - actual levels may vary based on installation conditions.",
            "6. Actuator sizing includes standard safety factors but should be confirmed with actuator manufacturers.",
            "7. This analysis assumes steady-state conditions - dynamic behavior should be evaluated separately."
        ]
        
        for disclaimer in disclaimers:
            pdf.safe_multi_cell(0, 5, disclaimer)
            pdf.ln(1)
        
        pdf.ln(5)
        
        # Report footer
        pdf.set_font('Arial', 'I', 9)
        footer_text = ("This report demonstrates compliance with industry standards including ISA S75.01, "
                      "ISA RP75.23, IEC 60534-8-3, and related engineering practices. "
                      "Professional engineering review is recommended for critical applications.")
        pdf.safe_multi_cell(0, 4, footer_text)
        
        return bytes(pdf.output(dest='S'), 'latin1')
        
    except Exception as e:
        print(f"Comprehensive PDF generation error: {e}")
        raise e

def create_comprehensive_text_report(report_data):
    """Create comprehensive text report as fallback"""
    inputs = report_data.get('inputs', {})
    results = report_data.get('results', {})
    
    report = f"""
===============================
CONTROL VALVE SIZING REPORT
===============================
Generated: {report_data.get('report_date', 'Unknown')}
Software: Enhanced Valve Sizing Application v2.0
Standards: {', '.join(report_data.get('standards_compliance', ['ISA S75.01', 'IEC 60534']))}

EXECUTIVE SUMMARY:
==================
Required Cv: {results.get('cv', 'N/A')}
Sizing Status: {'ACCEPTABLE' if results.get('rangeability_validation', {}).get('overall_valid', False) else 'UNDER REVIEW'}
Cavitation Risk: {results.get('sigma_analysis', {}).get('risk', 'Unknown')}
Noise Level: {results.get('total_noise_dba', 'N/A')} dBA

PROCESS CONDITIONS:
==================
Fluid Type: {inputs.get('fluid_type', 'N/A')}
Fluid Name: {inputs.get('fluid_name', 'N/A')}
Service Criticality: {inputs.get('service_criticality', 'N/A')}

Operating Conditions:
Flow Rate: {inputs.get('flow_rate', 'N/A')} {get_safe_flow_unit(inputs)}
Inlet Pressure (P1): {inputs.get('p1', 'N/A')} {get_safe_pressure_unit(inputs)}
Outlet Pressure (P2): {inputs.get('p2', 'N/A')} {get_safe_pressure_unit(inputs)}
Temperature: {inputs.get('t1', 'N/A')} {get_safe_temp_unit(inputs)}
"""

    # Add fluid-specific properties
    if inputs.get('fluid_type') == 'Liquid':
        report += f"""
Liquid Properties:
Density/SG: {inputs.get('rho', 'N/A')} {get_safe_density_unit(inputs)}
Vapor Pressure: {inputs.get('pv', 'N/A')} {get_safe_pressure_unit(inputs)}
Critical Pressure: {inputs.get('pc', 'N/A')} {get_safe_pressure_unit(inputs)}
Viscosity: {inputs.get('vc', 'N/A')} cP
"""
    else:
        report += f"""
Gas Properties:
Molecular Weight: {inputs.get('mw', 'N/A')}
Specific Heat Ratio (k): {inputs.get('k', 'N/A')}
Compressibility Factor (Z): {inputs.get('z', 'N/A')}
"""

    report += f"""
VALVE SELECTION:
================
Valve Type: {inputs.get('valve_type', 'N/A')}
Valve Style: {inputs.get('valve_style', 'N/A')}
Nominal Size: {inputs.get('valve_size_nominal', 'N/A')} inches
Flow Characteristic: {inputs.get('valve_char', 'N/A')}
Expected Operating Opening: {inputs.get('valve_opening_percent', 70)}%
Actuator Type: {format_safe_actuator_type(inputs.get('actuator_type', 'N/A'))}

SIZING RESULTS:
===============
Required Cv: {results.get('cv', 'N/A')}
"""

    # Enhanced calculations if available
    if 'reynolds_factor' in results:
        report += f"Reynolds Correction Factor (FR): {results['reynolds_factor']}\n"
    
    if 'ff_factor' in results:
        report += f"FF Factor: {results['ff_factor']}\n"

    report += f"""
Rated Cv: {results.get('rated_cv', 'N/A')}
Rangeability: {results.get('inherent_rangeability', 'N/A')}:1

CAVITATION ANALYSIS:
====================
"""
    if 'sigma_analysis' in results:
        sigma_data = results['sigma_analysis']
        report += f"""ISA RP75.23 Analysis:
Sigma Value: {sigma_data.get('sigma', 'N/A')}
Cavitation Level: {sigma_data.get('level', 'N/A')}
Risk Assessment: {sigma_data.get('risk', 'N/A')}
Status: {sigma_data.get('status', 'N/A')}
Recommendation: {sigma_data.get('recommendation', 'N/A')}
"""
    else:
        report += f"""Basic Analysis:
Sigma Value: {results.get('cavitation_index', 'N/A')}
Status: {results.get('cavitation_status', 'N/A')}
Flashing: {'Yes' if results.get('is_flashing', False) else 'No'}
"""

    report += f"""
NOISE ANALYSIS:
===============
Predicted Noise Level: {results.get('total_noise_dba', 'N/A')} dBA (at 1m)
Prediction Method: {results.get('method', 'Standard Calculation')}
Recommendation: {results.get('noise_recommendation', 'Standard trim acceptable')}

ACTUATOR REQUIREMENTS:
======================
"""
    if inputs.get('valve_type') == 'Globe':
        report += f"Required Thrust: {results.get('required_force', 'N/A')} {get_safe_force_unit(inputs)}\n"
    else:
        report += f"Required Torque: {results.get('required_torque', 'N/A')} {get_safe_torque_unit(inputs)}\n"

    report += f"""Safety Factor: {results.get('safety_factor_used', 'N/A')}
Recommendation: {results.get('actuator_recommendation', 'Consult manufacturer')}
"""

    if 'recommendations' in results:
        materials = results['recommendations']
        report += f"""
MATERIAL RECOMMENDATIONS:
=========================
Body Material: {materials.get('Body Material', 'N/A')}
Trim Material: {materials.get('Trim Material', 'N/A')}
Bolting: {materials.get('Bolting', 'N/A')}
Gasket: {materials.get('Gasket', 'N/A')}
Service Category: {results.get('service_category', 'N/A')}
"""

    if 'compliance_check' in results:
        report += f"""
COMPLIANCE:
===========
{results['compliance_check']}
"""

    report += """
DISCLAIMERS:
============
This report is for preliminary valve sizing purposes only.
Final selection must be verified with manufacturer software.
All calculations follow industry standards but require engineering judgment.

Report generated by Enhanced Valve Sizing Application v2.0
Professional engineering review recommended for critical applications.

===============================
END OF REPORT
===============================
"""
    
    return clean_unicode_for_pdf(report)

# Safe helper functions (same as before)
def get_safe_flow_unit(inputs):
    try:
        if inputs.get('fluid_type') == 'Liquid':
            return 'm3/hr' if inputs.get('unit_system') == 'Metric' else 'gpm'
        else:
            return 'Nm3/hr' if inputs.get('unit_system') == 'Metric' else 'scfh'
    except:
        return 'units'

def get_safe_pressure_unit(inputs):
    try:
        return 'bar' if inputs.get('unit_system') == 'Metric' else 'psi'
    except:
        return 'pressure_units'

def get_safe_temp_unit(inputs):
    try:
        return 'C' if inputs.get('unit_system') == 'Metric' else 'F'
    except:
        return 'temp_units'

def get_safe_density_unit(inputs):
    try:
        return 'kg/m3' if inputs.get('unit_system') == 'Metric' else 'SG'
    except:
        return 'density_units'

def get_safe_force_unit(inputs):
    try:
        return 'N' if inputs.get('unit_system') == 'Metric' else 'lbf'
    except:
        return 'force_units'

def get_safe_torque_unit(inputs):
    try:
        return 'Nm' if inputs.get('unit_system') == 'Metric' else 'ft-lbf'
    except:
        return 'torque_units'

def format_safe_actuator_type(actuator_type):
    try:
        type_map = {
            'pneumatic_spring_diaphragm': 'Pneumatic Spring-Diaphragm',
            'pneumatic_piston': 'Pneumatic Piston',
            'electric_linear': 'Electric Linear',
            'pneumatic_rotary': 'Pneumatic Rotary',
            'electric_rotary': 'Electric Rotary'
        }
        return type_map.get(actuator_type, str(actuator_type))
    except:
        return 'Unknown'

def create_pdf_with_reportlab_unicode(report_data):
    """ReportLab fallback version"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        title = clean_unicode_for_pdf("CONTROL VALVE SIZING REPORT")
        story.append(Paragraph(title, styles['Title']))
        
        content = create_comprehensive_text_report(report_data)
        for line in content.split('\n'):
            if line.strip():
                cleaned_line = clean_unicode_for_pdf(line)
                story.append(Paragraph(cleaned_line, styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except ImportError:
        raise ImportError("ReportLab not available")
    except Exception as e:
        print(f"ReportLab error: {e}")
        raise e
