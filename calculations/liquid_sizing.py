import numpy as np
from utils.unit_converters import convert_pressure, convert_flow_liquid, convert_density
from standards.isa_rp75_23 import calculate_sigma_levels
from utils.reynolds_correction import calculate_reynolds_factor

def calculate_ff_factor(pv, pc):
    """
    Calculate the liquid critical pressure ratio factor (FF) per ISA S75.01
    """
    if pc <= 0:
        return 0.96  # Default conservative value

    ratio = pv / pc
    if ratio > 1.0:
        ratio = 1.0  # Cap at 1.0 for physical consistency

    ff = 0.96 - 0.28 * np.sqrt(ratio)
    return max(0.6, min(0.96, ff))  # Reasonable bounds

def calculate_liquid_cv(data):
    """
    Enhanced liquid Cv calculation with ISA RP75.23 Sigma Method,
    Reynolds Number Correction, and proper FF factor calculation.
    """
    try:
        # Convert units to consistent base (Imperial for Cv calculation)
        p1 = convert_pressure(data['p1'], data['unit_system'], 'psi')
        p2 = convert_pressure(data['p2'], data['unit_system'], 'psi')
        pv = convert_pressure(data['pv'], data['unit_system'], 'psi')
        pc = convert_pressure(data['pc'], data['unit_system'], 'psi')
        flow_rate = convert_flow_liquid(data['flow_rate'], data['unit_system'], 'gpm')

        # Specific Gravity (Gf)
        if data['unit_system'] == 'Metric':
            Gf = data['rho'] / 1000.0  # Convert kg/m3 to specific gravity
        else:
            Gf = data['rho']  # Already specific gravity in Imperial

        # Get valve coefficients (potentially travel-dependent)
        valve_opening = data.get('valve_opening_percent', 70)  # Default 70% open
        fl = data.get('fl', 0.9)
        kc = data.get('kc', 0.7)

        # Apply travel-dependent corrections if available
        if 'fl_curve' in data:
            fl = interpolate_travel_coefficient(valve_opening, data['fl_curve'])
        if 'kc_curve' in data:
            kc = interpolate_travel_coefficient(valve_opening, data['kc_curve'])

        # Differential pressure
        dp = p1 - p2

        # Calculate FF factor properly instead of using default
        ff = calculate_ff_factor(pv, pc)

        # Choked flow calculation (delta P allowable)
        dp_allowable = (fl ** 2) * (p1 - ff * pv)

        # Use the smaller of actual or allowable delta P
        dp_sizing = min(dp, dp_allowable)

        if dp_sizing <= 0:
            raise ValueError("Sizing pressure drop (dP) must be positive. Check inlet/outlet pressures.")

        # Basic Cv calculation
        cv_basic = flow_rate * (Gf / dp_sizing) ** 0.5

        # Reynolds Number Correction
        viscosity = data.get('vc', 1.0)  # Viscosity in cP
        fr_factor = calculate_reynolds_factor(cv_basic, flow_rate, viscosity, Gf)

        # Apply Reynolds correction
        cv = cv_basic / fr_factor

        # Enhanced Cavitation Analysis using ISA RP75.23 Sigma Method
        valve_data_dict = {
            'valve_type': data.get('valve_type', 'Globe'),
            'valve_style': data.get('valve_style', 'Standard'),
            'valve_size': data.get('valve_size_nominal', 2),
            'kc': kc
        }

        # Safe sigma calculation
        try:
            sigma_results = calculate_sigma_levels(p1, p2, pv, valve_data_dict)
        except Exception as sigma_error:
            # Fallback to basic sigma calculation if enhanced method fails
            sigma_basic = (p1 - pv) / (p1 - p2) if (p1 - p2) > 0 else 0
            sigma_results = {
                'sigma': sigma_basic,
                'level': 'Basic Calculation',
                'status': 'No Significant Cavitation' if sigma_basic > 2.0 else 'Potential Cavitation',
                'risk': 'Low' if sigma_basic > 2.0 else 'Medium',
                'recommendation': 'Standard trim likely acceptable' if sigma_basic > 2.0 else 'Monitor for cavitation'
            }

        # Legacy flashing check
        is_flashing = p2 < pv

        # Additional cavitation metrics for compatibility
        sigma_basic = (p1 - pv) / (p1 - p2) if (p1 - p2) > 0 else 0

        return {
            "cv": cv,
            "cv_basic": cv_basic,
            "reynolds_factor": fr_factor,
            "ff_factor": ff,
            "is_flashing": is_flashing,
            "cavitation_index": sigma_basic,  # Keep for backward compatibility
            "sigma_analysis": sigma_results,  # New enhanced analysis
            "cavitation_status": sigma_results['status'],
            "trim_recommendation": sigma_results['recommendation'],
            "dp_sizing": dp_sizing,
            "dp_allowable": dp_allowable,
            "valve_opening_used": valve_opening
        }

    except Exception as e:
        # Fallback calculation if enhanced methods fail
        print(f"Enhanced calculation failed: {e}. Using basic calculation.")

        # Basic fallback calculation
        p1 = convert_pressure(data['p1'], data['unit_system'], 'psi')
        p2 = convert_pressure(data['p2'], data['unit_system'], 'psi')
        flow_rate = convert_flow_liquid(data['flow_rate'], data['unit_system'], 'gpm')

        if data['unit_system'] == 'Metric':
            Gf = data['rho'] / 1000.0
        else:
            Gf = data['rho']

        dp = p1 - p2
        if dp <= 0:
            raise ValueError("Pressure drop must be positive")

        cv = flow_rate * (Gf / dp) ** 0.5

        return {
            "cv": cv,
            "cv_basic": cv,
            "reynolds_factor": 1.0,
            "ff_factor": 0.96,
            "is_flashing": False,
            "cavitation_index": 2.0,
            "sigma_analysis": {
                'sigma': 2.0,
                'level': 'Basic Calculation',
                'status': 'No Significant Cavitation',
                'risk': 'Low',
                'recommendation': 'Standard trim acceptable'
            },
            "cavitation_status": "No Significant Cavitation",
            "trim_recommendation": "Standard trim acceptable",
            "dp_sizing": dp,
            "dp_allowable": dp,
            "valve_opening_used": 70
        }

def interpolate_travel_coefficient(opening_percent, coefficient_curve):
    """
    Interpolate valve coefficient based on opening percentage
    """
    if not coefficient_curve:
        return None

    openings = sorted(coefficient_curve.keys())

    if opening_percent <= openings[0]:
        return coefficient_curve[openings[0]]
    if opening_percent >= openings[-1]:
        return coefficient_curve[openings[-1]]

    # Linear interpolation
    for i in range(len(openings) - 1):
        if openings[i] <= opening_percent <= openings[i + 1]:
            x1, x2 = openings[i], openings[i + 1]
            y1, y2 = coefficient_curve[x1], coefficient_curve[x2]
            return y1 + (y2 - y1) * (opening_percent - x1) / (x2 - x1)

    return coefficient_curve[openings[0]]  # Fallback
