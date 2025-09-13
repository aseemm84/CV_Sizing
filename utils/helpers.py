import plotly.graph_objects as go
import numpy as np

UNITS = {
    'Metric': {
        'pressure': 'bar',
        'temperature': '°C',
        'flow_liquid': 'm³/hr',
        'flow_gas': 'Nm³/hr',
        'density': 'kg/m³',
        'viscosity': 'cP',
        'force': 'N',
        'torque': 'Nm'
    },
    'Imperial': {
        'pressure': 'psi',
        'temperature': '°F',
        'flow_liquid': 'gpm',
        'flow_gas': 'scfh',
        'density': 'SG',
        'viscosity': 'cP',
        'force': 'lbf',
        'torque': 'ft-lbf'
    }
}

# Industry-standard valve opening recommendations
VALVE_OPENING_STANDARDS = {
    "normal": {"min": 20, "max": 80},  # Changed from "normal_operation"
    "design": {"min": 60, "max": 70},   # Changed from "design_point"
    "minimum": {"min": 20, "max": 30},  # Changed from "minimum_flow"
    "maximum": {"min": 90, "max": 95},  # Changed from "maximum_flow"
    "emergency": {"min": 95, "max": 100} # Changed from "emergency_flow"
}

def get_units(unit_system):
    return UNITS.get(unit_system, UNITS['Metric'])

def recommend_characteristic(data):
    """Enhanced valve characteristic recommendation"""
    p1 = data.get('p1', 1)
    dp = data.get('dp', 1)
    valve_type = data.get('valve_type', 'Globe')

    # Pressure drop ratio
    if p1 > 0:
        dp_ratio = dp / p1
    else:
        dp_ratio = 0.5  # Default assumption

    # Enhanced logic based on valve type and system characteristics
    if valve_type == 'Globe':
        if dp_ratio > 0.4:
            return "Equal Percentage"  # High dp ratio needs non-linear valve
        elif dp_ratio > 0.2:
            return "Modified Equal Percentage"
        else:
            return "Linear"
    elif valve_type in ['Ball (Segmented)', 'Ball']:
        # Ball valves typically have inherent equal percentage
        return "Equal Percentage"
    else:  # Butterfly
        if dp_ratio > 0.3:
            return "Equal Percentage"
        else:
            return "Linear"

def validate_valve_opening(calculated_cv, rated_cv, flow_scenario="normal"):
    """
    Validate valve opening against industry standards
    """
    if rated_cv <= 0:
        return {
            "valid": False,
            "opening_percent": 0,
            "status": "Invalid",
            "message": "Invalid rated Cv",
            "recommendation": "Check valve selection"
        }

    opening_percent = (calculated_cv / rated_cv) * 100

    # Get standards for the flow scenario - use simplified keys
    standards = VALVE_OPENING_STANDARDS.get(flow_scenario, VALVE_OPENING_STANDARDS["normal"])
    min_opening = standards["min"]
    max_opening = standards["max"]

    # Validation logic
    if opening_percent < min_opening:
        status = "Oversized"
        message = f"Valve opening {opening_percent:.1f}% is below recommended minimum {min_opening}%"
        recommendation = f"Consider smaller valve size. Poor control expected below {min_opening}% opening."
        valid = False
    elif opening_percent > max_opening:
        status = "Undersized"
        message = f"Valve opening {opening_percent:.1f}% exceeds recommended maximum {max_opening}%"
        recommendation = f"Select larger valve size. Valve cannot meet flow requirement above {max_opening}% opening."
        valid = False
    else:
        status = "Acceptable"
        message = f"Valve opening {opening_percent:.1f}% is within recommended range {min_opening}-{max_opening}%"
        recommendation = f"Good valve sizing. Operating point at {opening_percent:.1f}% provides good control."
        valid = True

    return {
        "valid": valid,
        "opening_percent": opening_percent,
        "status": status,
        "message": message,
        "recommendation": recommendation,
        "standards_used": f"{min_opening}-{max_opening}% for {flow_scenario} operation"
    }

def get_multiple_flow_validation(calculated_cv, rated_cv):
    """
    Validate valve against multiple flow scenarios
    """
    scenarios = {
        "minimum": calculated_cv * 0.3,    # 30% of normal flow
        "normal": calculated_cv,           # Design flow
        "design": calculated_cv * 1.1,     # 110% of normal (design margin)
        "maximum": calculated_cv * 1.25,   # 125% of normal flow
        "emergency": calculated_cv * 1.5   # 150% of normal (emergency case)
    }

    results = {}
    overall_valid = True

    for scenario, cv_required in scenarios.items():
        validation = validate_valve_opening(cv_required, rated_cv, scenario)
        results[scenario] = validation

        if not validation["valid"] and scenario in ["normal", "design"]:
            overall_valid = False  # Critical scenarios must be valid

    results["overall_valid"] = overall_valid
    results["summary"] = generate_validation_summary(results)

    return results

