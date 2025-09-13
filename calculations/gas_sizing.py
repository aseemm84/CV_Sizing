import numpy as np
from utils.unit_converters import convert_pressure, convert_flow_gas, convert_temperature
from data import valve_data

def calculate_gas_cv(data):
    """
    Enhanced gas/vapor Cv calculation with improved accuracy
    Follows ISA S75.01 / IEC 60534-2-1 standards with enhancements
    """
    # Convert to consistent units (Imperial for Cv calculation)
    p1_abs = convert_pressure(data['p1'], data['unit_system'], 'psia')
    p2_abs = convert_pressure(data['p2'], data['unit_system'], 'psia')
    t1_abs = convert_temperature(data['t1'], data['unit_system'], 'R')  # Rankine
    flow_rate_scfh = convert_flow_gas(data['flow_rate'], data['unit_system'], 'scfh')

    mw = data['mw']
    k = data['k']
    z = data['z']

    # Get valve-specific Xt from data file
    valve_specifics = valve_data.get_valve_data(data['valve_type'], data['valve_style'])
    xt = valve_specifics.get('Xt', 0.75)

    # Apply travel-dependent Xt if available
    valve_opening = data.get('valve_opening_percent', 70)
    if 'Xt_curve' in valve_specifics:
        xt = valve_data.interpolate_coefficient_curve(valve_opening, valve_specifics['Xt_curve'])

    # Enhanced specific heat ratio factor
    fk = k / 1.40

    # Pressure drop ratio
    x = (p1_abs - p2_abs) / p1_abs

    # Critical pressure drop ratio (choked flow condition)
    x_choked = xt * fk

    # Flow regime determination
    if x >= x_choked:
        x_sizing = x_choked
        is_choked = True
        flow_regime = "Choked (Critical)"
    else:
        x_sizing = x
        is_choked = False
        flow_regime = "Subsonic"

    # Enhanced expansion factor Y calculation
    if x_sizing > 0:
        y = 1 - (x_sizing / (3 * fk * xt))
        y = max(0.1, min(1.0, y))  # Bounds check
    else:
        y = 1.0

    # Calculate Cv using enhanced formula
    # Standard formula: Cv = W / (1360 * Y * P1 * sqrt(x / (MW * T1 * Z)))
    # where W is mass flow rate (lb/hr)

    # Convert volumetric flow to mass flow
    # At standard conditions: 1 scf = MW/379.3 lb for ideal gas
    mass_flow_rate = flow_rate_scfh * mw / 379.3  # lb/hr

    # Calculate denominator
    denominator = 1360 * y * p1_abs * np.sqrt(x_sizing / (mw * t1_abs * z))

    if denominator == 0:
        raise ValueError("Calculation error: denominator is zero. Check inputs.")

    cv = mass_flow_rate / denominator

    # Additional gas flow parameters
    # Sonic velocity at inlet conditions
    sonic_velocity = np.sqrt(k * 1544 * t1_abs / mw)  # ft/s

    # Actual gas velocity through valve (approximate)
    if cv > 0:
        valve_area = cv / 20  # Approximate valve area (in²) based on Cv
        gas_velocity = flow_rate_scfh / (valve_area * 3600)  # ft/s (very approximate)
        mach_number = gas_velocity / sonic_velocity
    else:
        gas_velocity = 0
        mach_number = 0

    # Reynolds number for gas flow
    gas_density = (p1_abs * mw) / (10.73 * t1_abs)  # lb/ft³
    gas_viscosity = data.get('gas_viscosity', 0.018)  # Default air viscosity (cP)

    if cv > 0:
        # Approximate Reynolds number calculation
        characteristic_length = np.sqrt(cv / 30)  # inches
        reynolds_number = (gas_density * gas_velocity * characteristic_length) / (gas_viscosity * 6.72e-4)
    else:
        reynolds_number = 0

    # Choking analysis
    if is_choked:
        choked_mass_flow = calculate_choked_mass_flow(p1_abs, t1_abs, mw, k, xt, valve_specifics)
        choking_warning = "Flow is choked. Valve cannot pass more flow regardless of further pressure drop."
    else:
        choked_mass_flow = None
        choking_warning = None

    # Gas-specific recommendations
    if mach_number > 0.3:
        velocity_warning = f"High gas velocity (Mach {mach_number:.2f}). Consider larger valve or multi-stage design."
    else:
        velocity_warning = None

    return {
        "cv": cv,
        "is_choked": is_choked,
        "expansion_factor_y": y,
        "pressure_drop_ratio_x": x,
        "choked_pressure_drop_ratio": x_choked,
        "flow_regime": flow_regime,
        "mass_flow_rate": mass_flow_rate,
        "sonic_velocity": sonic_velocity,
        "gas_velocity": gas_velocity,
        "mach_number": mach_number,
        "reynolds_number": reynolds_number,
        "gas_density": gas_density,
        "choked_mass_flow": choked_mass_flow,
        "choking_warning": choking_warning,
        "velocity_warning": velocity_warning,
        "valve_opening_used": valve_opening,
        "xt_used": xt
    }

