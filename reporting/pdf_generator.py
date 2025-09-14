"""
Fixed Professional PDF Generator with Charts - Robust Version
Addresses dependency issues and ensures PDF generation works
"""
from datetime import datetime
import io
import os
import tempfile

def create_pdf_report(report_data):
    """
    Create comprehensive PDF report with charts and graphs
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"valve_sizing_report_{timestamp}.pdf"
    
    # Check dependencies first
    dependencies_ok = check_dependencies()
    
    if dependencies_ok:
        # Generate charts first
        chart_files = generate_charts_for_report(report_data)
        
        # Try fpdf2 with charts
        try:
            pdf_bytes = create_comprehensive_pdf_with_charts(report_data, chart_files)
            cleanup_chart_files(chart_files)
            return filename, pdf_bytes
        except Exception as e:
            print(f"fpdf2 with charts error: {e}")
            cleanup_chart_files(chart_files)
    
    # Fallback to PDF without charts
    try:
        pdf_bytes = create_pdf_without_charts(report_data)
        return filename, pdf_bytes
    except ImportError:
        print("fpdf2 not available, trying ReportLab...")
    except Exception as e:
        print(f"fpdf2 error: {e}, trying ReportLab...")
        
    # ReportLab fallback
    try:
        pdf_bytes = create_pdf_with_reportlab_unicode(report_data)
        return filename, pdf_bytes
    except ImportError:
        print("ReportLab not available, creating text report...")
    except Exception as e:
        print(f"ReportLab error: {e}, creating text report...")
        
    # Text fallback only as last resort
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

Please install: pip install fpdf2
        """
        return filename.replace('.pdf', '_error.txt'), basic_content.encode('utf-8')

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        from fpdf import FPDF
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

