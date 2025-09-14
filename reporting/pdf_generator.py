"""
Complete PDF generator
"""
from datetime import datetime
import io

def create_pdf_report(report_data):
    """
    Create comprehensive PDF report with Unicode character handling
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"valve_sizing_report_{timestamp}.pdf"
    
    # Try fpdf2 first with Unicode handling
    try:
        pdf_bytes = create_pdf_with_fpdf2_unicode(report_data)
        return filename, pdf_bytes
    except ImportError:
        print("fpdf2 not available, trying ReportLab...")
    except Exception as e:
        print(f"fpdf2 error: {e}, trying ReportLab...")
        
    # Try ReportLab with Unicode support
    try:
        pdf_bytes = create_pdf_with_reportlab_unicode(report_data)
        return filename, pdf_bytes
    except ImportError:
        print("ReportLab not available, creating Unicode-safe text report...")
    except Exception as e:
        print(f"ReportLab error: {e}, creating text report...")
        
    # Enhanced text fallback with Unicode cleaning
    try:
        content = create_unicode_safe_text_report(report_data)
        # Fix the encoding error by ensuring content is a string
        if isinstance(content, str):
            content_bytes = content.encode('utf-8', errors='replace')
        else:
            content_bytes = str(content).encode('utf-8', errors='replace')
        return filename.replace('.pdf', '.txt'), content_bytes
    except Exception as e:
        print(f"Text report error: {e}")
        # Ultimate fallback - basic report
        basic_content = f"""
VALVE SIZING REPORT ERROR
========================
Generated: {report_data.get('report_date', 'Unknown')}
Error: Could not generate detailed report
Required Cv: {report_data.get('results', {}).get('cv', 'N/A')}

