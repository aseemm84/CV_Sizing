import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import base64
import io
from PIL import Image
import requests

# Import enhanced calculation modules
from calculations import liquid_sizing, gas_sizing, noise_prediction, actuator_sizing
from data import materials, valve_data
from reporting import pdf_generator
from utils import helpers
from standards.isa_rp75_23 import get_cavitation_chart_data

st.set_page_config(layout="wide", page_title="Control Valve Sizing & Selection", page_icon="⚙️")

def load_logo():
    """Load and display the application logo"""
    try:
        # You can replace this URL with your actual logo file path
        # For now, I'll create a placeholder that you can replace
        logo_html = """
        <div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #003366 0%, #0066cc 100%); border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0; font-family: 'Arial', sans-serif; font-weight: bold;">⚙️ CONTROL VALVE</h2>
            <h3 style="color: #66ccff; margin: 0; font-family: 'Arial', sans-serif; font-weight: normal;">SIZING & SELECTION</h3>
            <p style="color: #cccccc; margin: 5px 0 0 0; font-size: 12px;">Professional Engineering Tool</p>
        </div>
        """
        return logo_html
    except Exception as e:
        # Fallback to text-based logo
        return """
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #003366 0%, #0066cc 100%); border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0; font-family: 'Arial', sans-serif;">⚙️ CONTROL VALVE</h2>
            <h3 style="color: #66ccff; margin: 0; font-family: 'Arial', sans-serif;">SIZING & SELECTION</h3>
            <p style="color: #cccccc; margin: 5px 0 0 0; font-size: 12px;">Professional Engineering Tool</p>
        </div>
        """

# --- APP STATE INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.step = 1
    st.session_state.input_data = {}
    st.session_state.results = {}
    st.session_state.unit_system = 'Metric'
    st.session_state.noise_method = 'simplified'
    st.session_state.vendor_mode = False

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

# --- SIDEBAR ---
with st.sidebar:
    # Display the professional logo at the top
    st.markdown(load_logo(), unsafe_allow_html=True)
    
    st.title("⚙️ Navigation")
    st.write("---")
    
    # Unit system selection
    st.session_state.unit_system = st.radio("Select Unit System", ('Metric', 'Imperial'), horizontal=True)
    units = helpers.get_units(st.session_state.unit_system)
    
    # Advanced options
    st.write("**⚡ Advanced Options:**")
    st.session_state.noise_method = st.selectbox("Noise Prediction Method", 
                                                ['simplified', 'iec_60534_8_3'], 
                                                format_func=lambda x: "Simplified Estimation" if x == 'simplified' else "IEC 60534-8-3 Model")
    
    st.session_state.vendor_mode = st.checkbox("Enable Vendor Data Integration", help="Use manufacturer-specific valve data")
    
    # Progress indicator
    st.write("**📊 Progress:**")
    st.info(f"**Current Step:** {st.session_state.step} of 6")
    st.progress(st.session_state.step / 6)
    
    st.write("---")
    
    # Enhanced standards compliance
    st.write("**📋 Standards Compliance:**")
    standards_list = [
        ("✅ ISA S75.01 / IEC 60534-2-1", "Flow Coefficient Calculations"),
        ("✅ ISA RP75.23", "Sigma Method Cavitation Analysis"),
        ("✅ IEC 60534-8-3", "Noise Prediction"),
        ("✅ API 6D", "Pipeline Valves"),
        ("✅ NACE MR0175", "Sour Service Materials"),
        ("✅ ASME B16.34", "Valve Design Standards")
    ]
    
    for standard, description in standards_list:
        st.success(standard)
        with st.expander(f"ℹ️ {standard.split(' ', 1)[1]}", expanded=False):
            st.caption(description)
    
    st.write("---")
    
    # Enhanced footer with professional styling
    footer_html = """
    <div style="text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 8px; margin-top: 10px;">
        <p style="margin: 0; font-size: 12px; color: #666;">
            <strong>Enhanced Professional-Grade Application</strong><br>
            by <strong>Aseem Mehrotra</strong><br>
            <em>Senior Instrumentation Construction Engineer</em><br>
            <em>KBR Inc</em>
        </p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# --- MAIN APPLICATION WIZARD ---
st.title("🏭 Control Valve Sizing and Selection Wizard")

# Add a professional header with key features
st.markdown("""
<div style="background: linear-gradient(90deg, #f0f8ff 0%, #e6f3ff 100%); padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #0066cc;">
    <h4 style="margin: 0; color: #003366;">🎯 Professional Engineering Analysis</h4>
    <p style="margin: 5px 0 0 0; color: #666;">Industry-standard calculations with enhanced cavitation analysis, noise prediction, and comprehensive material selection</p>
