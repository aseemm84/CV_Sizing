"""
Enhanced Actuator Sizing with Industry-Standard Safety Factors
Implements proper thrust/torque calculations with spring forces and safety considerations
"""
from utils.unit_converters import convert_pressure
import numpy as np

# Industry standard safety factors
SAFETY_FACTORS = {
    "pneumatic_spring_diaphragm": 1.5,
    "pneumatic_piston": 1.5,
    "electric_linear": 2.0,
    "pneumatic_rotary": 1.75,
    "electric_rotary": 2.0,
    "hydraulic": 1.3
}

# Typical spring rates for different actuator sizes (lbf/in)
SPRING_RATES = {
    # Size (in²): Spring rate (lbf/in)
    25: 150,    # Small diaphragm
    50: 300,    # Medium diaphragm  
    100: 600,   # Large diaphragm
    200: 1200,  # Extra large diaphragm
    400: 2400   # Industrial diaphragm
}

def calculate_globe_valve_forces(inputs, results):
    """
    Calculate forces for globe valve actuator sizing

    Args:
        inputs: Process and valve data
        results: Sizing calculation results

    Returns:
        Dictionary of force calculations
    """
    valve_size = inputs['valve_size_nominal']
    p1 = convert_pressure(inputs['p1'], inputs['unit_system'], 'psi')
    p2 = convert_pressure(inputs['p2'], inputs['unit_system'], 'psi')
    dp = p1 - p2

    # Valve geometry calculations
    seat_diameter = valve_size  # Simplified - actual seat diameter varies
    seat_area = np.pi * (seat_diameter / 2) ** 2  # in²

    # Stem diameter (typical values)
    stem_diameter_map = {1: 0.5, 2: 0.75, 3: 1.0, 4: 1.25, 6: 1.5, 8: 2.0}
    stem_diameter = stem_diameter_map.get(valve_size, 1.0)
    stem_area = np.pi * (stem_diameter / 2) ** 2

    # Force calculations
    # 1. Unbalanced force from process pressure
    unbalanced_force = seat_area * dp

    # 2. Stem force (pressure acting on stem area)
    stem_force = stem_area * p1

    # 3. Packing friction force (typically 10-20% of stem force)
    packing_friction = 0.15 * stem_force

    # 4. Seat load (for tight shutoff)
    seat_load = seat_area * 50  # Typical 50 psi seating stress

    # 5. Total operating force
    operating_force = unbalanced_force + stem_force + packing_friction

    # 6. Shutoff force (typically governing)
    shutoff_force = max(operating_force, seat_load)

    return {
        "seat_area": seat_area,
        "stem_area": stem_area,
        "unbalanced_force": unbalanced_force,
        "stem_force": stem_force,
        "packing_friction": packing_friction,
        "seat_load": seat_load,
        "operating_force": operating_force,
        "shutoff_force": shutoff_force,
        "governing_force": shutoff_force
    }

def calculate_rotary_valve_torque(inputs, results):
    """
    Calculate torque for rotary valve actuator sizing

    Args:
        inputs: Process and valve data
        results: Sizing calculation results

    Returns:
        Dictionary of torque calculations
    """
    valve_size = inputs['valve_size_nominal']
    valve_type = inputs['valve_type']
    p1 = convert_pressure(inputs['p1'], inputs['unit_system'], 'psi')
    dp = convert_pressure(inputs['dp'], inputs['unit_system'], 'psi')

    # Torque factors based on valve type and size
    if valve_type == 'Butterfly':
        # Butterfly valve torque factors (ft-lbf per psi differential per inch of valve size)
        torque_factor = 0.3 + (valve_size * 0.1)  # Increases with size
        breakaway_multiplier = 1.5  # Higher torque to break free
    else:  # Ball valve
        torque_factor = 0.5 + (valve_size * 0.15)
        breakaway_multiplier = 2.0

    # Basic operating torque
    operating_torque = torque_factor * dp * valve_size

    # Breakaway torque (to overcome static friction)
    breakaway_torque = operating_torque * breakaway_multiplier

    # Bearing friction (typically 10-25% of operating torque)
    bearing_friction = 0.2 * operating_torque

    # Total required torque
    total_torque = breakaway_torque + bearing_friction

    return {
        "torque_factor": torque_factor,
        "operating_torque": operating_torque,
        "breakaway_torque": breakaway_torque,
        "bearing_friction": bearing_friction,
        "total_torque": total_torque,
        "governing_torque": total_torque
    }

def calculate_spring_force(actuator_size, stroke, fail_position):
    """
    Calculate spring force for fail-safe operation

    Args:
        actuator_size: Effective area or torque rating
        stroke: Actuator stroke (inches or degrees)
        fail_position: "Fail Close" or "Fail Open"

    Returns:
        Spring force calculations
    """
    # Estimate spring rate based on actuator size
    spring_rate = None
    for size, rate in sorted(SPRING_RATES.items()):
        if actuator_size <= size:
            spring_rate = rate
            break

    if spring_rate is None:
        spring_rate = max(SPRING_RATES.values())  # Use largest for very big actuators

    # Spring force calculation
    spring_force_max = spring_rate * stroke
    spring_force_min = spring_force_max * 0.2  # Typical 20% preload

    # Available spring force (accounting for air pressure assist)
    if fail_position == "Fail Close (FC)":
        # Spring assists closing
        available_force = spring_force_max
    else:  # Fail Open
        # Spring opposes closing (reduces available force)
        available_force = -spring_force_max

    return {
        "spring_rate": spring_rate,
        "spring_force_max": spring_force_max,
        "spring_force_min": spring_force_min,
        "available_spring_force": available_force,
        "spring_energy": 0.5 * spring_rate * stroke ** 2
    }

