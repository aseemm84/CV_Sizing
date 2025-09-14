"""
Enhanced Professional PDF Generator with Charts and Graphs
Generates comprehensive reports with visual analysis
"""
from datetime import datetime
import io
import os
import tempfile
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

def create_pdf_report(report_data):
    """
    Create comprehensive PDF report with charts and graphs
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"valve_sizing_report_{timestamp}.pdf"
    
    # Generate charts first
    chart_files = generate_charts_for_report(report_data)
    
    # Try fpdf2 first (recommended)
    try:
        pdf_bytes = create_comprehensive_pdf_with_charts(report_data, chart_files)
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

Please install required libraries:
pip install fpdf2 matplotlib numpy
        """
        return filename.replace('.pdf', '_error.txt'), basic_content.encode('utf-8')
    finally:
        # Clean up temporary chart files
        cleanup_chart_files(chart_files)

def generate_charts_for_report(report_data):
    """Generate all charts for the report"""
    chart_files = {}
    
    try:
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
        
        # Chart 6: Flow Regime Analysis (for gas)
        if inputs.get('fluid_type') == 'Gas/Vapor' and 'flow_regime' in results:
            chart_files['flow_regime'] = create_gas_flow_analysis_chart(results)
        
        # Chart 7: Safety Factor Analysis
        if 'safety_factor_rec' in inputs:
            chart_files['safety_factors'] = create_safety_factor_chart(inputs['safety_factor_rec'])
        
    except Exception as e:
        print(f"Chart generation error: {e}")
    
    return chart_files