Please check your installation of PDF libraries:
pip install fpdf2
        """
        return filename.replace('.pdf', '_error.txt'), basic_content.encode('utf-8')

def clean_unicode_for_pdf(text):
    """
    Clean Unicode characters that cause PDF generation issues
    """
    if text is None:
        return ""
        
    if not isinstance(text, str):
        text = str(text)
    
    # Define Unicode character replacements
    unicode_replacements = {
        # Mathematical symbols that cause the error
        '≥': '>=',
        '≤': '<=',
        '≠': '!=',
        '≈': '~=',
        '±': '+/-',
        '×': 'x',
        '÷': '/',
        '°': ' deg',
        'σ': 'sigma',
        'Δ': 'Delta',
        'ΔP': 'Delta P',
        'μ': 'mu',
        'ρ': 'rho',
        
        # Greek letters commonly used in engineering
        'α': 'alpha',
        'β': 'beta',
        'γ': 'gamma',
        'δ': 'delta',
        'ε': 'epsilon',
        'θ': 'theta',
        'λ': 'lambda',
        'π': 'pi',
        'τ': 'tau',
        'φ': 'phi',
        'ψ': 'psi',
        'ω': 'omega',
        
        # Superscripts and subscripts
        '²': '^2',
        '³': '^3',
        '¹': '^1',
        
        # Special dashes and quotes
        '–': '-',  # en dash
        '—': '-',  # em dash
        '"': '"',  # smart quotes
        '"': '"',
        ''': "'",  # smart apostrophes  
        ''': "'",
        '…': '...',
        '•': '*',
        
        # Fractions
        '½': '1/2',
        '¼': '1/4',
        '¾': '3/4',
    }
    
    # Apply replacements
    cleaned_text = text
    for unicode_char, replacement in unicode_replacements.items():
        cleaned_text = cleaned_text.replace(unicode_char, replacement)
    
    # Remove any remaining non-ASCII characters
    try:
        cleaned_text = cleaned_text.encode('ascii', errors='ignore').decode('ascii')
    except:
        # If encoding fails, just return the original text
        pass
    
    return cleaned_text

def create_pdf_with_fpdf2_unicode(report_data):
    """Create PDF using fpdf2 with Unicode character handling"""
    from fpdf import FPDF
    
    class UnicodeValveSizingPDF(FPDF):
        def header(self):
            try:
                self.set_font('Arial', 'B', 15)
                title = clean_unicode_for_pdf('CONTROL VALVE SIZING REPORT')
                self.cell(0, 10, title, 0, 1, 'C')
                self.ln(5)
            except Exception as e:
                print(f"Header error: {e}")
            
        def footer(self):
            try:
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
            except Exception as e:
                print(f"Footer error: {e}")
        
        def safe_cell(self, w, h, txt='', border=0, ln=0, align=''):
            """Safe cell method that handles Unicode characters"""
            try:
                cleaned_txt = clean_unicode_for_pdf(str(txt))
                self.cell(w, h, cleaned_txt, border, ln, align)
            except Exception as e:
                print(f"Cell error: {e}")
                # Try with basic text
                try:
                    basic_txt = str(txt).encode('ascii', errors='ignore').decode('ascii')
                    self.cell(w, h, basic_txt, border, ln, align)
                except:
                    self.cell(w, h, "Data unavailable", border, ln, align)
        
        def safe_multi_cell(self, w, h, txt, border=0, align='L'):
            """Safe multi_cell method that handles Unicode characters"""
            try:
                cleaned_txt = clean_unicode_for_pdf(str(txt))
                self.multi_cell(w, h, cleaned_txt, border, align)
            except Exception as e:
                print(f"Multi-cell error: {e}")
                try:
                    basic_txt = str(txt).encode('ascii', errors='ignore').decode('ascii')
                    self.multi_cell(w, h, basic_txt, border, align)
                except:
                    self.multi_cell(w, h, "Content unavailable", border, align)
    
    pdf = UnicodeValveSizingPDF()
    pdf.add_page()
    
    try:
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Report Information
        pdf.set_font('Arial', '', 11)
        pdf.safe_cell(0, 8, f"Generated: {report_data.get('report_date', 'Unknown')}", 0, 1)
        pdf.safe_cell(0, 8, f"Software: Enhanced Valve Sizing Application v2.0", 0, 1)
        
        # Standards compliance
        if 'standards_compliance' in report_data:
            standards_text = f"Standards: {', '.join(report_data['standards_compliance'])}"
            pdf.safe_cell(0, 8, standards_text, 0, 1)
        
        pdf.ln(8)
        
        # Process Conditions Section
        pdf.set_font('Arial', 'B', 14)
        pdf.safe_cell(0, 10, 'PROCESS CONDITIONS', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        process_info = [
            f"Fluid Type: {inputs.get('fluid_type', 'N/A')}",
            f"Fluid Name: {inputs.get('fluid_name', 'N/A')}",
            f"Flow Rate: {inputs.get('flow_rate', 'N/A')} {get_safe_flow_unit(inputs)}",
            f"Inlet Pressure (P1): {inputs.get('p1', 'N/A')} {get_safe_pressure_unit(inputs)}",
            f"Outlet Pressure (P2): {inputs.get('p2', 'N/A')} {get_safe_pressure_unit(inputs)}",
            f"Temperature (T1): {inputs.get('t1', 'N/A')} {get_safe_temp_unit(inputs)}",
        ]
        
        # Add fluid-specific properties
        if inputs.get('fluid_type') == 'Liquid':
            process_info.extend([
                f"Density/SG: {inputs.get('rho', 'N/A')} {get_safe_density_unit(inputs)}",
                f"Vapor Pressure: {inputs.get('pv', 'N/A')} {get_safe_pressure_unit(inputs)}",
                f"Critical Pressure: {inputs.get('pc', 'N/A')} {get_safe_pressure_unit(inputs)}",
                f"Viscosity: {inputs.get('vc', 'N/A')} cP"
            ])
        else:
            process_info.extend([
                f"Molecular Weight: {inputs.get('mw', 'N/A')}",
                f"Specific Heat Ratio (k): {inputs.get('k', 'N/A')}",
                f"Compressibility Factor (Z): {inputs.get('z', 'N/A')}"
            ])
        
        for item in process_info:
            pdf.safe_cell(0, 6, item, 0, 1)
        
        pdf.ln(8)
        
        # Valve Selection Section
        pdf.set_font('Arial', 'B', 14)
        pdf.safe_cell(0, 10, 'VALVE SELECTION', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        valve_info = [
            f"Valve Type: {inputs.get('valve_type', 'N/A')}",
            f"Valve Style: {inputs.get('valve_style', 'N/A')}",
            f"Valve Size: {inputs.get('valve_size_nominal', 'N/A')} inches",
            f"Valve Characteristic: {inputs.get('valve_char', 'N/A')}",
            f"Expected Opening: {inputs.get('valve_opening_percent', 70)}%",
            f"Actuator Type: {format_safe_actuator_type(inputs.get('actuator_type', 'N/A'))}",
        ]
        
        for item in valve_info:
            pdf.safe_cell(0, 6, item, 0, 1)
        
        pdf.ln(8)
        
        # Sizing Results Section
        pdf.set_font('Arial', 'B', 14)
        pdf.safe_cell(0, 10, 'SIZING RESULTS', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Main results
        pdf.set_font('Arial', 'B', 11)
        cv_value = results.get('cv', 0)
        if isinstance(cv_value, (int, float)):
            cv_text = f"Required Flow Coefficient (Cv): {cv_value:.2f}"
        else:
            cv_text = f"Required Flow Coefficient (Cv): {cv_value}"
        pdf.safe_cell(0, 8, cv_text, 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Enhanced results if available
        sizing_results = []
        
        if 'reynolds_factor' in results:
            rf = results['reynolds_factor']
            if isinstance(rf, (int, float)):
                sizing_results.append(f"Reynolds Correction Factor (FR): {rf:.3f}")
            else:
                sizing_results.append(f"Reynolds Correction Factor (FR): {rf}")
        
        if 'ff_factor' in results:
            ff = results['ff_factor']
            if isinstance(ff, (int, float)):
                sizing_results.append(f"FF Factor: {ff:.3f}")
            else:
                sizing_results.append(f"FF Factor: {ff}")
        
        sizing_results.extend([
            f"Rated Cv: {results.get('rated_cv', 'N/A')}",
            f"Rangeability: {results.get('inherent_rangeability', 'N/A')}:1"
        ])
        
        # Calculate valve opening safely
        cv_val = results.get('cv', 0)
        rated_cv_val = results.get('rated_cv', 1)
        if isinstance(cv_val, (int, float)) and isinstance(rated_cv_val, (int, float)) and rated_cv_val > 0:
            opening = (cv_val / rated_cv_val) * 100
            sizing_results.append(f"Valve Opening: {opening:.1f}%")
        else:
            sizing_results.append(f"Valve Opening: N/A")
        
        for item in sizing_results:
            pdf.safe_cell(0, 6, item, 0, 1)
        
        pdf.ln(5)
        
        # Cavitation Analysis
        pdf.set_font('Arial', 'B', 12)
        pdf.safe_cell(0, 8, 'CAVITATION ANALYSIS', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        if 'sigma_analysis' in results:
            sigma_data = results['sigma_analysis']
            cavitation_info = [
                f"Sigma Value: {sigma_data.get('sigma', 'N/A')}",
                f"Cavitation Level: {sigma_data.get('level', 'N/A')}",
                f"Risk Assessment: {sigma_data.get('risk', 'N/A')}",
                f"Status: {sigma_data.get('status', 'N/A')}",
            ]
            
            # Clean recommendation text which likely contains >= symbols
            recommendation = clean_unicode_for_pdf(str(sigma_data.get('recommendation', 'N/A')))
            cavitation_info.append(f"Recommendation: {recommendation}")
        else:
            sigma_val = results.get('cavitation_index', 'N/A')
            if isinstance(sigma_val, (int, float)):
                sigma_text = f"{sigma_val:.2f}"
            else:
                sigma_text = str(sigma_val)
            
            cavitation_info = [
                f"Sigma Value: {sigma_text}",
                f"Status: {results.get('cavitation_status', 'N/A')}",
                f"Flashing: {'Yes' if results.get('is_flashing', False) else 'No'}"
            ]
        
        for item in cavitation_info:
            pdf.safe_cell(0, 6, item, 0, 1)
        
        pdf.ln(5)
        
        # Noise Analysis
        pdf.set_font('Arial', 'B', 12)
        pdf.safe_cell(0, 8, 'NOISE ANALYSIS', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        noise_level = results.get('total_noise_dba', 0)
        if isinstance(noise_level, (int, float)):
            noise_text = f"{noise_level:.1f}"
        else:
            noise_text = str(noise_level)
            
        noise_info = [
            f"Predicted Noise Level: {noise_text} dBA at 1m",
            f"Method: {results.get('method', 'Standard Calculation')}",
            f"Recommendation: {results.get('noise_recommendation', 'Standard trim acceptable')}"
        ]
        
        for item in noise_info:
            pdf.safe_cell(0, 6, item, 0, 1)
        
        pdf.ln(5)
        
        # Actuator Requirements
        pdf.set_font('Arial', 'B', 12)
        pdf.safe_cell(0, 8, 'ACTUATOR REQUIREMENTS', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        if inputs.get('valve_type') == 'Globe':
            force_val = results.get('required_force', 0)
            if isinstance(force_val, (int, float)):
                force_text = f"Required Thrust: {force_val:.0f} {get_safe_force_unit(inputs)}"
            else:
                force_text = f"Required Thrust: {force_val} {get_safe_force_unit(inputs)}"
            pdf.safe_cell(0, 6, force_text, 0, 1)
        else:
            torque_val = results.get('required_torque', 0)
            if isinstance(torque_val, (int, float)):
                torque_text = f"Required Torque: {torque_val:.0f} {get_safe_torque_unit(inputs)}"
            else:
                torque_text = f"Required Torque: {torque_val} {get_safe_torque_unit(inputs)}"
            pdf.safe_cell(0, 6, torque_text, 0, 1)
        
        safety_factor_val = results.get('safety_factor_used', 1.5)
        if isinstance(safety_factor_val, (int, float)):
            safety_factor_text = f"Safety Factor: {safety_factor_val:.1f}"
        else:
            safety_factor_text = f"Safety Factor: {safety_factor_val}"
        pdf.safe_cell(0, 6, safety_factor_text, 0, 1)
        
        recommendation_text = clean_unicode_for_pdf(str(results.get('actuator_recommendation', 'Consult manufacturer')))
        pdf.safe_cell(0, 6, f"Recommendation: {recommendation_text}", 0, 1)
        
        pdf.ln(10)
        
        # Footer disclaimer
        pdf.set_font('Arial', 'I', 8)
        disclaimer = ("DISCLAIMER: This report is generated for preliminary valve sizing purposes. "
                     "Final valve selection should be verified with manufacturer software and "
                     "confirmed against actual service conditions.")
        pdf.safe_multi_cell(0, 4, disclaimer)
        
        return bytes(pdf.output(dest='S'), 'latin1')
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise e

# Safe helper functions with error handling
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

def create_unicode_safe_text_report(report_data):
    """Create text report with Unicode cleaning and error handling"""
    try:
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Create the text report content
        report_content = f"""
