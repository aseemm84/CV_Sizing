"""
Enhanced Professional PDF Generator with Charts and Graphs
"""
from datetime import datetime
import io
import os
import tempfile
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

def create_pdf_report(report_data):
    """
    Create comprehensive PDF report with charts and graphs
    Enhanced with better error handling and robust fallbacks
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"valve_sizing_report_{timestamp}.pdf"
    
    # Generate charts first as byte streams (more reliable than files)
    chart_data = generate_charts_as_bytes(report_data)
    
    # Try fpdf2 first (recommended)
    try:
        pdf_bytes = create_comprehensive_pdf_with_charts(report_data, chart_data)
        return filename, pdf_bytes
    except ImportError:
        print("fpdf2 not available, trying alternative methods...")
    except Exception as e:
        print(f"fpdf2 error: {e}, trying alternative methods...")
    
    # Try HTML to PDF conversion as backup
    try:
        pdf_bytes = create_html_to_pdf_report(report_data, chart_data)
        return filename, pdf_bytes
    except ImportError:
        print("HTML-to-PDF libraries not available, using basic PDF...")
    except Exception as e:
        print(f"HTML-to-PDF error: {e}, using basic PDF...")
    
    # Basic PDF fallback (still generates PDF, not text)
    try:
        pdf_bytes = create_basic_pdf_with_essential_data(report_data)
        return filename, pdf_bytes
    except Exception as e:
        print(f"Basic PDF error: {e}, creating minimal PDF...")
        # Ultimate fallback - minimal but still PDF
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
        plt.close(fig)  # Clean up
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
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(scenarios, openings, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
        
        # Add optimal range shading
        ax.axhspan(20, 80, alpha=0.2, color='green', label='Optimal Range (20-80%)')
        
        # Add value labels on bars
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
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create horizontal bar chart
        y_pos = np.arange(len(levels))
        bars = ax.barh(y_pos, sigma_values, color=colors, alpha=0.7, edgecolor='black')
        
        # Add current operating point
        ax.axvline(x=current_sigma, color='red', linestyle='--', linewidth=3, 
                  label=f'Operating Point: σ = {current_sigma:.3f}')
        
        # Add text labels
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
        
        # Add risk assessment text
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
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot characteristic curve
        ax.plot(openings, flows, 'b-', linewidth=3, label=f'{valve_char} Characteristic')
        
        # Add operating point
        if 10 <= operating_opening <= 100:
            if valve_char == 'Linear':
                operating_flow = operating_opening
            elif valve_char == 'Quick Opening':
                operating_flow = np.sqrt(operating_opening / 100) * 100
            else:  # Equal Percentage
                operating_flow = (50**(operating_opening/100 - 1)) / (50**(1-1)) * 100
            
            ax.plot(operating_opening, operating_flow, 'ro', markersize=12, 
                   label=f'Operating Point ({operating_opening}%, {operating_flow:.1f}%)')
            
            # Add operating point lines
            ax.axvline(x=operating_opening, color='red', linestyle=':', alpha=0.7)
            ax.axhline(y=operating_flow, color='red', linestyle=':', alpha=0.7)
        
        # Add optimal operating range
        ax.axvspan(20, 80, alpha=0.2, color='green', label='Optimal Operating Range')
        
        # Add ideal linear line for reference
        ax.plot([0, 100], [0, 100], 'k--', alpha=0.5, label='Linear Reference')
        
        ax.set_xlabel('Valve Opening (%)', fontsize=12)
        ax.set_ylabel('Flow Rate (% of Maximum)', fontsize=12)
        ax.set_title(f'{valve_type} Valve Flow Characteristic\n{valve_char} Curve', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        
        # Add rangeability information
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
        
        # Create pressure distribution
        pressures = [p1, p2, pv] if fluid_type == 'Liquid' else [p1, p2]
        labels = ['Inlet (P1)', 'Outlet (P2)', 'Vapor (Pv)'] if fluid_type == 'Liquid' else ['Inlet (P1)', 'Outlet (P2)']
        colors = ['#4472C4', '#E70000', '#70AD47'] if fluid_type == 'Liquid' else ['#4472C4', '#E70000']
        
        # Bar chart
        bars = ax.bar(labels, pressures, color=colors, alpha=0.7, edgecolor='black')
        
        # Add value labels
        for bar, pressure in zip(bars, pressures):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(pressures)*0.01,
                   f'{pressure:.2f} bar', ha='center', va='bottom', fontweight='bold')
        
        # Add differential pressure
        dp = p1 - p2
        ax.text(0.5, max(pressures) * 0.8, f'ΔP = {dp:.2f} bar', 
               ha='center', transform=ax.transData,
               bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', alpha=0.8),
               fontsize=12, fontweight='bold')
        
        # Add pressure ratio for liquids
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
        # Define noise level ranges
        ranges = ['Acceptable\n<85 dBA', 'Moderate\n85-100 dBA', 'High\n100-110 dBA', 'Extreme\n>110 dBA']
        levels = [85, 100, 110, 130]  # Upper limits for visualization
        colors = ['#2E8B57', '#FFD700', '#FFA500', '#DC143C']
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create horizontal bar chart showing ranges
        y_pos = np.arange(len(ranges))
        bars = ax.barh(y_pos, levels, color=colors, alpha=0.7, edgecolor='black')
        
        # Add current noise level line
        ax.axvline(x=noise_level, color='red', linestyle='-', linewidth=4, 
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
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(ranges)
        ax.set_xlabel('Noise Level (dBA)', fontsize=12)
        ax.set_ylabel('Assessment Category', fontsize=12)
        ax.set_title('Noise Level Assessment at 1 Meter Distance', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.legend()
        ax.set_xlim(0, 130)
        
        # Add assessment text
        ax.text(0.02, 0.98, f'Assessment: {category}', transform=ax.transAxes, 
               fontsize=14, fontweight='bold', color=category_color,
               bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Add recommendations
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
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create stacked bar
        bottom = 0
        for i, (component, value, color) in enumerate(zip(components, values, colors)):
            if value > 0:
                ax.bar(0, value, bottom=bottom, color=color, label=f'{component}: +{value:.1f}', 
                      width=0.5, edgecolor='black')
                # Add value label
                ax.text(0, bottom + value/2, f'+{value:.1f}', ha='center', va='center', 
                       fontweight='bold', color='white' if value > 0.2 else 'black')
                bottom += value
        
        # Add total line
        ax.axhline(y=total_factor, color='red', linestyle='--', linewidth=2, 
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
        
        ax.text(0.6, total_factor, f'{category}\nApproach', ha='center', va='center',
               bbox=dict(boxstyle="round,pad=0.3", facecolor=cat_color, alpha=0.3),
               fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Safety Factor', fontsize=12)
        ax.set_title('Safety Factor Breakdown Analysis', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(0, total_factor * 1.2)
        ax.set_xticks([])  # Remove x-axis ticks
        
        plt.tight_layout()
        return save_chart_to_bytes(fig)
        
    except Exception as e:
        print(f"Safety factor chart error: {e}")
        return None

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

def truncate_text_to_fit(text, max_width, font_size=10):
    """Truncate text to fit within specified width"""
    if not text:
        return ""
    
    # Approximate character width (rough estimate for Arial)
    char_width = font_size * 0.6  # pixels per character
    max_chars = int(max_width / char_width)
    
    if len(text) <= max_chars:
        return text
    else:
        return text[:max_chars-3] + "..."

def create_comprehensive_pdf_with_charts(report_data, chart_data):
    """Create comprehensive professional PDF with embedded charts - FIXED VERSION"""
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("fpdf2 library not available")
    
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
        
        def safe_cell(self, w, h, txt='', border=0, ln=0, align='', fill=False, max_width=None):
            """Enhanced safe_cell with text truncation"""
            try:
                cleaned_txt = clean_unicode_for_pdf(str(txt))
                if max_width:
                    cleaned_txt = truncate_text_to_fit(cleaned_txt, max_width)
                self.cell(w, h, cleaned_txt, border, ln, align, fill)
            except Exception as e:
                print(f"Cell error: {e}")
                self.cell(w, h, "Data unavailable", border, ln, align, fill)
        
        def safe_multi_cell(self, w, h, txt, border=0, align='L', fill=False, max_chars=None):
            """Enhanced safe_multi_cell with better text handling"""
            try:
                cleaned_txt = clean_unicode_for_pdf(str(txt))
                if max_chars and len(cleaned_txt) > max_chars:
                    cleaned_txt = cleaned_txt[:max_chars-3] + "..."
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
        
        def add_key_value_pair(self, key, value, indent=0, key_width=70):
            """Enhanced key-value with better width management"""
            self.safe_cell(indent, 6, '', 0, 0)
            self.set_font('Arial', 'B', 10)
            # Truncate key if too long
            key_text = truncate_text_to_fit(str(key), key_width)
            self.safe_cell(key_width, 6, f"{key_text}:", 0, 0)
            self.set_font('Arial', '', 10)
            # Calculate remaining width for value
            remaining_width = self.w - self.l_margin - self.r_margin - indent - key_width
            value_text = truncate_text_to_fit(str(value), remaining_width)
            self.safe_cell(0, 6, value_text, 0, 1)
        
        def add_chart_from_bytes(self, chart_bytes, title, width=160, height=None):
            """Add chart to PDF from byte stream with title"""
            if chart_bytes:
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
                    
                    # Create temporary file for fpdf
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        chart_bytes.seek(0)
                        temp_file.write(chart_bytes.read())
                        temp_file_path = temp_file.name
                    
                    self.image(temp_file_path, x=x_pos, w=width, h=height)
                    self.ln(5)
                    
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                        
                except Exception as e:
                    print(f"Chart insertion error: {e}")
                    self.safe_cell(0, 10, f"Chart unavailable: {title}", 1, 1, 'C')
            else:
                self.safe_cell(0, 10, f"Chart unavailable: {title}", 1, 1, 'C')
    
    pdf = ProfessionalValvePDFWithCharts()
    pdf.add_page()
    
    try:
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        # Report Header Information
        pdf.set_font('Arial', '', 11)
        pdf.safe_cell(0, 6, f"Generated: {report_data.get('report_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}", 0, 1)
        pdf.safe_cell(0, 6, f"Software: Enhanced Valve Sizing Application v2.0", 0, 1)
        pdf.safe_cell(0, 6, f"Analysis: Professional Engineering with Visual Charts", 0, 1)
        
        # Standards compliance
        standards = ['ISA S75.01/IEC 60534-2-1', 'ISA RP75.23', 'IEC 60534-8-3', 'API 6D', 'NACE MR0175', 'ASME B16.34']
        standards_text = ', '.join(standards)
        pdf.safe_multi_cell(0, 6, f"Standards: {standards_text}", max_chars=200)
        
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
        if 'valve_opening' in chart_data and chart_data['valve_opening']:
            pdf.add_page()
            pdf.add_chart_from_bytes(chart_data['valve_opening'], 
                                   'Figure 1: Valve Opening Validation Across Flow Scenarios')
        
        # CHART 2: Cavitation Analysis 
        if 'cavitation' in chart_data and chart_data['cavitation']:
            pdf.add_page()
            pdf.add_chart_from_bytes(chart_data['cavitation'], 
                                   'Figure 2: ISA RP75.23 Cavitation Analysis')
        
        # CHART 3: Valve Characteristic
        if 'characteristic' in chart_data and chart_data['characteristic']:
            pdf.add_page()
            pdf.add_chart_from_bytes(chart_data['characteristic'], 
                                   'Figure 3: Valve Flow Characteristic Curve')
        
        # CHART 4: Pressure Distribution
        if 'pressure_distribution' in chart_data and chart_data['pressure_distribution']:
            pdf.add_page()
            pdf.add_chart_from_bytes(chart_data['pressure_distribution'], 
                                   'Figure 4: Pressure Distribution Analysis')
        
        # CHART 5: Noise Assessment
        if 'noise_assessment' in chart_data and chart_data['noise_assessment']:
            pdf.add_page()
            pdf.add_chart_from_bytes(chart_data['noise_assessment'], 
                                   'Figure 5: Noise Level Assessment')
        
        # CHART 6: Gas Flow Analysis (if applicable)
        if 'flow_regime' in chart_data and chart_data['flow_regime']:
            pdf.add_page()
            pdf.add_chart_from_bytes(chart_data['flow_regime'], 
                                   'Figure 6: Gas Flow Analysis')
        
        # CHART 7: Safety Factor Analysis
        if 'safety_factors' in chart_data and chart_data['safety_factors']:
            pdf.add_page()
            pdf.add_chart_from_bytes(chart_data['safety_factors'], 
                                   'Figure 7: Safety Factor Breakdown')
        
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
            pdf.safe_multi_cell(0, 5, recommendation, max_chars=500)
        
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
        pdf.safe_multi_cell(0, 5, clean_unicode_for_pdf(noise_rec), max_chars=500)
        
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
        pdf.safe_multi_cell(0, 5, clean_unicode_for_pdf(actuator_rec), max_chars=500)
        
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
                pdf.safe_multi_cell(0, 5, clean_unicode_for_pdf(results['compliance_check']), max_chars=500)
        
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
            pdf.safe_multi_cell(0, 5, disclaimer, max_chars=500)
            pdf.ln(1)
        
        pdf.ln(5)
        
        pdf.set_font('Arial', 'I', 9)
        footer_text = ("This enhanced report includes visual analysis charts to support engineering decisions. "
                      "All charts are generated from calculated data following industry standards. "
                      "Professional engineering review is recommended for critical applications.")
        pdf.safe_multi_cell(0, 4, footer_text, max_chars=500)
        
        return bytes(pdf.output(dest='S'), 'latin-1')
    
    except Exception as e:
        print(f"PDF with charts generation error: {e}")
        raise e

def create_html_to_pdf_report(report_data, chart_data):
    """Create PDF using HTML template and WeasyPrint as backup method"""
    try:
        from weasyprint import HTML
        import base64
    except ImportError:
        raise ImportError("WeasyPrint not available")
    
    # Convert chart byte streams to base64 for HTML embedding
    charts_b64 = {}
    for chart_name, chart_bytes in chart_data.items():
        if chart_bytes:
            chart_bytes.seek(0)
            img_b64 = base64.b64encode(chart_bytes.read()).decode()
            charts_b64[chart_name] = img_b64
    
    # Create HTML template
    inputs = report_data.get('inputs', {})
    results = report_data.get('results', {})
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Control Valve Sizing Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.4; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .section {{ margin: 20px 0; page-break-inside: avoid; }}
            .section-title {{ background-color: #f0f0f0; padding: 8px; font-weight: bold; font-size: 14px; }}
            .chart {{ text-align: center; margin: 20px 0; page-break-inside: avoid; }}
            .chart img {{ max-width: 100%; height: auto; }}
            .key-value {{ margin: 5px 0; word-wrap: break-word; }}
            .key {{ font-weight: bold; display: inline-block; width: 180px; vertical-align: top; }}
            .value {{ display: inline-block; max-width: 300px; word-wrap: break-word; }}
            @page {{ margin: 1in; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>CONTROL VALVE SIZING REPORT</h1>
            <p><i>Professional Engineering Analysis with Visual Charts</i></p>
            <p>Generated: {report_data.get('report_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
        </div>
        
        <div class="section">
            <div class="section-title">EXECUTIVE SUMMARY</div>
            <div class="key-value"><span class="key">Required Cv:</span> <span class="value">{results.get('cv', 'N/A')}</span></div>
            <div class="key-value"><span class="key">Cavitation Risk:</span> <span class="value">{results.get('sigma_analysis', {}).get('risk', 'N/A')}</span></div>
            <div class="key-value"><span class="key">Noise Level:</span> <span class="value">{results.get('total_noise_dba', 'N/A')} dBA</span></div>
        </div>
    """
    
    # Add charts
    chart_titles = {
        'valve_opening': 'Figure 1: Valve Opening Validation Across Flow Scenarios',
        'cavitation': 'Figure 2: ISA RP75.23 Cavitation Analysis',
        'characteristic': 'Figure 3: Valve Flow Characteristic Curve',
        'pressure_distribution': 'Figure 4: Pressure Distribution Analysis',
        'noise_assessment': 'Figure 5: Noise Level Assessment',
        'flow_regime': 'Figure 6: Gas Flow Analysis',
        'safety_factors': 'Figure 7: Safety Factor Breakdown'
    }
    
    for chart_name, title in chart_titles.items():
        if chart_name in charts_b64:
            html_content += f"""
            <div class="chart">
                <h3>{title}</h3>
                <img src="data:image/png;base64,{charts_b64[chart_name]}" alt="{title}">
            </div>
            """
    
    # Add process conditions section
    html_content += f"""
        <div class="section">
            <div class="section-title">PROCESS CONDITIONS</div>
            <div class="key-value"><span class="key">Fluid Type:</span> <span class="value">{inputs.get('fluid_type', 'N/A')}</span></div>
            <div class="key-value"><span class="key">Flow Rate:</span> <span class="value">{inputs.get('flow_rate', 'N/A')} {get_safe_flow_unit(inputs)}</span></div>
            <div class="key-value"><span class="key">Inlet Pressure:</span> <span class="value">{inputs.get('p1', 'N/A')} {get_safe_pressure_unit(inputs)}</span></div>
            <div class="key-value"><span class="key">Outlet Pressure:</span> <span class="value">{inputs.get('p2', 'N/A')} {get_safe_pressure_unit(inputs)}</span></div>
            <div class="key-value"><span class="key">Temperature:</span> <span class="value">{inputs.get('t1', 'N/A')} {get_safe_temp_unit(inputs)}</span></div>
        </div>
        
        <div class="section">
            <div class="section-title">VALVE SELECTION</div>
            <div class="key-value"><span class="key">Valve Type:</span> <span class="value">{inputs.get('valve_type', 'N/A')}</span></div>
            <div class="key-value"><span class="key">Nominal Size:</span> <span class="value">{inputs.get('valve_size_nominal', 'N/A')} inches</span></div>
            <div class="key-value"><span class="key">Flow Characteristic:</span> <span class="value">{inputs.get('valve_char', 'N/A')}</span></div>
            <div class="key-value"><span class="key">Actuator Type:</span> <span class="value">{format_safe_actuator_type(inputs.get('actuator_type', 'N/A'))}</span></div>
        </div>
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes

def create_basic_pdf_with_essential_data(report_data):
    """Create basic PDF with essential data (fallback method)"""
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("fpdf2 library not available")
    
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'CONTROL VALVE SIZING REPORT', 0, 1, 'C')
    pdf.ln(10)
    
    inputs = report_data.get('inputs', {})
    results = report_data.get('results', {})
    
    # Essential results
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 8, 'SIZING RESULTS', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    cv_value = results.get('cv', 'N/A')
    pdf.cell(0, 6, f'Required Cv: {cv_value}', 0, 1)
    pdf.cell(0, 6, f'Rated Cv: {results.get("rated_cv", "N/A")}', 0, 1)
    pdf.cell(0, 6, f'Rangeability: {results.get("inherent_rangeability", "N/A")}:1', 0, 1)
    
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
    pdf.cell(0, 6, f'Nominal Size: {inputs.get("valve_size_nominal", "N/A")} inches', 0, 1)
    pdf.cell(0, 6, f'Flow Characteristic: {inputs.get("valve_char", "N/A")}', 0, 1)
    
    # Analysis summary
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 8, 'ANALYSIS SUMMARY', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    if 'sigma_analysis' in results:
        sigma_data = results['sigma_analysis']
        pdf.cell(0, 6, f'Cavitation Level: {sigma_data.get("level", "N/A")}', 0, 1)
        pdf.cell(0, 6, f'Cavitation Risk: {sigma_data.get("risk", "N/A")}', 0, 1)
    
    noise_level = results.get('total_noise_dba', 0)
    if isinstance(noise_level, (int, float)):
        pdf.cell(0, 6, f'Noise Level: {noise_level:.1f} dBA', 0, 1)
    
    # Note about charts
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    pdf.multi_cell(0, 5, 'Note: This is a basic report. Full visual analysis charts are available in the complete version with proper PDF libraries installed.')
    
    return bytes(pdf.output(dest='S'), 'latin-1')

def create_minimal_pdf_report(report_data):
    """Create minimal PDF report (ultimate fallback)"""
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'CONTROL VALVE SIZING REPORT', 0, 1, 'C')
        
        # Add basic content
        inputs = report_data.get('inputs', {})
        results = report_data.get('results', {})
        
        pdf.set_font('Arial', '', 12)
        pdf.ln(10)
        
        # Key results only
        cv_value = results.get('cv', 'N/A')
        pdf.cell(0, 8, f'Required Cv: {cv_value}', 0, 1)
        
        pdf.ln(5)
        pdf.cell(0, 6, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
        pdf.cell(0, 6, f'Status: Basic report due to library limitations', 0, 1)
        
        pdf.ln(10)
        pdf.multi_cell(0, 6, 'This is a minimal report. For complete analysis with charts and detailed calculations, ensure fpdf2 and matplotlib libraries are properly installed.')
        
        return bytes(pdf.output(dest='S'), 'latin-1')
        
    except Exception as e:
        # Ultimate fallback - create basic content as bytes
        basic_content = f"""
CONTROL VALVE SIZING REPORT
===========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Required Cv: {results.get('cv', 'N/A')}
Error: Could not generate PDF: {e}

Please install required libraries:
pip install fpdf2 matplotlib numpy
"""
        return basic_content.encode('utf-8')

# Include all the helper functions
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