def create_valve_opening_chart(validation_data):
    """Create valve opening validation chart"""
    try:
        scenarios = []
        openings = []
        colors = []
        
        scenario_order = ['minimum', 'normal', 'design', 'maximum', 'emergency']
        
        for scenario in scenario_order:
            if scenario in validation_data:
                result = validation_data[scenario]
                scenarios.append(scenario.replace('_', ' ').title())
                openings.append(result.get('opening_percent', 0))
                
                # Color based on status
                status = result.get('status', 'Unknown')
                if status == 'Acceptable':
                    colors.append('#2E8B57')  # Sea Green
                elif status == 'Oversized':
                    colors.append('#FFA500')  # Orange
                else:
                    colors.append('#DC143C')  # Crimson
        
        if not scenarios:
            return None
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(scenarios, openings, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
        
        # Add optimal range shading
        plt.axhspan(20, 80, alpha=0.2, color='green', label='Optimal Range (20-80%)')
        
        # Add value labels on bars
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
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='valve_opening_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Valve opening chart error: {e}")
        return None

def create_cavitation_analysis_chart(sigma_data, inputs):
    """Create ISA RP75.23 cavitation analysis chart"""
    try:
        valve_type = inputs.get('valve_type', 'Globe')
        valve_style = inputs.get('valve_style', 'Standard')
        
        # Define sigma limits based on valve type
        if 'Anti-Cavitation' in valve_style or 'Low-Noise' in valve_style:
            sigma_limits = {'sigma_i': 4.0, 'sigma_c': 3.0, 'sigma_d': 2.5, 'sigma_ch': 2.0, 'sigma_mv': 1.5}
        elif valve_type == 'Ball':
            sigma_limits = {'sigma_i': 2.5, 'sigma_c': 1.8, 'sigma_d': 1.3, 'sigma_ch': 0.9, 'sigma_mv': 0.7}
        else:  # Standard Globe
            sigma_limits = {'sigma_i': 3.0, 'sigma_c': 2.0, 'sigma_d': 1.5, 'sigma_ch': 1.0, 'sigma_mv': 0.8}
        
        # Prepare data
        levels = ['No Cavitation', 'Incipient', 'Constant', 'Incip. Damage', 'Choking', 'Max Vibration']
        sigma_values = [sigma_limits['sigma_i'], sigma_limits['sigma_c'], sigma_limits['sigma_d'], 
                       sigma_limits['sigma_ch'], sigma_limits['sigma_mv'], 0]
        colors = ['#2E8B57', '#32CD32', '#FFD700', '#FFA500', '#FF6347', '#DC143C']
        
        current_sigma = sigma_data.get('sigma', 2.0)
        
        plt.figure(figsize=(12, 8))
        
        # Create horizontal bar chart
        y_pos = np.arange(len(levels))
        bars = plt.barh(y_pos, sigma_values, color=colors, alpha=0.7, edgecolor='black')
        
        # Add current operating point
        plt.axvline(x=current_sigma, color='red', linestyle='--', linewidth=3, 
                   label=f'Operating Point: σ = {current_sigma:.3f}')
        
        # Add text labels
        for i, (bar, sigma_val) in enumerate(zip(bars, sigma_values)):
            if sigma_val > 0:
                plt.text(sigma_val + 0.1, bar.get_y() + bar.get_height()/2, 
                        f'σ >= {sigma_val:.1f}', ha='left', va='center', fontweight='bold')
        
        plt.yticks(y_pos, levels)
        plt.xlabel('Sigma Value (σ)', fontsize=12)
        plt.ylabel('Cavitation Level', fontsize=12)
        plt.title(f'ISA RP75.23 Cavitation Analysis - {valve_type} Valve\n{valve_style}', 
                 fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')
        plt.legend()
        
        # Add risk assessment text
        risk = sigma_data.get('risk', 'Medium')
        risk_color = {'Low': 'green', 'Medium': 'orange', 'High': 'red', 'Critical': 'darkred'}.get(risk, 'black')
        plt.text(0.02, 0.98, f'Risk Assessment: {risk}', transform=plt.gca().transAxes, 
                fontsize=12, fontweight='bold', color=risk_color, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='cavitation_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Cavitation chart error: {e}")
        return None

def create_valve_characteristic_chart(valve_type, valve_char, operating_opening):
    """Create valve flow characteristic curve"""
    try:
        # Generate opening percentages
        openings = np.linspace(10, 100, 91)
        
        # Calculate flow coefficients based on characteristic
        if valve_char == 'Linear':
            flows = openings / 100
        elif valve_char == 'Quick Opening':
            flows = np.sqrt(openings / 100)
        else:  # Equal Percentage or Modified Equal Percentage
            flows = (50**(openings/100 - 1))  # R=50 for equal percentage
        
        # Normalize to 0-100%
        flows = (flows / np.max(flows)) * 100
        
        plt.figure(figsize=(10, 8))
        
        # Plot characteristic curve
        plt.plot(openings, flows, 'b-', linewidth=3, label=f'{valve_char} Characteristic')
        
        # Add operating point
        if 10 <= operating_opening <= 100:
            if valve_char == 'Linear':
                operating_flow = operating_opening
            elif valve_char == 'Quick Opening':
                operating_flow = np.sqrt(operating_opening / 100) * 100
            else:  # Equal Percentage
                operating_flow = (50**(operating_opening/100 - 1)) / (50**(1-1)) * 100
            
            plt.plot(operating_opening, operating_flow, 'ro', markersize=12, 
                    label=f'Operating Point ({operating_opening}%, {operating_flow:.1f}%)')
            
            # Add operating point lines
            plt.axvline(x=operating_opening, color='red', linestyle=':', alpha=0.7)
            plt.axhline(y=operating_flow, color='red', linestyle=':', alpha=0.7)
        
        # Add optimal operating range
        plt.axvspan(20, 80, alpha=0.2, color='green', label='Optimal Operating Range')
        
        # Add ideal linear line for reference
        plt.plot([0, 100], [0, 100], 'k--', alpha=0.5, label='Linear Reference')
        
        plt.xlabel('Valve Opening (%)', fontsize=12)
        plt.ylabel('Flow Rate (% of Maximum)', fontsize=12)
        plt.title(f'{valve_type} Valve Flow Characteristic\n{valve_char} Curve', 
                 fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.xlim(0, 100)
        plt.ylim(0, 100)
        
        # Add rangeability information
        plt.text(0.02, 0.98, f'Valve Type: {valve_type}', transform=plt.gca().transAxes, 
                fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='characteristic_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Characteristic chart error: {e}")
        return None

def create_pressure_distribution_chart(p1, p2, pv, fluid_type):
    """Create pressure distribution analysis chart"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Create pressure distribution
        pressures = [p1, p2, pv] if fluid_type == 'Liquid' else [p1, p2]
        labels = ['Inlet (P1)', 'Outlet (P2)', 'Vapor (Pv)'] if fluid_type == 'Liquid' else ['Inlet (P1)', 'Outlet (P2)']
        colors = ['#4472C4', '#E70000', '#70AD47'] if fluid_type == 'Liquid' else ['#4472C4', '#E70000']
        
        # Bar chart
        bars = plt.bar(labels, pressures, color=colors, alpha=0.7, edgecolor='black')
        
        # Add value labels
        for bar, pressure in zip(bars, pressures):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + max(pressures)*0.01,
                    f'{pressure:.2f} bar', ha='center', va='bottom', fontweight='bold')
        
        # Add differential pressure
        dp = p1 - p2
        plt.text(0.5, max(pressures) * 0.8, f'ΔP = {dp:.2f} bar', 
                ha='center', transform=plt.gca().transData,
                bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', alpha=0.8),
                fontsize=12, fontweight='bold')
        
        # Add pressure ratio for liquids
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
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='pressure_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Pressure chart error: {e}")
        return None

def create_noise_assessment_chart(noise_level):
    """Create noise level assessment chart"""
    try:
        # Define noise level ranges
        ranges = ['Acceptable\n<85 dBA', 'Moderate\n85-100 dBA', 'High\n100-110 dBA', 'Extreme\n>110 dBA']
        levels = [85, 100, 110, 130]  # Upper limits for visualization
        colors = ['#2E8B57', '#FFD700', '#FFA500', '#DC143C']
        
        plt.figure(figsize=(10, 6))
        
        # Create horizontal bar chart showing ranges
        y_pos = np.arange(len(ranges))
        bars = plt.barh(y_pos, levels, color=colors, alpha=0.7, edgecolor='black')
        
        # Add current noise level line
        plt.axvline(x=noise_level, color='red', linestyle='-', linewidth=4, 
                   label=f'Predicted Level: {noise_level:.1f} dBA')
        
        # Determine current level category
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
        
        # Add assessment text
        plt.text(0.02, 0.98, f'Assessment: {category}', transform=plt.gca().transAxes, 
                fontsize=14, fontweight='bold', color=category_color,
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Add recommendations
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
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='noise_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Noise chart error: {e}")
        return None

def create_gas_flow_analysis_chart(results):
    """Create gas flow analysis chart"""
    try:
        # Extract gas flow parameters
        mach_number = results.get('mach_number', 0)
        expansion_factor = results.get('expansion_factor_y', 1)
        pressure_ratio = results.get('pressure_drop_ratio_x', 0)
        flow_regime = results.get('flow_regime', 'Subsonic')
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Chart 1: Mach Number
        mach_categories = ['Subsonic\n<0.3', 'Transonic\n0.3-0.8', 'Sonic\n0.8-1.0', 'Supersonic\n>1.0']
        mach_limits = [0.3, 0.8, 1.0, 2.0]
        mach_colors = ['green', 'yellow', 'orange', 'red']
        
        bars1 = ax1.bar(mach_categories, mach_limits, color=mach_colors, alpha=0.7)
        ax1.axhline(y=mach_number, color='blue', linewidth=3, label=f'Current: {mach_number:.3f}')
        ax1.set_ylabel('Mach Number')
        ax1.set_title('Mach Number Analysis')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Expansion Factor
        openings = np.linspace(10, 100, 10)
        y_factors = [expansion_factor] * len(openings)  # Simplified
        ax2.plot(openings, y_factors, 'b-', linewidth=2, marker='o')
        ax2.set_xlabel('Valve Opening (%)')
        ax2.set_ylabel('Expansion Factor (Y)')
        ax2.set_title(f'Expansion Factor: {expansion_factor:.4f}')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 1)
        
        # Chart 3: Pressure Ratio
        critical_ratio = 0.53  # Typical for air
        ax3.pie([pressure_ratio, 1-pressure_ratio], labels=['Pressure Drop', 'Recovered Pressure'], 
               autopct='%1.1f%%', startangle=90)
        ax3.set_title(f'Pressure Drop Ratio (x): {pressure_ratio:.3f}')
        
        # Chart 4: Flow Regime Status
        regimes = ['Subsonic', 'Choked']
        regime_status = [1, 0] if flow_regime == 'Subsonic' else [0, 1]
        colors = ['green', 'red']
        ax4.bar(regimes, regime_status, color=colors, alpha=0.7)
        ax4.set_ylabel('Status')
        ax4.set_title(f'Current Regime: {flow_regime}')
        ax4.set_ylim(0, 1.2)
        
        plt.tight_layout()
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='gas_flow_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Gas flow chart error: {e}")
        return None

def create_safety_factor_chart(safety_factor_data):
    """Create safety factor breakdown chart"""
    try:
        # Extract safety factor components
        base_factor = 1.1
        service_factor = safety_factor_data.get('service_factor', 0.0)
        criticality_factor = safety_factor_data.get('criticality_factor', 0.1)
        expansion_factor = safety_factor_data.get('expansion_factor', 0.0)
        total_factor = safety_factor_data.get('recommended_factor', 1.5)
        
        # Create stacked bar chart
        components = ['Base\nSafety', 'Service\nType', 'Criticality\nLevel', 'Future\nExpansion']
        values = [base_factor, service_factor, criticality_factor, expansion_factor]
        colors = ['#4472C4', '#E70000', '#70AD47', '#FFC000']
        
        plt.figure(figsize=(10, 6))
        
        # Create stacked bar
        bottom = 0
        for i, (component, value, color) in enumerate(zip(components, values, colors)):
            if value > 0:
                plt.bar(0, value, bottom=bottom, color=color, label=f'{component}: +{value:.1f}', 
                       width=0.5, edgecolor='black')
                # Add value label
                plt.text(0, bottom + value/2, f'+{value:.1f}', ha='center', va='center', 
                        fontweight='bold', color='white' if value > 0.2 else 'black')
                bottom += value
        
        # Add total line
        plt.axhline(y=total_factor, color='red', linestyle='--', linewidth=2, 
                   label=f'Total Factor: {total_factor:.1f}')
        
        # Add category assessment
        if total_factor <= 1.25:
            category = "Standard"
            cat_color = 'green'
        elif total_factor <= 1.5:
            category = "Moderate" 
            cat_color = 'orange'
        else:
            category = "Conservative"
            cat_color = 'red'
        
        plt.text(0.6, total_factor, f'{category}\nApproach', ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor=cat_color, alpha=0.3),
                fontsize=12, fontweight='bold')
        
        plt.ylabel('Safety Factor', fontsize=12)
        plt.title('Safety Factor Breakdown Analysis', fontsize=14, fontweight='bold')
        plt.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
        plt.grid(True, alpha=0.3, axis='y')
        plt.xlim(-0.5, 1.5)
        plt.ylim(0, total_factor * 1.2)
        plt.xticks([])  # Remove x-axis ticks
        
        plt.tight_layout()
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', prefix='safety_factor_')
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"Safety factor chart error: {e}")
        return None

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

def create_comprehensive_pdf_with_charts(report_data, chart_files):
    """Create comprehensive professional PDF with embedded charts"""
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
                    
                    # Calculate height maintaining aspect ratio if not provided
                    if height is None:
                        height = width * 0.75  # 4:3 aspect ratio
                    
                    # Center the image
                    x_pos = (self.w - width) / 2
                    
                    self.image(chart_file, x=x_pos, w=width, h=height)
                    self.ln(5)
                except Exception as e:
                    print(f"Chart insertion error: {e}")
                    self.safe_cell(0, 10, f"Chart unavailable: {title}", 1, 1, 'C')
            else:
                print(f"Chart file not found: {chart_file}")
                self.safe_cell(0, 10, f"Chart unavailable: {title}", 1, 1, 'C')

    pdf = ProfessionalValvePDFWithCharts()
    pdf.add_page()
    
    try:
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Report Header Information
        pdf.set_font('Arial', '', 11)
        pdf.safe_cell(0, 6, f"Generated: {report_data.get('report_date', 'Unknown')}", 0, 1)
        pdf.safe_cell(0, 6, f"Software: Enhanced Valve Sizing Application v2.0", 0, 1)
        pdf.safe_cell(0, 6, f"Analysis: Professional Engineering with Visual Charts", 0, 1)
        
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
        
        # Quick status summary
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

        # CHART 1: Valve Opening Validation
        if 'valve_opening' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['valve_opening'], 
                         'Figure 1: Valve Opening Validation Across Flow Scenarios')

        # CHART 2: Cavitation Analysis  
        if 'cavitation' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['cavitation'], 
                         'Figure 2: ISA RP75.23 Cavitation Analysis')

        # CHART 3: Valve Characteristic
        if 'characteristic' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['characteristic'], 
                         'Figure 3: Valve Flow Characteristic Curve')

        # CHART 4: Pressure Distribution
        if 'pressure_distribution' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['pressure_distribution'], 
                         'Figure 4: Pressure Distribution Analysis')

        # Add detailed text sections after charts
        pdf.add_page()
        
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

        # CHART 5: Noise Assessment
        if 'noise_assessment' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['noise_assessment'], 
                         'Figure 5: Noise Level Assessment')

        # CHART 6: Gas Flow Analysis (if applicable)
        if 'flow_regime' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['flow_regime'], 
                         'Figure 6: Gas Flow Analysis')

        # CHART 7: Safety Factor Analysis
        if 'safety_factors' in chart_files:
            pdf.add_page()
            pdf.add_chart(chart_files['safety_factors'], 
                         'Figure 7: Safety Factor Breakdown')

        # Continue with remaining sections...
        pdf.add_page()
        
        # CAVITATION ANALYSIS
        pdf.section_header('CAVITATION ANALYSIS (ISA RP75.23)')
        
        if 'sigma_analysis' in results:
            sigma_data = results['sigma_analysis']
            
            sigma_val = sigma_data.get('sigma', 'N/A')
            if isinstance(sigma_val, (int, float)):
                pdf.add_key_value_pair("Sigma Value", f"{sigma_val:.3f}")
            
            pdf.add_key_value_pair("Cavitation Level", sigma_data.get('level', 'N/A'))
            pdf.add_key_value_pair("Risk Assessment", sigma_data.get('risk', 'N/A'))
            pdf.add_key_value_pair("Status", sigma_data.get('status', 'N/A'))
            
            recommendation = clean_unicode_for_pdf(str(sigma_data.get('recommendation', 'N/A')))
            pdf.ln(2)
            pdf.set_font('Arial', 'B', 10)
            pdf.safe_cell(0, 6, "Trim Recommendation:", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.safe_multi_cell(0, 5, recommendation)

        # NOISE ANALYSIS
        pdf.section_header('NOISE ANALYSIS')
        
        if isinstance(noise_level, (int, float)):
            pdf.add_key_value_pair("Predicted Noise Level", f"{noise_level:.1f} dBA (at 1m distance)")
        
        pdf.add_key_value_pair("Prediction Method", results.get('method', 'Standard Calculation'))
        
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
            torque_val = results.get('required_torque', 0)
            if isinstance(torque_val, (int, float)):
                torque_unit = get_safe_torque_unit(inputs)
                pdf.add_key_value_pair("Required Torque", f"{torque_val:.0f} {torque_unit}")
        
        safety_factor = results.get('safety_factor_used', 1.5)
        if isinstance(safety_factor, (int, float)):
            pdf.add_key_value_pair("Safety Factor Applied", f"{safety_factor:.1f}")
        
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
            "4. Charts and graphs are based on calculated data and industry-standard methodologies.",
            "5. Material selections are based on general service conditions and must be verified for specific applications.",
            "6. Noise predictions are estimates - actual levels may vary based on installation conditions.",
            "7. Visual analysis aids understanding but does not replace detailed engineering review."
        ]
        
        for disclaimer in disclaimers:
            pdf.safe_multi_cell(0, 5, disclaimer)
            pdf.ln(1)
        
        pdf.ln(5)
        
        pdf.set_font('Arial', 'I', 9)
        footer_text = ("This enhanced report includes visual analysis charts to support engineering decisions. "
                      "All charts are generated from calculated data following industry standards. "
                      "Professional engineering review is recommended for critical applications.")
        pdf.safe_multi_cell(0, 4, footer_text)
        
        return bytes(pdf.output(dest='S'), 'latin1')
        
    except Exception as e:
        print(f"PDF with charts generation error: {e}")
        raise e

# Include all the helper functions from the previous version
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

[Note: Full report includes 7 engineering charts for visual analysis]

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

VISUAL ANALYSIS INCLUDED:
========================
- Figure 1: Valve Opening Validation Chart
- Figure 2: ISA RP75.23 Cavitation Analysis
- Figure 3: Valve Flow Characteristic Curve  
- Figure 4: Pressure Distribution Analysis
- Figure 5: Noise Level Assessment
- Figure 6: Gas Flow Analysis (if applicable)
- Figure 7: Safety Factor Breakdown

This report provides preliminary valve sizing results with comprehensive visual analysis.
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
        from reportlab.platypus import SimpleDocDocument, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        buffer = io.BytesIO()
        doc = SimpleDocDocument(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        title = clean_unicode_for_pdf("CONTROL VALVE SIZING REPORT WITH CHARTS")
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
