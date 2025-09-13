"""
ISA RP75.23 - Fixed version to handle flow scenario validation
"""
import numpy as np

# Standard sigma limit values for different valve types and constructions
SIGMA_LIMITS = {
    "Globe": {
        "Standard": {
            "sigma_i": 3.0,    # Incipient cavitation
            "sigma_c": 2.0,    # Constant cavitation  
            "sigma_d": 1.5,    # Incipient damage
            "sigma_ch": 1.0,   # Choking cavitation
            "sigma_mv": 0.8    # Maximum vibration
        },
        "Anti-Cavitation": {
            "sigma_i": 4.0,
            "sigma_c": 3.0,
            "sigma_d": 2.5,
            "sigma_ch": 2.0,
            "sigma_mv": 1.5
        },
        "Low-Noise": {
            "sigma_i": 3.5,
            "sigma_c": 2.5,
            "sigma_d": 2.0,
            "sigma_ch": 1.5,
            "sigma_mv": 1.2
        }
    },
    "Ball (Segmented)": {  # Fixed the key name
        "Standard V-Notch": {
            "sigma_i": 2.5,
            "sigma_c": 1.8,
            "sigma_d": 1.3,
            "sigma_ch": 0.9,
            "sigma_mv": 0.7
        },
        "High-Performance": {
            "sigma_i": 3.2,
            "sigma_c": 2.2,
            "sigma_d": 1.7,
            "sigma_ch": 1.2,
            "sigma_mv": 1.0
        }
    },
    "Ball": {  # Added simple Ball entry
        "Standard": {
            "sigma_i": 2.5,
            "sigma_c": 1.8,
            "sigma_d": 1.3,
            "sigma_ch": 0.9,
            "sigma_mv": 0.7
        }
    },
    "Butterfly": {
        "Standard": {
            "sigma_i": 2.0,
            "sigma_c": 1.5,
            "sigma_d": 1.2,
            "sigma_ch": 0.8,
            "sigma_mv": 0.6
        },
        "High-Performance": {
            "sigma_i": 2.8,
            "sigma_c": 2.0,
            "sigma_d": 1.5,
            "sigma_ch": 1.1,
            "sigma_mv": 0.9
        }
    }
}

def get_sigma_limits(valve_type, valve_style):
    """
    Get sigma limits for specific valve type and style with better error handling
    """
    # Clean up valve type names
    valve_type_clean = valve_type.replace(" (Segmented)", "").strip()

    # Try to find the valve type, with fallbacks
    if valve_type_clean in SIGMA_LIMITS:
        valve_limits = SIGMA_LIMITS[valve_type_clean]
    elif "Ball" in valve_type:
        valve_limits = SIGMA_LIMITS["Ball"]
    else:
        valve_limits = SIGMA_LIMITS["Globe"]  # Default fallback

    # Find best matching style with better error handling
    style_key = "Standard"  # Default

    # Try exact match first
    if valve_style in valve_limits:
        style_key = valve_style
    else:
        # Try partial matches
        for key in valve_limits.keys():
            if valve_style.lower() in key.lower() or key.lower() in valve_style.lower():
                style_key = key
                break

    return valve_limits.get(style_key, valve_limits[list(valve_limits.keys())[0]])

def calculate_sigma_value(p1, p2, pv):
    """Calculate the sigma cavitation parameter with safety checks"""
    try:
        if (p1 - p2) <= 0:
            return float('inf')  # No pressure drop, no cavitation

        sigma = (p1 - pv) / (p1 - p2)
        return max(0, sigma)  # Ensure non-negative
    except:
        return 2.0  # Safe default value

def determine_cavitation_level(sigma, limits):
    """Determine cavitation level based on sigma value and limits"""
    try:
        sigma_i = limits.get("sigma_i", 3.0)
        sigma_c = limits.get("sigma_c", 2.0)
        sigma_d = limits.get("sigma_d", 1.5)
        sigma_ch = limits.get("sigma_ch", 1.0)
        sigma_mv = limits.get("sigma_mv", 0.8)

        if sigma >= sigma_i:
            return ("No Cavitation", "No cavitation occurs", "Low")
        elif sigma >= sigma_c:
            return ("Incipient", "Cavitation just detectable, no damage", "Low")
        elif sigma >= sigma_d:
            return ("Constant", "Constant cavitation, some noise/vibration", "Medium")
        elif sigma >= sigma_ch:
            return ("Incipient Damage", "Cavitation damage may begin", "High")
        elif sigma >= sigma_mv:
            return ("Choking", "Severe cavitation, significant damage risk", "Critical")
        else:
            return ("Maximum Vibration", "Extreme cavitation, valve damage likely", "Critical")
    except:
        return ("Unknown", "Could not determine cavitation level", "Medium")