def size_actuator(inputs, results):
    """
    Enhanced actuator sizing with proper safety factors and spring calculations

    Args:
        inputs: Process and valve data
        results: Sizing calculation results

    Returns:
        Complete actuator sizing results
    """
    valve_type = inputs['valve_type']
    valve_size = inputs['valve_size_nominal']
    fail_position = inputs.get('fail_position', 'Fail Close (FC)')
    actuator_type = inputs.get('actuator_type', 'pneumatic_spring_diaphragm')

    # Get safety factor
    safety_factor = SAFETY_FACTORS.get(actuator_type, 1.5)

    if valve_type == 'Globe':
        # Linear actuator for globe valve
        force_calcs = calculate_globe_valve_forces(inputs, results)
        required_force_basic = force_calcs['governing_force']

        # Spring force calculations
        stroke = valve_size * 0.25  # Typical stroke (inches)
        actuator_area = required_force_basic / 60  # Assume 60 psi supply pressure
        spring_calcs = calculate_spring_force(actuator_area, stroke, fail_position)

        # Net required force considering spring
        if fail_position == "Fail Close (FC)":
            net_force_required = required_force_basic - spring_calcs['available_spring_force']
        else:
            net_force_required = required_force_basic + abs(spring_calcs['available_spring_force'])

        # Apply safety factor
        required_force = max(net_force_required, required_force_basic) * safety_factor

        # Convert to Newtons if metric
        if inputs['unit_system'] == 'Metric':
            required_force *= 4.44822  # lbf to N
            force_unit = 'N'
        else:
            force_unit = 'lbf'

        # Actuator recommendation
        if actuator_type == 'pneumatic_spring_diaphragm':
            recommendation = f"Pneumatic spring-diaphragm actuator with minimum {required_force:.0f} {force_unit} thrust capacity. Effective area ≥ {required_force/87:.0f} cm² at 6 bar supply."
        elif actuator_type == 'pneumatic_piston':
            recommendation = f"Pneumatic piston actuator with minimum {required_force:.0f} {force_unit} thrust capacity."
        else:
            recommendation = f"Electric linear actuator with minimum {required_force:.0f} {force_unit} thrust capacity and {safety_factor:.1f} safety factor."

        return {
            "required_force": required_force,
            "required_torque": 0,
            "safety_factor_used": safety_factor,
            "actuator_recommendation": recommendation,
            "force_breakdown": force_calcs,
            "spring_analysis": spring_calcs,
            "net_force_required": net_force_required
        }

    else:
        # Rotary actuator for ball/butterfly valve
        torque_calcs = calculate_rotary_valve_torque(inputs, results)
        required_torque_basic = torque_calcs['governing_torque']

        # Apply safety factor
        required_torque = required_torque_basic * safety_factor

        # Convert to Nm if metric
        if inputs['unit_system'] == 'Metric':
            required_torque *= 1.35582  # ft-lbf to Nm
            torque_unit = 'Nm'
        else:
            torque_unit = 'ft-lbf'

        # Actuator recommendation
        if 'pneumatic' in actuator_type:
            recommendation = f"Pneumatic rack-and-pinion or vane actuator with minimum {required_torque:.0f} {torque_unit} output torque and {safety_factor:.1f} safety factor."
        else:
            recommendation = f"Electric rotary actuator with minimum {required_torque:.0f} {torque_unit} output torque and {safety_factor:.1f} safety factor."

        return {
            "required_force": 0,
            "required_torque": required_torque,
            "safety_factor_used": safety_factor,
            "actuator_recommendation": recommendation,
            "torque_breakdown": torque_calcs,
            "spring_analysis": None  # Not applicable for rotary
        }

def get_actuator_selection_guide():
    """
    Return actuator selection guidelines

    Returns:
        Dictionary of selection criteria
    """
    return {
        "pneumatic_spring_diaphragm": {
            "pros": ["Fail-safe operation", "Simple design", "Cost effective"],
            "cons": ["Limited thrust", "Slow response", "Supply pressure dependent"],
            "applications": ["General service", "Small to medium valves", "Fail-safe required"]
        },
        "pneumatic_piston": {
            "pros": ["High thrust", "Fast response", "Compact"],
            "cons": ["No inherent fail-safe", "Complex accessories needed"],
            "applications": ["High pressure service", "Fast control required"]
        },
        "electric_linear": {
            "pros": ["High precision", "No air supply needed", "Remote operation"],
            "cons": ["Higher cost", "Complex controls", "Power failure risk"],
            "applications": ["Precise control", "Remote locations", "Modulating service"]
        },
        "pneumatic_rotary": {
            "pros": ["High torque", "Fast operation", "Simple"],
            "cons": ["Supply pressure dependent", "Limited fail-safe options"],
            "applications": ["Ball/butterfly valves", "On-off service"]
        },
        "electric_rotary": {
            "pros": ["Precise positioning", "High torque", "Remote operation"],
            "cons": ["Higher cost", "Complex controls"],
            "applications": ["Precise modulating control", "High torque requirements"]
        }
    }