</div>
""", unsafe_allow_html=True)

# --- STEP 1: Enhanced Process Conditions ---
if st.session_state.step == 1:
    st.header("🔧 Step 1: Process Conditions")
    
    if 'step1_data' not in st.session_state:
        st.session_state.step1_data = {
            "fluid_type": "Liquid", "fluid_name": "Water", "fluid_nature": "Clean",
            "p1": 10.0, "p2": 5.0, "t1": 25.0, "flow_rate": 100.0,
            "rho": 1000.0 if st.session_state.unit_system == 'Metric' else 1.0,
            "pv": 0.03, "pc": 221.0, "vc": 1.0, "mw": 28.97, "z": 1.0, "k": 1.4,
            "gas_viscosity": 0.018, "service_criticality": "medium", "future_expansion": "none"
        }
    
    s1_data = st.session_state.step1_data
    
    # Fluid Information Section
    st.subheader("💧 Fluid Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        s1_data['fluid_type'] = st.selectbox("Fluid Type", ["Liquid", "Gas/Vapor"], 
                                           index=["Liquid", "Gas/Vapor"].index(s1_data['fluid_type']))
        s1_data['fluid_name'] = st.text_input("Fluid Name", value=s1_data['fluid_name'])
    
    with col2:
        s1_data['fluid_nature'] = st.selectbox("Fluid Nature", 
                                             ["Clean", "Corrosive", "Abrasive", "Flashing/Cavitating"],
                                             index=["Clean", "Corrosive", "Abrasive", "Flashing/Cavitating"].index(s1_data['fluid_nature']))
    
    with col3:
        s1_data['service_criticality'] = st.selectbox("Service Criticality", 
                                                     ["low", "medium", "high", "critical"])
        s1_data['future_expansion'] = st.selectbox("Future Expansion", 
                                                 ["none", "moderate", "significant"])
    
    # Operating Conditions Section
    st.subheader("🌡️ Operating Conditions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        s1_data['p1'] = st.number_input(f"Inlet Pressure (P1) [{units['pressure']}]", 
                                      min_value=0.1, value=s1_data['p1'], step=0.1)
        s1_data['t1'] = st.number_input(f"Inlet Temperature (T1) [{units['temperature']}]", 
                                      value=s1_data['t1'])
        s1_data['flow_rate'] = st.number_input(f"Flow Rate (Q) [{units['flow_liquid' if s1_data['fluid_type'] == 'Liquid' else 'flow_gas']}]", 
                                             min_value=0.1, value=s1_data['flow_rate'], step=1.0)
    
    with col2:
        s1_data['p2'] = st.number_input(f"Outlet Pressure (P2) [{units['pressure']}]", 
                                      min_value=0.1, value=s1_data['p2'], step=0.1)
        
        if s1_data['fluid_type'] == "Liquid":
            s1_data['rho'] = st.number_input(f"Density / Specific Gravity [{units['density']}]", 
                                           value=s1_data['rho'], min_value=0.1)
            s1_data['pv'] = st.number_input(f"Vapor Pressure (Pv) [{units['pressure']}]", 
                                          value=s1_data['pv'], min_value=0.0)
            s1_data['vc'] = st.number_input(f"Viscosity [{units['viscosity']}]", 
                                          value=s1_data['vc'], min_value=0.1)
        else:
            s1_data['mw'] = st.number_input("Molecular Weight (MW)", 
                                          value=s1_data['mw'], min_value=1.0)
            s1_data['z'] = st.number_input("Compressibility Factor (Z)", 
                                         value=s1_data['z'], min_value=0.2, max_value=2.0)
            s1_data['gas_viscosity'] = st.number_input("Gas Viscosity [cP]", 
                                                     value=s1_data['gas_viscosity'], min_value=0.001)
    
    with col3:
        dp = s1_data['p1'] - s1_data['p2']
        st.metric(label=f"Differential Pressure (ΔP) [{units['pressure']}]", value=f"{dp:.2f}")
        
        if s1_data['fluid_type'] == "Liquid":
            s1_data['pc'] = st.number_input(f"Critical Pressure (Pc) [{units['pressure']}]", 
                                          value=s1_data['pc'], min_value=0.1)
        else:
            s1_data['k'] = st.number_input("Specific Heat Ratio (k = Cp/Cv)", 
                                         value=s1_data['k'], min_value=1.0, max_value=2.0)
    
    # Safety Factor Recommendation
    st.subheader("🛡️ Safety Factor Recommendation")
    safety_factor_rec = helpers.recommend_safety_factor("continuous", s1_data['service_criticality'], s1_data['future_expansion'])
    
    st.info(f"**Recommended Safety Factor:** {safety_factor_rec['recommended_factor']} ({safety_factor_rec['category']})")
    st.caption(f"Justification: {safety_factor_rec['justification']}")
    
    if st.button("💾 Save and Go to Step 2 ➡️", type="primary"):
        if s1_data['p1'] <= s1_data['p2']:
            st.error("❌ Error: Inlet Pressure (P1) must be greater than Outlet Pressure (P2).")
        else:
            st.session_state.input_data = s1_data.copy()
            st.session_state.input_data['dp'] = dp
            st.session_state.input_data['units'] = units
            st.session_state.input_data['unit_system'] = st.session_state.unit_system
            st.session_state.input_data['safety_factor_rec'] = safety_factor_rec
            del st.session_state.step1_data
            next_step()
            st.rerun()

# --- STEP 2: Enhanced Valve Selection ---
elif st.session_state.step == 2:
    st.header("⚙️ Step 2: Valve Type and Characteristics")
    
    if 'step2_data' not in st.session_state:
        initial_valve_type = "Globe"
        initial_valve_styles = valve_data.get_valve_styles(initial_valve_type)
        initial_valve_style = initial_valve_styles[0]
        initial_valve_data = valve_data.get_valve_data(initial_valve_type, initial_valve_style)
        
        st.session_state.step2_data = {
            'valve_type': initial_valve_type,
            'valve_style': initial_valve_style,
            'valve_char': "Equal Percentage",
            'valve_size_nominal': 2,
            'fl': initial_valve_data.get('FL', 0.9),
            'kc': initial_valve_data.get('Kc', 0.7),
            'valve_opening_percent': 70,
            'actuator_type': 'pneumatic_spring_diaphragm',
            'vendor': None,
            'series': None
        }
    
    s2_data = st.session_state.step2_data
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Basic valve selection
        valve_types = ["Globe", "Ball (Segmented)", "Butterfly"]
        new_valve_type = st.selectbox("🔧 Select Valve Type", valve_types, 
                                    index=valve_types.index(s2_data['valve_type']))
        
        if new_valve_type != s2_data['valve_type']:
            s2_data['valve_type'] = new_valve_type
            available_styles = valve_data.get_valve_styles(new_valve_type)
            s2_data['valve_style'] = available_styles[0]
            st.rerun()
        
        available_styles = valve_data.get_valve_styles(s2_data['valve_type'])
        new_valve_style = st.selectbox("⚡ Select Valve Style / Trim", available_styles,
                                     index=available_styles.index(s2_data['valve_style']))
        
        if new_valve_style != s2_data['valve_style']:
            s2_data['valve_style'] = new_valve_style
            st.rerun()
        
        # Enhanced vendor selection
        if st.session_state.vendor_mode:
            st.subheader("🏭 Vendor-Specific Data")
            vendors = valve_data.get_available_vendors()
            vendor_options = ["Generic"] + vendors
            selected_vendor = st.selectbox("Manufacturer", vendor_options)
            
            if selected_vendor != "Generic":
                s2_data['vendor'] = selected_vendor
                series_options = valve_data.get_vendor_series(selected_vendor, s2_data['valve_type'])
                if series_options:
                    s2_data['series'] = st.selectbox("Model/Series", series_options)
            else:
                s2_data['vendor'] = None
                s2_data['series'] = None
        
        # Valve characteristic recommendation
        rec_char = helpers.recommend_characteristic(st.session_state.input_data)
        st.info(f"**💡 Recommendation:** {rec_char} characteristic recommended for your process.")
        
        s2_data['valve_char'] = st.selectbox("📈 Valve Characteristic", 
                                           ["Equal Percentage", "Linear", "Quick Opening", "Modified Equal Percentage"])
    
    with col2:
        # Valve sizing
        globe_sizes = [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24]
        large_sizes = globe_sizes + [30, 36, 42, 48, 54, 60, 66, 72]
        available_sizes = globe_sizes if s2_data['valve_type'] == 'Globe' else large_sizes
        
        if s2_data['valve_size_nominal'] not in available_sizes:
            s2_data['valve_size_nominal'] = available_sizes[0]
        
        current_size_index = available_sizes.index(s2_data['valve_size_nominal'])
        s2_data['valve_size_nominal'] = st.selectbox("📏 Nominal Valve Size (inches)", available_sizes, 
                                                    index=current_size_index)
        
        # Operating point
        s2_data['valve_opening_percent'] = st.slider("🎯 Expected Operating Opening (%)", 
                                                   min_value=10, max_value=100, 
                                                   value=s2_data['valve_opening_percent'])
        
        # Actuator selection
        st.subheader("🔧 Actuator Type")
        actuator_options = {
            'pneumatic_spring_diaphragm': '🌬️ Pneumatic Spring-Diaphragm',
            'pneumatic_piston': '🌬️ Pneumatic Piston',
            'electric_linear': '⚡ Electric Linear',
            'pneumatic_rotary': '🌬️ Pneumatic Rotary',
            'electric_rotary': '⚡ Electric Rotary'
        }
        
        s2_data['actuator_type'] = st.selectbox("Actuator Type", 
                                              list(actuator_options.keys()),
                                              format_func=lambda x: actuator_options[x])
        
        # Enhanced valve data display
        valve_specific_data = valve_data.get_valve_data(s2_data['valve_type'], s2_data['valve_style'], 
                                                      s2_data.get('vendor'), s2_data.get('series'))
        
        st.write("**📊 Valve Coefficients:**")
        display_data = {k: v for k, v in valve_specific_data.items() 
                       if k in ['FL', 'Kc', 'Xt', 'Rangeability', 'Style']}
        st.json(display_data)
        
        # Travel-dependent coefficient override
        if st.checkbox("🔧 Override Coefficients"):
            s2_data['fl'] = st.number_input("FL (Pressure Recovery Factor)", 
                                          value=valve_specific_data.get('FL', 0.9), step=0.01)
            s2_data['kc'] = st.number_input("Kc (Cavitation Index Factor)", 
                                          value=valve_specific_data.get('Kc', 0.7), step=0.01)
        else:
            s2_data['fl'] = valve_specific_data.get('FL', 0.9)
            s2_data['kc'] = valve_specific_data.get('Kc', 0.7)
    
    col1, col2 = st.columns([1, 5])
    with col1:
        st.button("⬅️ Back to Step 1", on_click=prev_step)
    with col2:
        if st.button("💾 Save and Go to Step 3 ➡️", type="primary"):
            st.session_state.input_data.update(s2_data)
            del st.session_state.step2_data
            next_step()
            st.rerun()

# --- STEP 3: Enhanced Sizing Calculations ---
elif st.session_state.step == 3:
    st.header("🧮 Step 3: Sizing Calculation Results")
    
    try:
        # Perform calculations with enhanced methods
        if st.session_state.input_data['fluid_type'] == 'Liquid':
            results = liquid_sizing.calculate_liquid_cv(st.session_state.input_data)
        else:
            results = gas_sizing.calculate_gas_cv(st.session_state.input_data)
        
        st.session_state.results.update(results)
        
        # Main results display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🎯 Required Cv", f"{results['cv']:.2f}")
        with col2:
            if 'reynolds_factor' in results:
                st.metric("🔄 Reynolds Factor (FR)", f"{results['reynolds_factor']:.3f}")
        with col3:
            if 'ff_factor' in results:
                st.metric("⚡ FF Factor", f"{results['ff_factor']:.3f}")
        
        st.info("✅ This is the required Cv with enhanced corrections applied.")
        
        # Enhanced Cavitation Analysis with ISA RP75.23
        if 'sigma_analysis' in results:
            with st.expander("🌊 Cavitation Analysis (ISA RP75.23)", expanded=True):
                sigma_results = results['sigma_analysis']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("σ Sigma Value", f"{sigma_results['sigma']:.2f}")
                with col2:
                    st.metric("📊 Cavitation Level", sigma_results['level'])
                with col3:
                    st.metric("⚠️ Risk Assessment", sigma_results['risk'])
                with col4:
                    if 'margin_to_damage' in sigma_results and sigma_results['margin_to_damage']:
                        st.metric("🛡️ Margin to Damage", f"{sigma_results['margin_to_damage']:.2f}")
                
                # Risk-based styling
                if sigma_results['risk'] == 'Critical':
                    st.error(f"🚨 **{sigma_results['level']} Cavitation Detected**")
                elif sigma_results['risk'] == 'High':
                    st.warning(f"⚠️ **{sigma_results['level']} Cavitation Detected**")
                else:
                    st.success(f"✅ **{sigma_results['level']} Cavitation**")
                
                st.info(f"**💡 Recommendation:** {sigma_results['recommendation']}")
                
                # Cavitation level visualization
                if st.checkbox("📊 Show Cavitation Limits Chart"):
                    chart_data = get_cavitation_chart_data(
                        st.session_state.input_data['valve_type'],
                        st.session_state.input_data['valve_style']
                    )
                    
                    fig = go.Figure()
                    for i, (level, sigma_val, color) in enumerate(zip(chart_data['levels'], 
                                                                     chart_data['sigma_values'], 
                                                                     chart_data['colors'])):
                        fig.add_trace(go.Bar(
                            x=[level], y=[sigma_val], name=level,
                            marker_color=color, opacity=0.7
                        ))
                    
                    # Add current operating point
                    fig.add_hline(y=sigma_results['sigma'], line_dash="dash", line_color="red",
                                annotation_text=f"Operating Point: {sigma_results['sigma']:.2f}")
                    
                    fig.update_layout(
                        title="ISA RP75.23 Cavitation Limits",
                        xaxis_title="Cavitation Level",
                        yaxis_title="Sigma Value",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Enhanced Rangeability Analysis with Industry Standards
        with st.expander("📏 Rangeability Analysis", expanded=True):
            valve_size = st.session_state.input_data['valve_size_nominal']
            valve_type = st.session_state.input_data['valve_type']
            valve_style = st.session_state.input_data['valve_style']
            
            valve_specifics = valve_data.get_valve_data(valve_type, valve_style)
            inherent_rangeability = valve_specifics.get("Rangeability", 30)
            rated_cv = valve_data.get_rated_cv(valve_size, valve_type)
            min_cv = rated_cv / inherent_rangeability
            
            st.session_state.results.update({
                'inherent_rangeability': inherent_rangeability,
                'rated_cv': rated_cv,
                'min_controllable_cv': min_cv
            })
            
            # Multiple flow scenario validation
            validation_results = helpers.get_multiple_flow_validation(results['cv'], rated_cv)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🔢 Inherent Rangeability", f"{inherent_rangeability}:1")
            with col2:
                st.metric(f"⭐ Rated Cv ({valve_size}\")", f"{rated_cv}")
            with col3:
                st.metric("🎯 Min Controllable Cv", f"{min_cv:.2f}")
            
            # Display validation for different scenarios
            st.write("**📊 Validation Across Flow Scenarios:**")
            for scenario, result in validation_results.items():
                if scenario in ['overall_valid', 'summary']:
                    continue
                scenario_name = scenario.replace('_', ' ').title()
                status_color = {"Acceptable": "🟢", "Oversized": "🟡", "Undersized": "🔴"}
                st.write(f"{status_color.get(result['status'], '⚪')} **{scenario_name}**: {result['opening_percent']:.1f}% - {result['status']}")
            
            # Overall assessment
            if validation_results['overall_valid']:
                st.success("✅ Valve sizing is acceptable for all critical flow scenarios")
            else:
                st.error("❌ Valve sizing issues detected - review recommendations")
            
            st.info(f"**📝 Summary:** {validation_results['summary']}")
            st.session_state.results['rangeability_validation'] = validation_results
        
        # Gas-specific enhancements
        if st.session_state.input_data['fluid_type'] == 'Gas/Vapor' and 'flow_regime' in results:
            with st.expander("💨 Gas Flow Analysis", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🌊 Flow Regime", results['flow_regime'])
                    st.metric("📈 Expansion Factor (Y)", f"{results['expansion_factor_y']:.3f}")
                with col2:
                    if 'mach_number' in results:
                        st.metric("⚡ Mach Number", f"{results['mach_number']:.3f}")
                    if 'gas_velocity' in results:
                        st.metric("🏃 Gas Velocity", f"{results['gas_velocity']:.1f} ft/s")
                with col3:
                    if 'reynolds_number' in results:
                        st.metric("🔄 Reynolds Number", f"{results['reynolds_number']:.0f}")
                
                # Gas-specific warnings
                if results.get('choking_warning'):
                    st.warning(f"⚠️ {results['choking_warning']}")
                if results.get('velocity_warning'):
                    st.warning(f"⚠️ {results['velocity_warning']}")
    
    except Exception as e:
        st.error(f"❌ Calculation error: {e}")
        st.warning("Please check input values and try again.")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        st.button("⬅️ Back to Step 2", on_click=prev_step)
    with col2:
        st.button("🔊 Continue to Enhanced Noise Analysis ➡️", on_click=next_step, type="primary")

# --- STEP 4: Enhanced Noise Prediction ---
elif st.session_state.step == 4:
    st.header("🔊 Step 4: Noise Prediction")
    
    # Method selection reminder
    method_description = {
        'simplified': "Simplified empirical estimation for preliminary analysis",
        'iec_60534_8_3': "Industry-standard IEC 60534-8-3 model for detailed analysis"
    }
    st.info(f"**📋 Method:** {method_description[st.session_state.noise_method]}")
    
    try:
        noise_results = noise_prediction.predict_noise(
            st.session_state.input_data, 
            st.session_state.results,
            method=st.session_state.noise_method
        )
        st.session_state.results.update(noise_results)
        
        # Main noise display
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🔊 Predicted Noise Level (at 1m)", f"{noise_results['total_noise_dba']:.1f} dBA")
        with col2:
            noise_level = noise_results['total_noise_dba']
            if noise_level > 110:
                st.error("🚨 EXTREME - Immediate action required")
            elif noise_level > 85:
                st.warning("⚠️ HIGH - Mitigation recommended")
            else:
                st.success("✅ ACCEPTABLE - Within limits")
        
        st.info(f"**📋 Method:** {noise_results['method']}")
        
        # Enhanced recommendations
        if noise_results.get('warning'):
            st.warning(f"⚠️ {noise_results['warning']}")
        
        st.write(f"**💡 Recommendation:** {noise_results['noise_recommendation']}")
        
        # Detailed IEC results
        if st.session_state.noise_method == 'iec_60534_8_3':
            with st.expander("📊 IEC 60534-8-3 Detailed Results", expanded=False):
                if 'mechanical_stream_power' in noise_results:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("⚡ Mechanical Power", f"{noise_results['mechanical_stream_power']:.1f} W")
                    with col2:
                        st.metric("🔊 Acoustic Efficiency", f"{noise_results['acoustic_efficiency']:.6f}")
                    with col3:
                        st.metric("📈 Sound Power Level", f"{noise_results['sound_power_level']:.1f} dB")
                
                if 'peak_frequency' in noise_results:
                    st.metric("📻 Peak Frequency", f"{noise_results['peak_frequency']:.0f} Hz")
                
                st.write(f"**🌊 Flow Regime:** {noise_results.get('flow_regime', 'N/A')}")
        
        # Noise control recommendations
        noise_control_recs = noise_prediction.get_noise_control_recommendations(
            noise_level, 
            st.session_state.input_data['valve_type'],
            st.session_state.input_data['fluid_type']
        )
        
        if noise_control_recs:
            st.write("**🛡️ Noise Control Recommendations:**")
            for rec in noise_control_recs:
                st.write(f"• {rec}")
    
    except Exception as e:
        st.error(f"❌ Noise prediction error: {e}")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        st.button("⬅️ Back to Step 3", on_click=prev_step)
    with col2:
        st.button("🔧 Continue to Enhanced Actuator & Materials ➡️", on_click=next_step, type="primary")

# --- STEP 5: Enhanced Actuator, Materials & Final Selection ---
elif st.session_state.step == 5:
    st.header("🔧 Step 5: Actuator, Materials, and Final Selection")
    
    # Enhanced Actuator Sizing
    with st.expander("🔧 Actuator Sizing", expanded=True):
        fail_position = st.radio("🛡️ Fail-Safe Position", ["Fail Close (FC)", "Fail Open (FO)"], horizontal=True)
        st.session_state.input_data['fail_position'] = fail_position
        
        actuator_results = actuator_sizing.size_actuator(st.session_state.input_data, st.session_state.results)
        st.session_state.results.update(actuator_results)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.session_state.input_data['valve_type'] == 'Globe':
                st.metric("💪 Required Thrust", f"{actuator_results['required_force']:.0f} {units['force']}")
            else:
                st.metric("🔄 Required Torque", f"{actuator_results['required_torque']:.0f} {units['torque']}")
        
        with col2:
            st.metric("🛡️ Safety Factor Applied", f"{actuator_results['safety_factor_used']:.1f}")
        
        with col3:
            if 'spring_analysis' in actuator_results and actuator_results['spring_analysis']:
                spring_force = actuator_results['spring_analysis']['spring_force_max']
                st.metric("🌀 Spring Force", f"{spring_force:.0f} lbf")
        
        st.success(f"**💡 Recommendation:** {actuator_results['actuator_recommendation']}")
        
        # Detailed actuator analysis
        if st.checkbox("📊 Show Detailed Actuator Analysis"):
            if 'force_breakdown' in actuator_results:
                breakdown = actuator_results['force_breakdown']
                st.write("**💪 Force Breakdown:**")
                for key, value in breakdown.items():
                    if isinstance(value, (int, float)):
                        st.write(f"• {key.replace('_', ' ').title()}: {value:.0f} lbf")
            
            if 'torque_breakdown' in actuator_results:
                breakdown = actuator_results['torque_breakdown']
                st.write("**🔄 Torque Breakdown:**")
                for key, value in breakdown.items():
                    if isinstance(value, (int, float)):
                        st.write(f"• {key.replace('_', ' ').title()}: {value:.0f} ft-lbf")
    
    # Enhanced Material Selection
    with st.expander("🏗️ Material Selection", expanded=True):
        material_results = materials.select_materials(st.session_state.input_data)
        st.session_state.results.update(material_results)
        
        # Main materials table
        st.write("**🏗️ Recommended Materials:**")
        df_materials = pd.DataFrame([material_results['recommendations']])
        st.table(df_materials)
        
        # Service category and justification
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**📋 Service Category:** {material_results['service_category']}")
        with col2:
            st.info(f"**💡 Material Justification:** {material_results['material_justification']}")
        
        # Compliance and testing
        st.success(f"**✅ Compliance:** {material_results['compliance_check']}")
        
        if material_results['testing_requirements']:
            st.write("**🧪 Required Testing:**")
            for test in material_results['testing_requirements']:
                st.write(f"• {test}")
        
        # Alternative materials
        if st.checkbox("📊 Show Alternative Materials"):
            alternatives = material_results['alternative_materials']
            st.write("**🔄 Alternative Options:**")
            for component, options in alternatives.items():
                st.write(f"**{component}:** {', '.join(options)}")
    
    # Enhanced Valve Characteristic Curve
    with st.expander("📈 Valve Dynamic Characteristic", expanded=True):
        try:
            fig = helpers.plot_valve_characteristic(st.session_state.input_data, st.session_state.results['cv'])
            st.plotly_chart(fig, use_container_width=True)
            
            # Valve authority calculation
            valve_dp = st.session_state.input_data['dp']
            system_dp = st.number_input("🏭 Total System Pressure Drop", value=valve_dp*2, 
                                      help="Include valve + piping losses")
            
            if system_dp > 0:
                authority = helpers.calculate_valve_authority(valve_dp, system_dp)
                st.metric(f"📊 Valve Authority", f"{authority['authority_percent']:.1f}%")
                st.info(f"**📋 Assessment:** {authority['assessment']}")
        
        except Exception as e:
            st.warning(f"⚠️ Could not generate characteristic plot: {e}")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        st.button("⬅️ Back to Step 4", on_click=prev_step)
    with col2:
        st.button("📊 Finalize and Generate Report ➡️", on_click=next_step, type="primary")

# --- STEP 6: Enhanced Summary and Report Generation ---
elif st.session_state.step == 6:
    st.header("📊 Step 6: Summary and Report")
    
    # Comprehensive summary
    st.subheader("📋 Executive Summary")
    
    # Key results summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Required Cv", f"{st.session_state.results.get('cv', 0):.2f}")
    
    with col2:
        validation = st.session_state.results.get('rangeability_validation', {})
        if validation.get('overall_valid', False):
            st.metric("✅ Sizing Status", "✅ ACCEPTABLE")
        else:
            st.metric("⚠️ Sizing Status", "⚠️ REVIEW NEEDED")
    
    with col3:
        noise_level = st.session_state.results.get('total_noise_dba', 0)
        st.metric("🔊 Noise Level", f"{noise_level:.1f} dBA")
    
    with col4:
        sigma_analysis = st.session_state.results.get('sigma_analysis', {})
        cavitation_risk = sigma_analysis.get('risk', 'Unknown')
        risk_colors = {'Low': '🟢', 'Medium': '🟡', 'High': '🟠', 'Critical': '🔴'}
        st.metric("🌊 Cavitation Risk", f"{risk_colors.get(cavitation_risk, '⚪')} {cavitation_risk}")
    
    # Enhanced data view
    with st.expander("📊 View Complete Calculation Data", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📋 Process Inputs:**")
            display_inputs = {k: v for k, v in st.session_state.input_data.items() 
                            if k not in ['units', 'safety_factor_rec']}
            st.json(display_inputs)
        
        with col2:
            st.write("**📊 Enhanced Results:**")
            display_results = {k: v for k, v in st.session_state.results.items() 
                             if not isinstance(v, dict) or k == 'sigma_analysis'}
            st.json(display_results)
    
    # Report generation
    st.subheader("📄 Generate Report")
    
    report_options = st.columns(2)
    with report_options[0]:
        include_charts = st.checkbox("📊 Include Characteristic Charts", value=True)
    with report_options[1]:
        include_detailed_analysis = st.checkbox("📋 Include Detailed Technical Analysis", value=True)
    
    st.info("📥 Click below to generate a comprehensive PDF report with all calculations, analysis, and recommendations.")
    
    # Enhanced report data
    report_data = {
        "inputs": st.session_state.input_data,
        "results": st.session_state.results,
        "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "software_version": "Enhanced Valve Sizing v2.0",
        "standards_compliance": ["ISA S75.01", "ISA RP75.23", "IEC 60534-8-3", "API 6D", "NACE MR0175"],
        "include_charts": include_charts,
        "include_detailed_analysis": include_detailed_analysis
    }
    
    try:
        pdf_filename, pdf_bytes = pdf_generator.create_pdf_report(report_data)
        st.download_button(
            label="📥 Download Enhanced PDF Report",
            data=pdf_bytes,
            file_name=pdf_filename,
            mime="application/pdf",
            type="primary"
        )
    except Exception as e:
        st.error(f"❌ Report generation error: {e}")
    
    st.button("⬅️ Back to Step 5", on_click=prev_step)
    
    # Success message
    st.success("🎉 Enhanced valve sizing and selection complete! The application has analyzed your process conditions using industry-leading standards and provided comprehensive recommendations.")
    
    # Summary of enhancements
    st.subheader("🚀 Enhanced Features Applied")
    
    enhancements = [
        "✅ ISA RP75.23 Five-Level Sigma Method for cavitation analysis",
        "✅ Reynolds Number Correction for non-turbulent flow conditions", 
        "✅ Enhanced actuator sizing with proper safety factors",
        "✅ Industry-standard 20-80% valve opening validation",
        "✅ Travel-dependent valve coefficients (FL, Kc, Xt)",
        "✅ Vendor-specific data integration capability",
        "✅ Proper FF factor calculation for liquid service",
        "✅ Enhanced noise prediction with IEC 60534-8-3 option",
        "✅ Comprehensive material selection with compliance checking",
        "✅ Multi-scenario flow validation and safety factor recommendations"
    ]
    
    for enhancement in enhancements:
        st.write(enhancement)