def create_pdf_without_charts(report_data):
    """Create comprehensive PDF without charts as fallback"""
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
            self.set_fill_color(230, 230, 230)
            self.safe_cell(0, 8, title, 0, 1, 'L', True)
            self.set_fill_color(255, 255, 255)
            self.set_font('Arial', '', 10)
            self.ln(2)
        
        def add_key_value_pair(self, key, value, indent=0):
            self.safe_cell(indent, 6, '', 0, 0)
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
        pdf.safe_cell(0, 6, f"Analysis: Professional Engineering Analysis", 0, 1)
        
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
        
        pdf.set_font('Arial', 'B', 12)
        pdf.safe_cell(0, 8, f"Required Cv: {cv_text}", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Status assessment
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
        
        cavitation_risk = results.get('sigma_analysis', {}).get('risk', 'Unknown')
        if cavitation_risk == 'Unknown':
            cavitation_risk = 'Low' if results.get('cavitation_index', 2) > 2 else 'Medium'
        pdf.add_key_value_pair("Cavitation Risk", cavitation_risk)
        
        noise_level = results.get('total_noise_dba', 0)
        if isinstance(noise_level, (int, float)):
            noise_status = "ACCEPTABLE" if noise_level < 85 else "HIGH" if noise_level < 110 else "EXTREME"
            pdf.add_key_value_pair("Noise Level", f"{noise_level:.1f} dBA ({noise_status})")

        # PROCESS CONDITIONS
        pdf.section_header('PROCESS CONDITIONS')
        
        pdf.add_key_value_pair("Fluid Type", inputs.get('fluid_type', 'N/A'))
        pdf.add_key_value_pair("Fluid Name", inputs.get('fluid_name', 'N/A'))
        pdf.add_key_value_pair("Service Criticality", inputs.get('service_criticality', 'N/A'))
        
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

        # SIZING RESULTS
        pdf.section_header('SIZING RESULTS & ANALYSIS')
        
        pdf.set_font('Arial', 'B', 12)
        pdf.safe_cell(0, 8, f"Required Flow Coefficient (Cv): {cv_text}", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        if 'reynolds_factor' in results:
            rf = results['reynolds_factor']
            if isinstance(rf, (int, float)):
                pdf.add_key_value_pair("Reynolds Correction Factor (FR)", f"{rf:.4f}")
        
        if 'ff_factor' in results:
            ff = results['ff_factor']
            if isinstance(ff, (int, float)):
                pdf.add_key_value_pair("FF Factor (Liquid Critical Ratio)", f"{ff:.4f}")
        
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
                    status_symbol = "OK" if status == "Acceptable" else "WARN" if status == "Oversized" else "ERROR"
                    scenario_name = scenario.replace('_', ' ').title()
                    pdf.add_key_value_pair(f"{scenario_name} Flow", f"{opening_pct:.1f}% ({status}) [{status_symbol}]", 10)

        # Start new page for additional analysis
        pdf.add_page()

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
            
            recommendation = clean_unicode_for_pdf(str(sigma_data.get('recommendation', 'N/A')))
            pdf.ln(2)
            pdf.set_font('Arial', 'B', 10)
            pdf.safe_cell(0, 6, "Trim Recommendation:", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.safe_multi_cell(0, 5, recommendation)
        else:
            sigma_val = results.get('cavitation_index', 'N/A')
            if isinstance(sigma_val, (int, float)):
                pdf.add_key_value_pair("Sigma Value", f"{sigma_val:.3f}")
            else:
                pdf.add_key_value_pair("Sigma Value", str(sigma_val))
            
            pdf.add_key_value_pair("Status", results.get('cavitation_status', 'N/A'))
            pdf.add_key_value_pair("Flashing Occurrence", 'Yes' if results.get('is_flashing', False) else 'No')

        # NOISE ANALYSIS
        pdf.section_header('NOISE ANALYSIS')
        
        if isinstance(noise_level, (int, float)):
            pdf.add_key_value_pair("Predicted Noise Level", f"{noise_level:.1f} dBA (at 1m distance)")
        else:
            pdf.add_key_value_pair("Predicted Noise Level", f"{noise_level} dBA")
        
        pdf.add_key_value_pair("Prediction Method", results.get('method', 'Standard Calculation'))
        
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
        
        actuator_rec = results.get('actuator_recommendation', 'Consult manufacturer')
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 10)
        pdf.safe_cell(0, 6, "Actuator Recommendation:", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.safe_multi_cell(0, 5, clean_unicode_for_pdf(actuator_rec))

        # MATERIAL SELECTION
        if 'recommendations' in results:
            pdf.section_header('MATERIAL SELECTION')
            
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
        
        pdf.set_font('Arial', 'I', 9)
        footer_text = ("This report demonstrates compliance with industry standards including ISA S75.01, "
                      "ISA RP75.23, IEC 60534-8-3, and related engineering practices. "
                      "Professional engineering review is recommended for critical applications.")
        pdf.safe_multi_cell(0, 4, footer_text)
        
        return bytes(pdf.output(dest='S'), 'latin1')
        
    except Exception as e:
        print(f"Comprehensive PDF generation error: {e}")
        raise e

def generate_charts_for_report(report_data):
    """Generate all charts for the report - with error handling"""
    chart_files = {}
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Chart 1: Valve Opening Validation Chart
        if 'rangeability_validation' in results:
            chart_files['valve_opening'] = create_valve_opening_chart(results['rangeability_validation'])
        
        # Chart 2: Cavitation Analysis Chart
        if 'sigma_analysis' in results:
            chart_files['cavitation'] = create_cavitation_analysis_chart(results['sigma_analysis'], inputs)
        
        # Chart 3: Valve Characteristic Curve
        valve_type = inputs.get('valve_type', 'Globe')
        valve_char = inputs.get('valve_char', 'Equal Percentage')
        operating_opening = inputs.get('valve_opening_percent', 70)
        chart_files['characteristic'] = create_valve_characteristic_chart(valve_type, valve_char, operating_opening)
        
        # Chart 4: Pressure Drop Distribution
        p1 = inputs.get('p1', 10)
        p2 = inputs.get('p2', 5)
        pv = inputs.get('pv', 0.03)
        if isinstance(p1, (int, float)) and isinstance(p2, (int, float)):
            chart_files['pressure_distribution'] = create_pressure_distribution_chart(p1, p2, pv, inputs.get('fluid_type', 'Liquid'))
        
        # Chart 5: Noise Level Assessment
        noise_level = results.get('total_noise_dba', 0)
        if isinstance(noise_level, (int, float)) and noise_level > 0:
            chart_files['noise_assessment'] = create_noise_assessment_chart(noise_level)
        
    except Exception as e:
        print(f"Chart generation error: {e}")
    
    return chart_files

def create_valve_opening_chart(validation_data):
    """Create valve opening validation chart - simplified"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        scenarios = []
        openings = []
        colors = []
        
        scenario_order = ['minimum', 'normal', 'design', 'maximum', 'emergency']
        
        for scenario in scenario_order:
            if scenario in validation_data:
                result = validation_data[scenario]
                scenarios.append(scenario.replace('_', ' ').title())
                openings.append(result.get('opening_percent', 0))
                
                status = result.get('status', 'Unknown')
                if status == 'Acceptable':
                    colors.append('#2E8B57')
                elif status == 'Oversized':
                    colors.append('#FFA500')
                else:
                    colors.append('#DC143C')
        
        if not scenarios:
            return None
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(scenarios, openings, color=colors, alpha=0.7, edgecolor='black')
        
        plt.axhspan(20, 80, alpha=0.2, color='green', label='Optimal Range (20-80%)')
        
        for bar, opening in zip(bars, openings):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{opening:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.title('Valve Opening Validation Across Flow Scenarios', fontsize=14, fontweight='bold')
        plt.xlabel('Flow Scenario', fontsize=12)
        plt.ylabel('Valve Opening (%)', fontsize=12)
        plt.ylim(0, 105)
        plt.grid(True, alpha=0.3, axis='y')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='valve_opening_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Valve opening chart error: {e}")
        return None

def create_cavitation_analysis_chart(sigma_data, inputs):
    """Create cavitation analysis chart - simplified"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        valve_type = inputs.get('valve_type', 'Globe')
        valve_style = inputs.get('valve_style', 'Standard')
        
        if 'Anti-Cavitation' in valve_style or 'Low-Noise' in valve_style:
            sigma_limits = {'sigma_i': 4.0, 'sigma_c': 3.0, 'sigma_d': 2.5, 'sigma_ch': 2.0, 'sigma_mv': 1.5}
        elif valve_type == 'Ball':
            sigma_limits = {'sigma_i': 2.5, 'sigma_c': 1.8, 'sigma_d': 1.3, 'sigma_ch': 0.9, 'sigma_mv': 0.7}
        else:
            sigma_limits = {'sigma_i': 3.0, 'sigma_c': 2.0, 'sigma_d': 1.5, 'sigma_ch': 1.0, 'sigma_mv': 0.8}
        
        levels = ['No Cavitation', 'Incipient', 'Constant', 'Incip. Damage', 'Choking', 'Max Vibration']
        sigma_values = [sigma_limits['sigma_i'], sigma_limits['sigma_c'], sigma_limits['sigma_d'], 
                       sigma_limits['sigma_ch'], sigma_limits['sigma_mv'], 0]
        colors = ['#2E8B57', '#32CD32', '#FFD700', '#FFA500', '#FF6347', '#DC143C']
        
        current_sigma = sigma_data.get('sigma', 2.0)
        
        plt.figure(figsize=(12, 8))
        
        y_pos = np.arange(len(levels))
        bars = plt.barh(y_pos, sigma_values, color=colors, alpha=0.7, edgecolor='black')
        
        plt.axvline(x=current_sigma, color='red', linestyle='--', linewidth=3,
                   label=f'Operating Point: sigma = {current_sigma:.3f}')
        
        for i, (bar, sigma_val) in enumerate(zip(bars, sigma_values)):
            if sigma_val > 0:
                plt.text(sigma_val + 0.1, bar.get_y() + bar.get_height()/2, 
                        f'sigma >= {sigma_val:.1f}', ha='left', va='center', fontweight='bold')
        
        plt.yticks(y_pos, levels)
        plt.xlabel('Sigma Value', fontsize=12)
        plt.ylabel('Cavitation Level', fontsize=12)
        plt.title(f'ISA RP75.23 Cavitation Analysis - {valve_type} Valve\n{valve_style}', 
                 fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')
        plt.legend()
        
        risk = sigma_data.get('risk', 'Medium')
        risk_color = {'Low': 'green', 'Medium': 'orange', 'High': 'red', 'Critical': 'darkred'}.get(risk, 'black')
        plt.text(0.02, 0.98, f'Risk Assessment: {risk}', transform=plt.gca().transAxes, 
                fontsize=12, fontweight='bold', color=risk_color, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='cavitation_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Cavitation chart error: {e}")
        return None

def create_valve_characteristic_chart(valve_type, valve_char, operating_opening):
    """Create valve characteristic chart - simplified"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        openings = np.linspace(10, 100, 91)
        
        if valve_char == 'Linear':
            flows = openings / 100
        elif valve_char == 'Quick Opening':
            flows = np.sqrt(openings / 100)
        else:  # Equal Percentage
            flows = (50**(openings/100 - 1))
        
        flows = (flows / np.max(flows)) * 100
        
        plt.figure(figsize=(10, 8))
        
        plt.plot(openings, flows, 'b-', linewidth=3, label=f'{valve_char} Characteristic')
        
        if 10 <= operating_opening <= 100:
            if valve_char == 'Linear':
                operating_flow = operating_opening
            elif valve_char == 'Quick Opening':
                operating_flow = np.sqrt(operating_opening / 100) * 100
            else:
                operating_flow = (50**(operating_opening/100 - 1)) / (50**(1-1)) * 100
            
            plt.plot(operating_opening, operating_flow, 'ro', markersize=12, 
                    label=f'Operating Point ({operating_opening}%, {operating_flow:.1f}%)')
            
            plt.axvline(x=operating_opening, color='red', linestyle=':', alpha=0.7)
            plt.axhline(y=operating_flow, color='red', linestyle=':', alpha=0.7)
        
        plt.axvspan(20, 80, alpha=0.2, color='green', label='Optimal Operating Range')
        plt.plot([0, 100], [0, 100], 'k--', alpha=0.5, label='Linear Reference')
        
        plt.xlabel('Valve Opening (%)', fontsize=12)
        plt.ylabel('Flow Rate (% of Maximum)', fontsize=12)
        plt.title(f'{valve_type} Valve Flow Characteristic\n{valve_char} Curve', 
                 fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.xlim(0, 100)
        plt.ylim(0, 100)
        
        plt.text(0.02, 0.98, f'Valve Type: {valve_type}', transform=plt.gca().transAxes, 
                fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='characteristic_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Characteristic chart error: {e}")
        return None

def create_pressure_distribution_chart(p1, p2, pv, fluid_type):
    """Create pressure distribution chart - simplified"""
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(10, 6))
        
        pressures = [p1, p2, pv] if fluid_type == 'Liquid' else [p1, p2]
        labels = ['Inlet (P1)', 'Outlet (P2)', 'Vapor (Pv)'] if fluid_type == 'Liquid' else ['Inlet (P1)', 'Outlet (P2)']
        colors = ['#4472C4', '#E70000', '#70AD47'] if fluid_type == 'Liquid' else ['#4472C4', '#E70000']
        
        bars = plt.bar(labels, pressures, color=colors, alpha=0.7, edgecolor='black')
        
        for bar, pressure in zip(bars, pressures):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + max(pressures)*0.01,
                    f'{pressure:.2f} bar', ha='center', va='bottom', fontweight='bold')
        
        dp = p1 - p2
        plt.text(0.5, max(pressures) * 0.8, f'Delta P = {dp:.2f} bar', 
                ha='center', transform=plt.gca().transData,
                bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', alpha=0.8),
                fontsize=12, fontweight='bold')
        
        if fluid_type == 'Liquid' and pv > 0:
            pressure_ratio = (p1 - pv) / (p1 - p2)
            plt.text(0.02, 0.98, f'Pressure Ratio (P1-Pv)/(P1-P2): {pressure_ratio:.3f}', 
                    transform=plt.gca().transAxes, fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        plt.ylabel('Pressure (bar)', fontsize=12)
        plt.title(f'{fluid_type} Service - Pressure Distribution Analysis', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='y')
        plt.ylim(0, max(pressures) * 1.2)
        
        plt.tight_layout()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='pressure_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Pressure chart error: {e}")
        return None

def create_noise_assessment_chart(noise_level):
    """Create noise assessment chart - simplified"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        ranges = ['Acceptable\n<85 dBA', 'Moderate\n85-100 dBA', 'High\n100-110 dBA', 'Extreme\n>110 dBA']
        levels = [85, 100, 110, 130]
        colors = ['#2E8B57', '#FFD700', '#FFA500', '#DC143C']
        
        plt.figure(figsize=(10, 6))
        
        y_pos = np.arange(len(ranges))
        bars = plt.barh(y_pos, levels, color=colors, alpha=0.7, edgecolor='black')
        
        plt.axvline(x=noise_level, color='red', linestyle='-', linewidth=4, 
                   label=f'Predicted Level: {noise_level:.1f} dBA')
        
        if noise_level < 85:
            category = "ACCEPTABLE"
            category_color = 'green'
        elif noise_level < 100:
            category = "MODERATE"
            category_color = 'orange'
        elif noise_level < 110:
            category = "HIGH"
            category_color = 'red'
        else:
            category = "EXTREME"
            category_color = 'darkred'
        
        plt.yticks(y_pos, ranges)
        plt.xlabel('Noise Level (dBA)', fontsize=12)
        plt.ylabel('Assessment Category', fontsize=12)
        plt.title('Noise Level Assessment at 1 Meter Distance', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')
        plt.legend()
        plt.xlim(0, 130)
        
        plt.text(0.02, 0.98, f'Assessment: {category}', transform=plt.gca().transAxes, 
                fontsize=14, fontweight='bold', color=category_color,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        recommendations = {
            "ACCEPTABLE": "No special measures required",
            "MODERATE": "Consider noise reduction measures",
            "HIGH": "Noise reduction required",
            "EXTREME": "Immediate mitigation essential"
        }
        
        plt.text(0.02, 0.88, f'Recommendation: {recommendations[category]}', 
                transform=plt.gca().transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='noise_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Noise chart error: {e}")
        return None

def create_comprehensive_pdf_with_charts(report_data, chart_files):
    """Create comprehensive PDF with charts embedded"""
    from fpdf import FPDF
    
    class ProfessionalValvePDFWithCharts(FPDF):
        def header(self):
            try:
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, 'CONTROL VALVE SIZING REPORT', 0, 1, 'C')
                self.set_font('Arial', 'I', 10)
                self.cell(0, 6, 'Professional Engineering Analysis with Visual Charts', 0, 1, 'C')
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
            self.set_fill_color(230, 230, 230)
            self.safe_cell(0, 8, title, 0, 1, 'L', True)
            self.set_fill_color(255, 255, 255)
            self.set_font('Arial', '', 10)
            self.ln(2)
        
        def add_key_value_pair(self, key, value, indent=0):
            self.safe_cell(indent, 6, '', 0, 0)
            self.set_font('Arial', 'B', 10)
            self.safe_cell(80, 6, f"{key}:", 0, 0)
            self.set_font('Arial', '', 10)
            self.safe_cell(0, 6, str(value), 0, 1)
        
        def add_chart(self, chart_file, title, width=160, height=None):
            """Add chart to PDF with title"""
            if chart_file and os.path.exists(chart_file):
                try:
                    self.ln(5)
                    self.set_font('Arial', 'B', 12)
                    self.safe_cell(0, 8, title, 0, 1, 'C')
                    self.ln(3)
                    
                    if height is None:
                        height = width * 0.75
                    
                    x_pos = (self.w - width) / 2
                    self.image(chart_file, x=x_pos, w=width, h=height)
                    self.ln(5)
                except Exception as e:
                    print(f"Chart insertion error: {e}")
                    self.safe_cell(0, 10, f"Chart unavailable: {title}", 1, 1, 'C')
            else:
                print(f"Chart file not found: {chart_file}")
                self.safe_cell(0, 10, f"Chart unavailable: {title}", 1, 1, 'C')

    # Use the same comprehensive content as create_pdf_without_charts but add charts
    pdf = ProfessionalValvePDFWithCharts()
    pdf.add_page()
    
    try:
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Header info
        pdf.set_font('Arial', '', 11)
        pdf.safe_cell(0, 6, f"Generated: {report_data.get('report_date', 'Unknown')}", 0, 1)
        pdf.safe_cell(0, 6, f"Software: Enhanced Valve Sizing Application v2.0 with Charts", 0, 1)
        
        if 'standards_compliance' in report_data:
            standards = ', '.join(report_data['standards_compliance'])
            pdf.safe_cell(0, 6, f"Standards: {standards}", 0, 1)
        
        # Executive summary
        pdf.section_header('EXECUTIVE SUMMARY')
        
        cv_value = results.get('cv', 0)
        cv_text = f"{cv_value:.2f}" if isinstance(cv_value, (int, float)) else str(cv_value)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.safe_cell(0, 8, f"Required Cv: {cv_text}", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Add key charts on separate pages
        if 'valve_opening' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['valve_opening'], 'Figure 1: Valve Opening Validation')
        
        if 'cavitation' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['cavitation'], 'Figure 2: ISA RP75.23 Cavitation Analysis')
        
        if 'characteristic' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['characteristic'], 'Figure 3: Valve Flow Characteristic')
        
        if 'pressure_distribution' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['pressure_distribution'], 'Figure 4: Pressure Distribution')
        
        if 'noise_assessment' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['noise_assessment'], 'Figure 5: Noise Assessment')
        
        # Add detailed technical sections on final pages
        pdf.add_page()
        pdf.section_header('DETAILED TECHNICAL ANALYSIS')
        
        # Process conditions summary
        pdf.add_key_value_pair("Fluid Type", inputs.get('fluid_type', 'N/A'))
        pdf.add_key_value_pair("Required Cv", cv_text)
        pdf.add_key_value_pair("Rated Cv", str(results.get('rated_cv', 'N/A')))
        
        if isinstance(cv_value, (int, float)) and isinstance(results.get('rated_cv', 0), (int, float)) and results.get('rated_cv', 0) > 0:
            opening = (cv_value / results['rated_cv']) * 100
            pdf.add_key_value_pair("Valve Opening", f"{opening:.1f}%")
        
        # Cavitation summary
        if 'sigma_analysis' in results:
            sigma_data = results['sigma_analysis']
            pdf.add_key_value_pair("Sigma Value", f"{sigma_data.get('sigma', 'N/A'):.3f}")
            pdf.add_key_value_pair("Cavitation Risk", sigma_data.get('risk', 'N/A'))
        
        # Noise summary
        noise_level = results.get('total_noise_dba', 0)
        if isinstance(noise_level, (int, float)):
            pdf.add_key_value_pair("Noise Level", f"{noise_level:.1f} dBA")
        
        # Disclaimers
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 9)
        disclaimer = ("This enhanced report includes visual analysis charts generated from calculated data. "
                     "Professional engineering review is recommended for critical applications.")
        pdf.safe_multi_cell(0, 4, disclaimer)
        
        return bytes(pdf.output(dest='S'), 'latin1')
        
    except Exception as e:
        print(f"PDF with charts generation error: {e}")
        raise e

def cleanup_chart_files(chart_files):
    """Clean up temporary chart files"""
    for chart_file in chart_files.values():
        if chart_file and os.path.exists(chart_file):
            try:
                os.unlink(chart_file)
            except:
                pass

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

# Helper functions
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

def create_comprehensive_text_report(report_data):
    """Create comprehensive text report as fallback"""
    inputs = report_data.get('inputs', {})
    results = report_data.get('results', {})
    
    report = f"""
===============================
CONTROL VALVE SIZING REPORT
===============================
Generated: {report_data.get('report_date', 'Unknown')}
Software: Enhanced Valve Sizing Application v2.0 with Charts
Standards: {', '.join(report_data.get('standards_compliance', ['ISA S75.01', 'IEC 60534']))}

EXECUTIVE SUMMARY:
==================
Required Cv: {results.get('cv', 'N/A')}
Sizing Status: {'ACCEPTABLE' if results.get('rangeability_validation', {}).get('overall_valid', False) else 'UNDER REVIEW'}
Cavitation Risk: {results.get('sigma_analysis', {}).get('risk', 'Unknown')}
Noise Level: {results.get('total_noise_dba', 'N/A')} dBA

[Note: Charts are included when PDF generation is successful]

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

SIZING RESULTS:
===============
Required Cv: {results.get('cv', 'N/A')}
Reynolds Factor (FR): {results.get('reynolds_factor', 'N/A')}
FF Factor: {results.get('ff_factor', 'N/A')}
Rated Cv: {results.get('rated_cv', 'N/A')}
Rangeability: {results.get('inherent_rangeability', 'N/A')}:1

This report provides preliminary valve sizing results.
Final selection should be verified with manufacturer software.
Professional engineering review recommended for critical applications.
===============================
END OF REPORT
===============================
"""
    
    return clean_unicode_for_pdf(report)

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