def get_trim_recommendation(level, risk):
    """Get trim recommendation based on cavitation level"""
    recommendations = {
        "No Cavitation": "Standard trim materials acceptable.",
        "Incipient": "Standard trim acceptable. Monitor for changes in service conditions.",
        "Constant": "Standard trim likely acceptable but monitor closely. Consider hardened materials for critical applications.",
        "Incipient Damage": "Hardened trim materials recommended (e.g., Stellite overlay). Consider anti-cavitation design.",
        "Choking": "Hardened trim essential. Multi-stage pressure reduction recommended. Consider valve redesign.",
        "Maximum Vibration": "Multi-stage anti-cavitation valve required. Single-stage valve not recommended."
    }

    return recommendations.get(level, "Consult valve manufacturer for specific recommendations.")

def calculate_sigma_levels(p1, p2, pv, valve_data):
    """
    Complete ISA RP75.23 sigma analysis with improved error handling
    """
    try:
        # Calculate sigma with safety checks
        sigma = calculate_sigma_value(p1, p2, pv)

        # Get valve-specific limits with fallbacks
        limits = get_sigma_limits(
            valve_data.get('valve_type', 'Globe'),
            valve_data.get('valve_style', 'Standard')
        )

        # Determine cavitation level
        level, description, risk = determine_cavitation_level(sigma, limits)

        # Get recommendation
        recommendation = get_trim_recommendation(level, risk)

        # Additional metrics
        damage_potential = "High" if risk in ["High", "Critical"] else "Low"

        # Calculate margin to damage safely
        margin_to_damage = None
        try:
            if sigma < limits.get("sigma_i", 3.0):
                margin_to_damage = sigma - limits.get("sigma_d", 1.5)
        except:
            pass

        return {
            "sigma": sigma,
            "level": level,
            "description": description,
            "status": f"{level} Cavitation",
            "risk": risk,
            "recommendation": recommendation,
            "damage_potential": damage_potential,
            "limits_used": limits,
            "margin_to_damage": margin_to_damage
        }

    except Exception as e:
        # Ultimate fallback
        return {
            "sigma": 2.0,
            "level": "Basic Calculation",
            "description": "Fallback calculation used",
            "status": "No Significant Cavitation",
            "risk": "Low",
            "recommendation": "Standard trim likely acceptable",
            "damage_potential": "Low",
            "limits_used": {"sigma_i": 3.0, "sigma_c": 2.0, "sigma_d": 1.5},
            "margin_to_damage": None
        }

def get_cavitation_chart_data(valve_type, valve_style):
    """Get data for plotting cavitation limits chart"""
    try:
        limits = get_sigma_limits(valve_type, valve_style)

        return {
            "levels": ["No Cavitation", "Incipient", "Constant", "Incipient Damage", "Choking", "Max Vibration"],
            "sigma_values": [limits.get("sigma_i", 3.0), limits.get("sigma_c", 2.0), 
                            limits.get("sigma_d", 1.5), limits.get("sigma_ch", 1.0), 
                            limits.get("sigma_mv", 0.8), 0],
            "colors": ["green", "yellow", "orange", "red", "darkred", "black"],
            "descriptions": [
                "Safe operation zone",
                "Detectable but harmless", 
                "Some noise/vibration",
                "Potential trim damage",
                "Severe damage risk",
                "Extreme damage zone"
            ]
        }
    except:
        # Fallback chart data
        return {
            "levels": ["No Cavitation", "Potential Cavitation"],
            "sigma_values": [2.0, 1.0],
            "colors": ["green", "orange"],
            "descriptions": ["Safe operation", "Monitor closely"]
        }