def calculate_choked_mass_flow(p1, t1, mw, k, xt, valve_data):
    """
    Calculate maximum (choked) mass flow rate through valve

    Args:
        p1: Inlet pressure (psia)
        t1: Inlet temperature (°R)
        mw: Molecular weight
        k: Specific heat ratio
        xt: Terminal pressure drop ratio factor
        valve_data: Valve characteristics

    Returns:
        Maximum mass flow rate (lb/hr)
    """
    # Critical pressure ratio
    pr_critical = (2 / (k + 1)) ** (k / (k - 1))

    # Choked mass flow coefficient
    c_choked = np.sqrt(k * (2 / (k + 1)) ** ((k + 1) / (k - 1)))

    # This is a simplified calculation - full implementation would require
    # valve-specific flow coefficients and detailed geometry
    # For now, return approximate choked flow based on critical conditions

    choked_flow_factor = xt * c_choked
    return choked_flow_factor * p1 * np.sqrt(mw / t1)

def calculate_gas_pressure_recovery(p1, p2, pv, k, xt):
    """
    Calculate pressure recovery characteristics for gas flow

    Args:
        p1: Inlet pressure
        p2: Outlet pressure  
        pv: Vapor pressure (not applicable for gases, use 0)
        k: Specific heat ratio
        xt: Terminal pressure drop ratio factor

    Returns:
        Pressure recovery analysis
    """
    x = (p1 - p2) / p1
    x_critical = xt * (k / 1.4)

    if x >= x_critical:
        recovery_status = "No pressure recovery - choked flow"
        vena_contracta_pressure = p1 * (1 - x_critical)
    else:
        recovery_ratio = 1 - (x / x_critical)
        vena_contracta_pressure = p2 + (p1 - p2) * recovery_ratio
        recovery_status = f"Partial pressure recovery - {recovery_ratio*100:.1f}%"

    return {
        "recovery_status": recovery_status,
        "vena_contracta_pressure": vena_contracta_pressure,
        "pressure_recovery_ratio": recovery_ratio if x < x_critical else 0,
        "critical_pressure_ratio": x_critical
    }

def validate_gas_flow_conditions(data, results):
    """
    Validate gas flow conditions and provide warnings

    Args:
        data: Input process data
        results: Calculation results

    Returns:
        Validation results and recommendations
    """
    warnings = []
    recommendations = []

    # Check for high Mach number
    mach = results.get('mach_number', 0)
    if mach > 0.7:
        warnings.append("Extremely high gas velocity - significant pressure losses expected")
        recommendations.append("Consider multi-stage pressure reduction or larger valve")
    elif mach > 0.3:
        warnings.append("High gas velocity may cause additional pressure losses")
        recommendations.append("Verify downstream piping design for high velocity")

    # Check for choked flow
    if results.get('is_choked'):
        warnings.append("Flow is choked - valve cannot handle flow increases")
        recommendations.append("Use choked flow conditions for safety calculations")

    # Check Reynolds number
    re = results.get('reynolds_number', 0)
    if re < 10000:
        warnings.append("Low Reynolds number - flow may not be fully turbulent")
        recommendations.append("Consider viscosity effects on valve performance")

    # Check temperature limits
    temp = data.get('t1', 20)
    if temp < -50:
        warnings.append("Very low temperature - material selection critical")
        recommendations.append("Verify low-temperature material compatibility")
    elif temp > 500:
        warnings.append("High temperature service - thermal effects important")
        recommendations.append("Consider thermal expansion and high-temp materials")

    # Check pressure ratio
    p1 = data.get('p1', 1)
    p2 = data.get('p2', 1)
    if p1 / p2 > 10:
        warnings.append("Very high pressure ratio - consider multi-stage design")
        recommendations.append("Multi-stage valve recommended for pressure ratios > 10:1")

    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "recommendations": recommendations,
        "overall_assessment": "Acceptable" if len(warnings) == 0 else "Caution Required"
    }