CONTROL VALVE SIZING REPORT
============================
Generated: {report_data.get('report_date', 'Unknown')}
Software: Enhanced Valve Sizing Application v2.0

PROCESS CONDITIONS:
Fluid Type: {inputs.get('fluid_type', 'N/A')}
Flow Rate: {inputs.get('flow_rate', 'N/A')} {get_safe_flow_unit(inputs)}
Inlet Pressure: {inputs.get('p1', 'N/A')} {get_safe_pressure_unit(inputs)}
Outlet Pressure: {inputs.get('p2', 'N/A')} {get_safe_pressure_unit(inputs)}
Temperature: {inputs.get('t1', 'N/A')} {get_safe_temp_unit(inputs)}

SIZING RESULTS:
Required Cv: {results.get('cv', 'N/A')}
Rated Cv: {results.get('rated_cv', 'N/A')}

CAVITATION ANALYSIS:
Sigma Value: {results.get('cavitation_index', 'N/A')}
Status: {results.get('cavitation_status', 'N/A')}

NOISE ANALYSIS:
Noise Level: {results.get('total_noise_dba', 'N/A')} dBA

This report provides preliminary valve sizing results.
Final selection should be verified with manufacturer software.
"""
        
        # Clean all Unicode characters
        return clean_unicode_for_pdf(report_content)
        
    except Exception as e:
        print(f"Text report creation error: {e}")
        return f"""
VALVE SIZING REPORT
===================
Error creating detailed report: {e}
Please check your data and try again.
"""

# Fallback functions for ReportLab
def create_pdf_with_reportlab_unicode(report_data):
    """ReportLab version with Unicode handling"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Create simple PDF content with Unicode cleaning
        title = clean_unicode_for_pdf("CONTROL VALVE SIZING REPORT")
        story.append(Paragraph(title, styles['Title']))
        
        content = create_unicode_safe_text_report(report_data)
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
