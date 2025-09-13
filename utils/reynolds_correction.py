"""
Reynolds Number Correction for Control Valve Sizing
Implements FR factor calculation per IEC 60534-2-1 for non-turbulent flow
"""
import numpy as np

def calculate_valve_reynolds_number(cv, flow_rate, viscosity, specific_gravity):
    """
    Calculate valve Reynolds number for liquid flow

    Args:
        cv: Flow coefficient 
        flow_rate: Flow rate (gpm)
        viscosity: Kinematic viscosity (cP)
        specific_gravity: Fluid specific gravity

    Returns:
        Valve Reynolds number (Rev)
    """
    if cv <= 0 or viscosity <= 0:
        return 10000  # Assume turbulent if invalid inputs

    # Formula: Rev = 1360 * Q * SG / (Cv * μ)
    # Where Q is in gpm, μ is in cP, SG is specific gravity
    rev = 1360 * flow_rate * specific_gravity / (cv * viscosity)

    return max(0, rev)

def get_reynolds_factor_from_curve(rev):
    """
    Calculate FR factor using IEC 60534-2-1 curve data
    Based on the standard curve relating Rev to FR

    Args:
        rev: Valve Reynolds number

    Returns:
        Reynolds correction factor (FR)
    """
    # Standard curve data points from IEC 60534-2-1
    # These are typical values - in practice, use manufacturer-specific curves
    rev_points = [10, 20, 40, 60, 100, 200, 400, 600, 1000, 2000, 4000, 6000, 10000, 20000]
    fr_points = [0.15, 0.22, 0.35, 0.45, 0.60, 0.75, 0.85, 0.90, 0.95, 0.98, 0.99, 1.00, 1.00, 1.00]

    # If Rev >= 10,000, flow is fully turbulent
    if rev >= 10000:
        return 1.0

    # If Rev < 10, use minimum value
    if rev < 10:
        return 0.15

    # Interpolate between curve points
    return np.interp(rev, rev_points, fr_points)

def calculate_reynolds_factor(cv, flow_rate, viscosity, specific_gravity):
    """
    Main function to calculate Reynolds correction factor

    Args:
        cv: Flow coefficient (from basic calculation)
        flow_rate: Flow rate (gpm) 
        viscosity: Dynamic viscosity (cP)
        specific_gravity: Fluid specific gravity

    Returns:
        Reynolds correction factor (FR)
    """
    # Calculate valve Reynolds number
    rev = calculate_valve_reynolds_number(cv, flow_rate, viscosity, specific_gravity)

    # Get FR factor from standardized curve
    fr = get_reynolds_factor_from_curve(rev)

    return fr

def check_reynolds_regime(rev):
    """
    Determine flow regime based on Reynolds number

    Args:
        rev: Valve Reynolds number

    Returns:
        Tuple of (regime, description, correction_needed)
    """
    if rev >= 10000:
        return ("Turbulent", "Fully turbulent flow - no correction needed", False)
    elif rev >= 2000:
        return ("Transitional", "Transition zone - moderate correction applied", True)
    elif rev >= 100:
        return ("Laminar", "Laminar flow - significant correction required", True)
    else:
        return ("Highly Laminar", "Very low flow - maximum correction applied", True)

def get_viscosity_recommendation(rev, fr):
    """
    Provide recommendations based on Reynolds analysis

    Args:
        rev: Valve Reynolds number
        fr: Reynolds correction factor

    Returns:
        Recommendation string
    """
    if rev >= 10000:
        return "Flow is fully turbulent. Standard sizing methods apply."
    elif rev >= 2000:
        return f"Flow is in transition zone. Cv increased by {((1/fr - 1) * 100):.1f}% due to viscous effects."
    elif rev >= 100:
        return f"Laminar flow detected. Cv increased by {((1/fr - 1) * 100):.1f}% to account for viscosity. Consider larger valve or heating fluid."
    else:
        return f"Highly viscous flow. Cv increased by {((1/fr - 1) * 100):.1f}%. Strong recommendation to reduce viscosity or use larger valve."

def calculate_corrected_cv_iterative(flow_rate, dp, specific_gravity, viscosity, max_iterations=10, tolerance=0.01):
    """
    Iterative calculation of corrected Cv since Cv appears in both the basic equation and Reynolds correction

    Args:
        flow_rate: Flow rate (gpm)
        dp: Pressure drop (psi)
        specific_gravity: Fluid specific gravity
        viscosity: Viscosity (cP)
        max_iterations: Maximum iterations
        tolerance: Convergence tolerance

    Returns:
        Dictionary with converged results
    """
    # Initial guess using basic formula
    cv_prev = flow_rate * np.sqrt(specific_gravity / dp)

    for iteration in range(max_iterations):
        # Calculate Reynolds number with current Cv
        rev = calculate_valve_reynolds_number(cv_prev, flow_rate, viscosity, specific_gravity)

        # Get FR factor
        fr = get_reynolds_factor_from_curve(rev)

        # Calculate new Cv
        cv_new = cv_prev / fr

        # Check convergence
        error = abs(cv_new - cv_prev) / cv_prev

        if error < tolerance:
            regime, description, _ = check_reynolds_regime(rev)
            recommendation = get_viscosity_recommendation(rev, fr)

            return {
                "cv_corrected": cv_new,
                "reynolds_number": rev,
                "fr_factor": fr,
                "iterations": iteration + 1,
                "converged": True,
                "flow_regime": regime,
                "regime_description": description,
                "recommendation": recommendation
            }

        cv_prev = cv_new

    # If not converged
    return {
        "cv_corrected": cv_new,
        "reynolds_number": rev,
        "fr_factor": fr,
        "iterations": max_iterations,
        "converged": False,
        "flow_regime": "Unknown",
        "regime_description": "Did not converge",
        "recommendation": "Calculation did not converge. Check input values."
    }
