"""
ROBUST PDF Generator - Simplified and Error-Free Version
This version focuses on stability and eliminates PDF corruption issues
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
    ROBUST VERSION - Eliminates PDF corruption errors
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"valve_sizing_report_{timestamp}.pdf"
    
    # Generate charts first as byte streams
    chart_data = generate_charts_as_bytes(report_data)
    
    # Try fpdf2 with simplified approach first
    try:
        pdf_bytes = create_robust_pdf_with_charts(report_data, chart_data)
        return filename, pdf_bytes
    except ImportError:
        print("fpdf2 not available, trying alternative methods...")
    except Exception as e:
        print(f"fpdf2 error: {e}, trying alternative methods...")
    
    # Try basic PDF without complex formatting
    try:
        pdf_bytes = create_simple_pdf_report(report_data)
        return filename, pdf_bytes
    except Exception as e:
        print(f"Simple PDF error: {e}, creating minimal PDF...")
        # Ultimate fallback
        pdf_bytes = create_minimal_pdf_report(report_data)
        return filename.replace('.pdf', '_minimal.pdf'), pdf_bytes

def generate_charts_as_bytes(report_data):
    """Generate all charts as byte streams for embedding"""
    chart_data = {}
    
    try:
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Chart 1: Valve Opening Validation Chart
        if 'rangeability_validation' in results:
            chart_data['valve_opening'] = create_valve_opening_chart_bytes(results['rangeability_validation'])
        
        # Chart 2: Cavitation Analysis Chart
        if 'sigma_analysis' in results:
            chart_data['cavitation'] = create_cavitation_analysis_chart_bytes(results['sigma_analysis'], inputs)
        
        # Chart 3: Valve Characteristic Curve
        valve_type = inputs.get('valve_type', 'Globe')
        valve_char = inputs.get('valve_char', 'Equal Percentage')
        operating_opening = inputs.get('valve_opening_percent', 70)
        chart_data['characteristic'] = create_valve_characteristic_chart_bytes(valve_type, valve_char, operating_opening)
        
        # Chart 4: Pressure Drop Distribution
        p1 = inputs.get('p1', 10)
        p2 = inputs.get('p2', 5)
        pv = inputs.get('pv', 0.03)
        if isinstance(p1, (int, float)) and isinstance(p2, (int, float)):
            chart_data['pressure_distribution'] = create_pressure_distribution_chart_bytes(p1, p2, pv, inputs.get('fluid_type', 'Liquid'))
        
        # Chart 5: Noise Level Assessment
        noise_level = results.get('total_noise_dba', 0)
        if isinstance(noise_level, (int, float)) and noise_level > 0:
            chart_data['noise_assessment'] = create_noise_assessment_chart_bytes(noise_level)
        
        # Chart 6: Flow Regime Analysis (for gas)
        if inputs.get('fluid_type') == 'Gas/Vapor' and 'flow_regime' in results:
            chart_data['flow_regime'] = create_gas_flow_analysis_chart_bytes(results)
        
        # Chart 7: Safety Factor Analysis
        if 'safety_factor_rec' in inputs:
            chart_data['safety_factors'] = create_safety_factor_chart_bytes(inputs['safety_factor_rec'])
        
    except Exception as e:
        print(f"Chart generation error: {e}")
    
    return chart_data

def save_chart_to_bytes(fig):
    """Save matplotlib figure to bytes for PDF embedding"""
    img_buffer = io.BytesIO()
    try:
        fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        plt.close(fig)
        return img_buffer
    except Exception as e:
        print(f"Chart save error: {e}")
        plt.close(fig)
        return None

def create_valve_opening_chart_bytes(validation_data):
    """Create valve opening validation chart as bytes"""
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
                
                status = result.get('status', 'Unknown')
                if status == 'Acceptable':
                    colors.append('#2E8B57')
                elif status == 'Oversized':
                    colors.append('#FFA500')
                else:
                    colors.append('#DC143C')
        
        if not scenarios:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(scenarios, openings, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
        
        ax.axhspan(20, 80, alpha=0.2, color='green', label='Optimal Range (20-80%)')
        
        for bar, opening in zip(bars, openings):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{opening:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        ax.set_title('Valve Opening Validation Across Flow Scenarios', fontsize=14, fontweight='bold')
        ax.set_xlabel('Flow Scenario', fontsize=12)
        ax.set_ylabel('Valve Opening (%)', fontsize=12)
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        return save_chart_to_bytes(fig)
        
    except Exception as e:
        print(f"Valve opening chart error: {e}")
        return None

def create_cavitation_analysis_chart_bytes(sigma_data, inputs):
    """Create ISA RP75.23 cavitation analysis chart as bytes"""
    try:
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
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        y_pos = np.arange(len(levels))
        bars = ax.barh(y_pos, sigma_values, color=colors, alpha=0.7, edgecolor='black')
        
        ax.axvline(x=current_sigma, color='red', linestyle='--', linewidth=3, 
                  label=f'Operating Point: σ = {current_sigma:.3f}')
        
        for i, (bar, sigma_val) in enumerate(zip(bars, sigma_values)):
            if sigma_val > 0:
                ax.text(sigma_val + 0.1, bar.get_y() + bar.get_height()/2, 
                       f'σ >= {sigma_val:.1f}', ha='left', va='center', fontweight='bold')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(levels)
        ax.set_xlabel('Sigma Value (σ)', fontsize=12)
        ax.set_ylabel('Cavitation Level', fontsize=12)
        ax.set_title(f'ISA RP75.23 Cavitation Analysis - {valve_type} Valve\n{valve_style}', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.legend()
        
        risk = sigma_data.get('risk', 'Medium')
        risk_color = {'Low': 'green', 'Medium': 'orange', 'High': 'red', 'Critical': 'darkred'}.get(risk, 'black')
        ax.text(0.02, 0.98, f'Risk Assessment: {risk}', transform=ax.transAxes, 
               fontsize=12, fontweight='bold', color=risk_color, 
               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        return save_chart_to_bytes(fig)
        
    except Exception as e:
        print(f"Cavitation chart error: {e}")
        return None

def create_valve_characteristic_chart_bytes(valve_type, valve_char, operating_opening):
    """Create valve flow characteristic curve as bytes"""
    try:
        openings = np.linspace(10, 100, 91)
        
        if valve_char == 'Linear':
            flows = openings / 100
        elif valve_char == 'Quick Opening':
            flows = np.sqrt(openings / 100)
        else:
            flows = (50**(openings/100 - 1))
        
        flows = (flows / np.max(flows)) * 100
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        ax.plot(openings, flows, 'b-', linewidth=3, label=f'{valve_char} Characteristic')
        
        if 10 <= operating_opening <= 100:
            if valve_char == 'Linear':
                operating_flow = operating_opening
            elif valve_char == 'Quick Opening':
                operating_flow = np.sqrt(operating_opening / 100) * 100
            else:
                operating_flow = (50**(operating_opening/100 - 1)) / (50**(1-1)) * 100
            
            ax.plot(operating_opening, operating_flow, 'ro', markersize=12, 
                   label=f'Operating Point ({operating_opening}%, {operating_flow:.1f}%)')
            
            ax.axvline(x=operating_opening, color='red', linestyle=':', alpha=0.7)
            ax.axhline(y=operating_flow, color='red', linestyle=':', alpha=0.7)
        
        ax.axvspan(20, 80, alpha=0.2, color='green', label='Optimal Operating Range')
        ax.plot([0, 100], [0, 100], 'k--', alpha=0.5, label='Linear Reference')
        
        ax.set_xlabel('Valve Opening (%)', fontsize=12)
        ax.set_ylabel('Flow Rate (% of Maximum)', fontsize=12)
        ax.set_title(f'{valve_type} Valve Flow Characteristic\n{valve_char} Curve', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        
        ax.text(0.02, 0.98, f'Valve Type: {valve_type}', transform=ax.transAxes, 
               fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        return save_chart_to_bytes(fig)
        
    except Exception as e:
        print(f"Characteristic chart error: {e}")
        return None

def create_pressure_distribution_chart_bytes(p1, p2, pv, fluid_type):
    """Create pressure distribution analysis chart as bytes"""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        pressures = [p1, p2, pv] if fluid_type == 'Liquid' else [p1, p2]
        labels = ['Inlet (P1)', 'Outlet (P2)', 'Vapor (Pv)'] if fluid_type == 'Liquid' else ['Inlet (P1)', 'Outlet (P2)']
        colors = ['#4472C4', '#E70000', '#70AD47'] if fluid_type == 'Liquid' else ['#4472C4', '#E70000']
        
        bars = ax.bar(labels, pressures, color=colors, alpha=0.7, edgecolor='black')
        
        for bar, pressure in zip(bars, pressures):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(pressures)*0.01,
                   f'{pressure:.2f} bar', ha='center', va='bottom', fontweight='bold')
        
        dp = p1 - p2
        ax.text(0.5, max(pressures) * 0.8, f'ΔP = {dp:.2f} bar', 
               ha='center', transform=ax.transData,
               bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', alpha=0.8),
               fontsize=12, fontweight='bold')
        
        if fluid_type == 'Liquid' and pv > 0:
            pressure_ratio = (p1 - pv) / (p1 - p2)
            ax.text(0.02, 0.98, f'Pressure Ratio (P1-Pv)/(P1-P2): {pressure_ratio:.3f}', 
                   transform=ax.transAxes, fontsize=10,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        ax.set_ylabel('Pressure (bar)', fontsize=12)
        ax.set_title(f'{fluid_type} Service - Pressure Distribution Analysis', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, max(pressures) * 1.2)
        
        plt.tight_layout()
        return save_chart_to_bytes(fig)
        
    except Exception as e:
        print(f"Pressure chart error: {e}")
        return None

def create_noise_assessment_chart_bytes(noise_level):
    """Create noise level assessment chart as bytes"""
    try:
        ranges = ['Acceptable\n<85 dBA', 'Moderate\n85-100 dBA', 'High\n100-110 dBA', 'Extreme\n>110 dBA']
        levels = [85, 100, 110, 130]
        colors = ['#2E8B57', '#FFD700', '#FFA500', '#DC143C']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        y_pos = np.arange(len(ranges))
        bars = ax.barh(y_pos, levels, color=colors, alpha=0.7, edgecolor='black')
        
        ax.axvline(x=noise_level, color='red', linestyle='-', linewidth=4, 
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
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(ranges)
        ax.set_xlabel('Noise Level (dBA)', fontsize=12)
        ax.set_ylabel('Assessment Category', fontsize=12)
        ax.set_title('Noise Level Assessment at 1 Meter Distance', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.legend()
        ax.set_xlim(0, 130)
        
        ax.text(0.02, 0.98, f'Assessment: {category}', transform=ax.transAxes, 
               fontsize=14, fontweight='bold', color=category_color,
               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        recommendations = {
            "ACCEPTABLE": "No special measures required",
            "MODERATE": "Consider noise reduction measures",
            "HIGH": "Noise reduction required",
            "EXTREME": "Immediate mitigation essential"
        }
        
        ax.text(0.02, 0.88, f'Recommendation: {recommendations[category]}', 
               transform=ax.transAxes, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        return save_chart_to_bytes(fig)
        
    except Exception as e:
        print(f"Noise chart error: {e}")
        return None

def create_gas_flow_analysis_chart_bytes(results):
    """Create gas flow analysis chart as bytes"""
    try:
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
        y_factors = [expansion_factor] * len(openings)
        ax2.plot(openings, y_factors, 'b-', linewidth=2, marker='o')
        ax2.set_xlabel('Valve Opening (%)')
        ax2.set_ylabel('Expansion Factor (Y)')
        ax2.set_title(f'Expansion Factor: {expansion_factor:.4f}')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 1)
        
        # Chart 3: Pressure Ratio
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
        return save_chart_to_bytes(fig)
        
    except Exception as e:
        print(f"Gas flow chart error: {e}")
        return None

def create_safety_factor_chart_bytes(safety_factor_data):
    """Create safety factor breakdown chart as bytes"""
    try:
        base_factor = 1.1
        service_factor = safety_factor_data.get('service_factor', 0.0)
        criticality_factor = safety_factor_data.get('criticality_factor', 0.1)
        expansion_factor = safety_factor_data.get('expansion_factor', 0.0)
        total_factor = safety_factor_data.get('recommended_factor', 1.5)
        
        components = ['Base\nSafety', 'Service\nType', 'Criticality\nLevel', 'Future\nExpansion']
        values = [base_factor, service_factor, criticality_factor, expansion_factor]
        colors = ['#4472C4', '#E70000', '#70AD47', '#FFC000']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bottom = 0
        for i, (component, value, color) in enumerate(zip(components, values, colors)):
            if value > 0:
                ax.bar(0, value, bottom=bottom, color=color, label=f'{component}: +{value:.1f}', 
                      width=0.5, edgecolor='black')
                ax.text(0, bottom + value/2, f'+{value:.1f}', ha='center', va='center', 
                       fontweight='bold', color='white' if value > 0.2 else 'black')
                bottom += value
        
        ax.axhline(y=total_factor, color='red', linestyle='--', linewidth=2, 
                  label=f'Total Factor: {total_factor:.1f}')
        
        if total_factor <= 1.25:
            category = "Standard"
            cat_color = 'green'
        elif total_factor <= 1.5:
            category = "Moderate"
            cat_color = 'orange'
        else:
            category = "Conservative"
            cat_color = 'red'
        
        ax.text(0.6, total_factor, f'{category}\nApproach', ha='center', va='center',
               bbox=dict(boxstyle="round,pad=0.3", facecolor=cat_color, alpha=0.3),
               fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Safety Factor', fontsize=12)
        ax.set_title('Safety Factor Breakdown Analysis', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0, total_factor * 1.2)
        ax.set_xticks([])
        
        plt.tight_layout()
        return save_chart_to_bytes(fig)
        
    except Exception as e:
        print(f"Safety factor chart error: {e}")
        return None

def clean_text_simple(text):
    """Simple text cleaning for PDF compatibility"""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    
    # Simple replacements only
    replacements = {
        'σ': 'sigma', 'Δ': 'Delta', '≥': '>=', '≤': '<=', '°': ' deg'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove any problematic characters
    try:
        text = text.encode('latin-1', errors='ignore').decode('latin-1')
    except:
        text = ''.join(c for c in text if ord(c) < 256)
    
    return text

def create_robust_pdf_with_charts(report_data, chart_data):
    """Create robust PDF with simplified formatting to avoid errors"""
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("fpdf2 library not available")
    
    class RobustPDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, 'CONTROL VALVE SIZING REPORT', 0, 1, 'C')
            self.set_font('Arial', 'I', 10)
            self.cell(0, 6, 'Professional Engineering Analysis with Visual Charts', 0, 1, 'C')
            self.ln(8)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
        def add_text_line(self, label, value, bold_label=True):
            """Add a simple text line with label and value"""
            if bold_label:
                self.set_font('Arial', 'B', 10)
            else:
                self.set_font('Arial', '', 10)
            
            # Clean the text
            label_clean = clean_text_simple(str(label))
            value_clean = clean_text_simple(str(value))
            
            # Simple approach - use multi_cell for everything
            self.multi_cell(0, 6, f"{label_clean}: {value_clean}")
            self.ln(1)
        
        def add_section_header(self, title):
            self.ln(5)
            self.set_font('Arial', 'B', 12)
            self.set_fill_color(230, 230, 230)
            self.cell(0, 8, clean_text_simple(title), 0, 1, 'L', True)
            self.set_fill_color(255, 255, 255)
            self.ln(2)
        
        def add_chart_simple(self, chart_bytes, title):
            """Add chart with simple error handling"""
            if chart_bytes:
                try:
                    self.add_page()
                    self.set_font('Arial', 'B', 12)
                    self.cell(0, 8, clean_text_simple(title), 0, 1, 'C')
                    self.ln(5)
                    
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        chart_bytes.seek(0)
                        temp_file.write(chart_bytes.read())
                        temp_file_path = temp_file.name
                    
                    # Add image centered
                    page_width = self.w - 2 * self.l_margin
                    img_width = min(160, page_width)
                    img_height = img_width * 0.75
                    x_pos = (self.w - img_width) / 2
                    
                    self.image(temp_file_path, x=x_pos, w=img_width, h=img_height)
                    
                    # Clean up
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                        
                except Exception as e:
                    print(f"Chart error: {e}")
                    self.cell(0, 10, f"Chart unavailable: {clean_text_simple(title)}", 1, 1, 'C')
    
    pdf = RobustPDF()
    pdf.add_page()
    
    try:
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Header info
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, f"Generated: {report_data.get('report_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}", 0, 1)
        pdf.cell(0, 6, "Software: Enhanced Valve Sizing Application v2.0", 0, 1)
        pdf.ln(5)
        
        # Executive Summary
        pdf.add_section_header('EXECUTIVE SUMMARY')
        
        cv_value = results.get('cv', 'N/A')
        pdf.add_text_line("Required Cv", cv_value)
        
        # Status
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
        
        pdf.add_text_line("Sizing Status", status)
        
        # Add all charts
        chart_titles = {
            'valve_opening': 'Figure 1: Valve Opening Validation',
            'cavitation': 'Figure 2: Cavitation Analysis',
            'characteristic': 'Figure 3: Valve Characteristic Curve',
            'pressure_distribution': 'Figure 4: Pressure Distribution',
            'noise_assessment': 'Figure 5: Noise Assessment',
            'flow_regime': 'Figure 6: Gas Flow Analysis',
            'safety_factors': 'Figure 7: Safety Factor Analysis'
        }
        
        for chart_name, title in chart_titles.items():
            if chart_name in chart_data and chart_data[chart_name]:
                pdf.add_chart_simple(chart_data[chart_name], title)
        
        # Detailed sections
        pdf.add_page()
        
        # Process Conditions
        pdf.add_section_header('PROCESS CONDITIONS')
        pdf.add_text_line("Fluid Type", inputs.get('fluid_type', 'N/A'))
        pdf.add_text_line("Flow Rate", f"{inputs.get('flow_rate', 'N/A')} {get_safe_flow_unit(inputs)}")
        pdf.add_text_line("Inlet Pressure", f"{inputs.get('p1', 'N/A')} {get_safe_pressure_unit(inputs)}")
        pdf.add_text_line("Outlet Pressure", f"{inputs.get('p2', 'N/A')} {get_safe_pressure_unit(inputs)}")
        pdf.add_text_line("Temperature", f"{inputs.get('t1', 'N/A')} {get_safe_temp_unit(inputs)}")
        
        # Valve Selection
        pdf.add_section_header('VALVE SELECTION')
        pdf.add_text_line("Valve Type", inputs.get('valve_type', 'N/A'))
        pdf.add_text_line("Nominal Size", f"{inputs.get('valve_size_nominal', 'N/A')} inches")
        pdf.add_text_line("Flow Characteristic", inputs.get('valve_char', 'N/A'))
        pdf.add_text_line("Actuator Type", format_safe_actuator_type(inputs.get('actuator_type', 'N/A')))
        
        # Sizing Results
        pdf.add_section_header('SIZING RESULTS')
        pdf.add_text_line("Required Cv", cv_value)
        if 'reynolds_factor' in results:
            pdf.add_text_line("Reynolds Factor (FR)", f"{results['reynolds_factor']:.4f}")
        if 'ff_factor' in results:
            pdf.add_text_line("FF Factor", f"{results['ff_factor']:.4f}")
        pdf.add_text_line("Rated Cv", results.get('rated_cv', 'N/A'))
        
        # Add remaining sections with simple formatting
        if 'sigma_analysis' in results:
            pdf.add_section_header('CAVITATION ANALYSIS')
            sigma_data = results['sigma_analysis']
            if isinstance(sigma_data.get('sigma'), (int, float)):
                pdf.add_text_line("Sigma Value", f"{sigma_data['sigma']:.3f}")
            pdf.add_text_line("Cavitation Level", sigma_data.get('level', 'N/A'))
            pdf.add_text_line("Risk Assessment", sigma_data.get('risk', 'N/A'))
        
        # Noise Analysis
        pdf.add_section_header('NOISE ANALYSIS')
        noise_level = results.get('total_noise_dba', 0)
        if isinstance(noise_level, (int, float)):
            noise_status = "ACCEPTABLE" if noise_level < 85 else "HIGH" if noise_level < 110 else "EXTREME"
            pdf.add_text_line("Noise Level", f"{noise_level:.1f} dBA ({noise_status})")
        
        # Professional notes
        pdf.add_section_header('PROFESSIONAL NOTES')
        notes = [
            "This report is for preliminary valve sizing purposes only.",
            "Final selection must be verified with manufacturer software.",
            "All calculations follow published industry standards.",
            "Professional engineering review recommended for critical applications."
        ]
        
        for i, note in enumerate(notes, 1):
            pdf.add_text_line(f"{i}", note, False)
        
        return pdf.output(dest='S').encode('latin-1')
    
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise e

def create_simple_pdf_report(report_data):
    """Create simple PDF without charts as fallback"""
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'CONTROL VALVE SIZING REPORT', 0, 1, 'C')
        pdf.ln(10)
        
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Basic info
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
        pdf.ln(5)
        
        # Results
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 8, 'SIZING RESULTS', 0, 1)
        pdf.set_font('Arial', '', 12)
        
        cv_value = results.get('cv', 'N/A')
        pdf.cell(0, 6, f'Required Cv: {cv_value}', 0, 1)
        pdf.cell(0, 6, f'Rated Cv: {results.get("rated_cv", "N/A")}', 0, 1)
        
        # Process conditions
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 8, 'PROCESS CONDITIONS', 0, 1)
        pdf.set_font('Arial', '', 12)
        
        pdf.cell(0, 6, f'Fluid Type: {inputs.get("fluid_type", "N/A")}', 0, 1)
        pdf.cell(0, 6, f'Flow Rate: {inputs.get("flow_rate", "N/A")} {get_safe_flow_unit(inputs)}', 0, 1)
        pdf.cell(0, 6, f'Inlet Pressure: {inputs.get("p1", "N/A")} {get_safe_pressure_unit(inputs)}', 0, 1)
        pdf.cell(0, 6, f'Outlet Pressure: {inputs.get("p2", "N/A")} {get_safe_pressure_unit(inputs)}', 0, 1)
        
        # Valve selection
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 8, 'VALVE SELECTION', 0, 1)
        pdf.set_font('Arial', '', 12)
        
        pdf.cell(0, 6, f'Valve Type: {inputs.get("valve_type", "N/A")}', 0, 1)
        pdf.cell(0, 6, f'Size: {inputs.get("valve_size_nominal", "N/A")} inches', 0, 1)
        pdf.cell(0, 6, f'Characteristic: {inputs.get("valve_char", "N/A")}', 0, 1)
        
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        print(f"Simple PDF error: {e}")
        raise e

def create_minimal_pdf_report(report_data):
    """Create minimal PDF as ultimate fallback"""
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'CONTROL VALVE SIZING REPORT', 0, 1, 'C')
        pdf.ln(10)
        
        results = report_data.get('results', {})
        cv_value = results.get('cv', 'N/A')
        
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f'Required Cv: {cv_value}', 0, 1)
        pdf.ln(5)
        pdf.cell(0, 6, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
        
        pdf.ln(10)
        pdf.multi_cell(0, 6, 'This is a minimal report due to PDF generation issues. For complete analysis, please ensure all required libraries are properly installed.')
        
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        print(f"Minimal PDF error: {e}")
        # Final fallback - return basic bytes
        content = f"VALVE SIZING REPORT\nRequired Cv: {results.get('cv', 'N/A')}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return content.encode('utf-8')

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