def generate_validation_summary(validation_results):
    """Generate summary of validation results"""
    critical_issues = []
    warnings = []
    acceptable = []

    for scenario, result in validation_results.items():
        if scenario in ["overall_valid", "summary"]:
            continue

        if result["status"] == "Undersized":
            critical_issues.append(f"{scenario}: {result['opening_percent']:.1f}%")
        elif result["status"] == "Oversized":
            warnings.append(f"{scenario}: {result['opening_percent']:.1f}%")
        else:
            acceptable.append(f"{scenario}: {result['opening_percent']:.1f}%")

    summary = []
    if critical_issues:
        summary.append(f"CRITICAL: Undersized for {', '.join(critical_issues)}")
    if warnings:
        summary.append(f"WARNING: Oversized for {', '.join(warnings)}")
    if acceptable:
        summary.append(f"ACCEPTABLE: {', '.join(acceptable)}")

    return "; ".join(summary) if summary else "No validation performed"

def plot_valve_characteristic(data, calculated_cv):
    """Enhanced valve characteristic plotting with opening validation"""
    try:
        valve_char = data.get('valve_char', 'Equal Percentage')
        valve_type = data.get('valve_type', 'Globe')
        valve_style = data.get('valve_style', 'Standard')
        rated_cv = data.get('rated_cv', calculated_cv * 2)

        travel = np.linspace(0, 100, 101)  # Percent open

        # Enhanced characteristic curves
        if valve_char == 'Linear':
            inherent_cv = (travel / 100) * rated_cv
        elif valve_char == 'Quick Opening':
            inherent_cv = np.sqrt(travel / 100) * rated_cv
        elif valve_char == 'Modified Equal Percentage':
            R = data.get('inherent_rangeability', 30)
            inherent_cv = rated_cv * (R ** ((travel / 100) - 1))
            inherent_cv = np.clip(inherent_cv, 0, rated_cv * 0.95)  # Limit to 95%
        else:  # Equal Percentage (default)
            R = data.get('inherent_rangeability', 50)
            inherent_cv = rated_cv * (R ** ((travel / 100) - 1))

        inherent_cv = np.clip(inherent_cv, 0, rated_cv)

        # Installed characteristic (more realistic system interaction)
        system_pressure_drop_ratio = data.get('system_dp_ratio', 0.5)  # Ratio of system to valve dp
        installed_cv = inherent_cv * (1 - system_pressure_drop_ratio * 0.3)  # Approximate interaction

        # Create enhanced plot
        fig = go.Figure()

        # Main characteristic curves
        fig.add_trace(go.Scatter(
            x=travel, y=inherent_cv,
            mode='lines',
            name='Inherent Characteristic',
            line=dict(color='blue', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=travel, y=installed_cv,
            mode='lines',
            name='Estimated Installed',
            line=dict(color='orange', dash='dash', width=2)
        ))

        # Operating point
        op_travel = (calculated_cv / rated_cv) * 100 if rated_cv > 0 else 0
        if 0 <= op_travel <= 100:
            fig.add_trace(go.Scatter(
                x=[op_travel], y=[calculated_cv],
                mode='markers+text',
                name='Operating Point',
                marker=dict(color='red', size=15, symbol='x'),
                text=[f'{op_travel:.1f}%'],
                textposition="top center"
            ))

        # Industry standard zones
        fig.add_vrect(x0=20, x1=80, fillcolor="green", opacity=0.1, 
                      annotation_text="Normal Operating Zone", annotation_position="top")
        fig.add_vrect(x0=60, x1=70, fillcolor="darkgreen", opacity=0.15,
                      annotation_text="Design Point", annotation_position="bottom")

        # Warning zones
        fig.add_vrect(x0=0, x1=20, fillcolor="orange", opacity=0.1,
                      annotation_text="Poor Control Zone", annotation_position="top")
        fig.add_vrect(x0=80, x1=100, fillcolor="red", opacity=0.1,
                      annotation_text="High Opening Zone", annotation_position="top")

        fig.update_layout(
            title=f'Valve Dynamic Characteristic Curve - {valve_type} {valve_style}',
            xaxis_title='Valve Travel (% Open)',
            yaxis_title='Flow Coefficient (Cv)',
            legend_title='Characteristic',
            template='plotly_white',
            height=500,
            showlegend=True
        )

        # Add validation annotation
        validation = validate_valve_opening(calculated_cv, rated_cv)
        fig.add_annotation(
            x=op_travel,
            y=calculated_cv * 1.1,
            text=f"Status: {validation['status']}",
            showarrow=True,
            arrowhead=2,
            bgcolor={"Acceptable": "lightgreen", "Oversized": "yellow", "Undersized": "lightcoral"}.get(validation['status'], "white")
        )

        return fig

    except Exception as e:
        # Create a simple fallback plot
        print(f"Enhanced plot failed: {e}. Creating basic plot.")

        fig = go.Figure()

        # Simple linear characteristic as fallback
        travel = np.linspace(0, 100, 101)
        rated_cv = calculated_cv * 2  # Simple estimate
        inherent_cv = (travel / 100) * rated_cv

        fig.add_trace(go.Scatter(
            x=travel, y=inherent_cv,
            mode='lines',
            name='Basic Characteristic',
            line=dict(color='blue', width=2)
        ))

        # Operating point
        op_travel = (calculated_cv / rated_cv) * 100
        fig.add_trace(go.Scatter(
            x=[op_travel], y=[calculated_cv],
            mode='markers',
            name='Operating Point',
            marker=dict(color='red', size=10, symbol='x')
        ))

        fig.update_layout(
            title='Basic Valve Characteristic Curve',
            xaxis_title='Valve Travel (% Open)',
            yaxis_title='Flow Coefficient (Cv)',
            template='plotly_white',
            height=400
        )

        return fig

def calculate_valve_authority(valve_dp, system_dp):
    """
    Calculate valve authority (N) = valve ΔP / total system ΔP
    """
    if system_dp <= 0:
        return {"authority": 0, "assessment": "Invalid system data"}

    authority = valve_dp / system_dp

    if authority >= 0.5:
        assessment = "Excellent - Good control throughout range"
    elif authority >= 0.3:
        assessment = "Good - Acceptable control characteristics"
    elif authority >= 0.2:
        assessment = "Fair - Some control degradation at low flows"
    else:
        assessment = "Poor - Significant control problems expected"

    return {
        "authority": authority,
        "authority_percent": authority * 100,
        "assessment": assessment,
        "recommendation": "Increase valve ΔP or reduce system losses" if authority < 0.3 else "Authority is adequate"
    }

def get_sizing_safety_factors():
    """Return recommended safety factors for different applications"""
    return {
        "general_service": {
            "factor": 1.1,
            "description": "General process applications with stable conditions"
        },
        "critical_service": {
            "factor": 1.25,
            "description": "Critical process control, safety systems"
        },
        "future_expansion": {
            "factor": 1.5,
            "description": "Allow for future plant expansion or modifications"
        },
        "uncertain_conditions": {
            "factor": 1.3,
            "description": "When process conditions are not well defined"
        },
        "emergency_service": {
            "factor": 2.0,
            "description": "Emergency shutdown or blowdown systems"
        }
    }

def recommend_safety_factor(service_type, process_criticality, future_expansion):
    """
    Recommend appropriate safety factor based on application
    """
    base_factor = 1.1  # Minimum safety factor

    # Service type adjustments
    service_factors = {
        "continuous": 0.0,
        "batch": 0.1,
        "emergency": 0.5,
        "safety": 0.8
    }

    # Criticality adjustments
    criticality_factors = {
        "low": 0.0,
        "medium": 0.1,
        "high": 0.2,
        "critical": 0.4
    }

    # Future expansion adjustments
    expansion_factors = {
        "none": 0.0,
        "moderate": 0.2,
        "significant": 0.4
    }

    total_factor = (base_factor + 
                   service_factors.get(service_type, 0.1) +
                   criticality_factors.get(process_criticality, 0.1) +
                   expansion_factors.get(future_expansion, 0.0))

    # Reasonable bounds
    total_factor = max(1.1, min(2.0, total_factor))

    justification = f"Base: {base_factor}, Service: +{service_factors.get(service_type, 0.1)}, Criticality: +{criticality_factors.get(process_criticality, 0.1)}, Expansion: +{expansion_factors.get(future_expansion, 0.0)}"

    return {
        "recommended_factor": round(total_factor, 2),
        "justification": justification,
        "category": "Conservative" if total_factor > 1.5 else "Moderate" if total_factor > 1.25 else "Standard"
    }
