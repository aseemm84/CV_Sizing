"""
Enhanced valve data with travel-dependent coefficients and vendor data integration
Provides comprehensive valve characteristics across different opening percentages
"""

# Travel-dependent FL and Kc curves (opening % -> coefficient)
# Based on typical valve test data
TRAVEL_DEPENDENT_COEFFICIENTS = {
    "Globe": {
        "Standard, Cage-Guided": {
            "FL_curve": {10: 0.85, 30: 0.88, 50: 0.90, 70: 0.90, 90: 0.89, 100: 0.88},
            "Kc_curve": {10: 0.75, 30: 0.72, 50: 0.70, 70: 0.69, 90: 0.68, 100: 0.67},
            "Xt_curve": {10: 0.70, 30: 0.73, 50: 0.75, 70: 0.76, 90: 0.75, 100: 0.74}
        },
        "Low-Noise, Multi-Path": {
            "FL_curve": {10: 0.92, 30: 0.94, 50: 0.95, 70: 0.95, 90: 0.94, 100: 0.93},
            "Kc_curve": {10: 0.85, 30: 0.82, 50: 0.80, 70: 0.79, 90: 0.78, 100: 0.77},
            "Xt_curve": {10: 0.75, 30: 0.78, 50: 0.80, 70: 0.81, 90: 0.80, 100: 0.79}
        },
        "Anti-Cavitation, Multi-Stage": {
            "FL_curve": {10: 0.95, 30: 0.97, 50: 0.98, 70: 0.98, 90: 0.97, 100: 0.96},
            "Kc_curve": {10: 0.90, 30: 0.87, 50: 0.85, 70: 0.84, 90: 0.83, 100: 0.82},
            "Xt_curve": {10: 0.80, 30: 0.83, 50: 0.85, 70: 0.86, 90: 0.85, 100: 0.84}
        },
        "Port-Guided, Quick Opening": {
            "FL_curve": {10: 0.80, 30: 0.83, 50: 0.85, 70: 0.85, 90: 0.84, 100: 0.83},
            "Kc_curve": {10: 0.70, 30: 0.67, 50: 0.65, 70: 0.64, 90: 0.63, 100: 0.62},
            "Xt_curve": {10: 0.65, 30: 0.68, 50: 0.70, 70: 0.71, 90: 0.70, 100: 0.69}
        }
    },
    "Ball (Segmented)": {
        "Standard V-Notch": {
            "FL_curve": {10: 0.75, 30: 0.78, 50: 0.80, 70: 0.81, 90: 0.80, 100: 0.79},
            "Kc_curve": {10: 0.65, 30: 0.62, 50: 0.60, 70: 0.59, 90: 0.58, 100: 0.57},
            "Xt_curve": {10: 0.35, 30: 0.38, 50: 0.40, 70: 0.41, 90: 0.40, 100: 0.39}
        },
        "High-Performance": {
            "FL_curve": {10: 0.70, 30: 0.73, 50: 0.75, 70: 0.76, 90: 0.75, 100: 0.74},
            "Kc_curve": {10: 0.60, 30: 0.57, 50: 0.55, 70: 0.54, 90: 0.53, 100: 0.52},
            "Xt_curve": {10: 0.30, 30: 0.33, 50: 0.35, 70: 0.36, 90: 0.35, 100: 0.34}
        }
    },
    "Butterfly": {
        "Standard, Centric Disc": {
            "FL_curve": {10: 0.65, 30: 0.68, 50: 0.70, 70: 0.71, 90: 0.70, 100: 0.69},
            "Kc_curve": {10: 0.55, 30: 0.52, 50: 0.50, 70: 0.49, 90: 0.48, 100: 0.47},
            "Xt_curve": {10: 0.25, 30: 0.28, 50: 0.30, 70: 0.31, 90: 0.30, 100: 0.29}
        },
        "High-Performance, Double Offset": {
            "FL_curve": {10: 0.80, 30: 0.83, 50: 0.85, 70: 0.86, 90: 0.85, 100: 0.84},
            "Kc_curve": {10: 0.70, 30: 0.67, 50: 0.65, 70: 0.64, 90: 0.63, 100: 0.62},
            "Xt_curve": {10: 0.50, 30: 0.53, 50: 0.55, 70: 0.56, 90: 0.55, 100: 0.54}
        }
    }
}

# Base valve characteristics (average values)
VALVE_COEFFICIENTS = {
    "Globe": {
        "Standard, Cage-Guided": {
            "FL": 0.90, "Kc": 0.70, "Xt": 0.75, "Rangeability": 50,
            "Style": "General purpose, excellent throttling, moderate capacity.",
            "Cv_efficiency": 0.85,  # Percentage of theoretical max Cv
            "Pressure_class": ["150", "300", "600", "900", "1500"],
            "Temperature_range": [-29, 427]  # °C
        },
        "Low-Noise, Multi-Path": {
            "FL": 0.95, "Kc": 0.80, "Xt": 0.80, "Rangeability": 40,
            "Style": "Designed to attenuate aerodynamic noise in gas service.",
            "Cv_efficiency": 0.75,
            "Pressure_class": ["150", "300", "600"],
            "Temperature_range": [-20, 400]
        },
        "Anti-Cavitation, Multi-Stage": {
            "FL": 0.98, "Kc": 0.85, "Xt": 0.85, "Rangeability": 30,
            "Style": "Reduces pressure in multiple steps to prevent cavitation damage.",
            "Cv_efficiency": 0.70,
            "Pressure_class": ["150", "300", "600", "900"],
            "Temperature_range": [-20, 400]
        },
        "Port-Guided, Quick Opening": {
            "FL": 0.85, "Kc": 0.65, "Xt": 0.70, "Rangeability": 20,
            "Style": "Best for on/off service, poor throttling.",
            "Cv_efficiency": 0.90,
            "Pressure_class": ["150", "300", "600"],
            "Temperature_range": [-29, 427]
        }
    },
    "Ball (Segmented)": {
        "Standard V-Notch": {
            "FL": 0.80, "Kc": 0.60, "Xt": 0.40, "Rangeability": 100,
            "Style": "Good rangeability and throttling, suitable for slurries.",
            "Cv_efficiency": 0.95,
            "Pressure_class": ["150", "300", "600", "900", "1500"],
            "Temperature_range": [-46, 232]
        },
        "High-Performance": {
            "FL": 0.75, "Kc": 0.55, "Xt": 0.35, "Rangeability": 80,
            "Style": "Higher capacity, but less pressure recovery.",
            "Cv_efficiency": 0.98,
            "Pressure_class": ["150", "300", "600", "900"],
            "Temperature_range": [-46, 232]
        }
    },
    "Butterfly": {
        "Standard, Centric Disc": {
            "FL": 0.70, "Kc": 0.50, "Xt": 0.30, "Rangeability": 20,
            "Style": "Low cost, high capacity, limited throttling range (typically 60-degree opening).",
            "Cv_efficiency": 0.95,
            "Pressure_class": ["150", "300"],
            "Temperature_range": [-40, 200]
        },
        "High-Performance, Double Offset": {
            "FL": 0.85, "Kc": 0.65, "Xt": 0.55, "Rangeability": 50,
            "Style": "Better shutoff and control than standard butterfly valves.",
            "Cv_efficiency": 0.90,
            "Pressure_class": ["150", "300", "600"],
            "Temperature_range": [-40, 260]
        }
    }
}

# Rated Cv values with size-dependent variations
VALVE_RATED_CVS = {
    # Size (inches): {valve_type: rated_cv}
    1: {"Globe": 12, "Ball": 15, "Butterfly": 18},
    2: {"Globe": 50, "Ball": 65, "Butterfly": 80},
    3: {"Globe": 110, "Ball": 140, "Butterfly": 170},
    4: {"Globe": 170, "Ball": 220, "Butterfly": 280},
    6: {"Globe": 400, "Ball": 520, "Butterfly": 650},
    8: {"Globe": 700, "Ball": 900, "Butterfly": 1100},
    10: {"Globe": 1080, "Ball": 1400, "Butterfly": 1700},
    12: {"Globe": 1750, "Ball": 2250, "Butterfly": 2800},
    14: {"Globe": 2400, "Ball": 3100, "Butterfly": 3800},
    16: {"Globe": 3200, "Ball": 4100, "Butterfly": 5000},
    18: {"Globe": 4100, "Ball": 5300, "Butterfly": 6500},
    20: {"Globe": 5000, "Ball": 6500, "Butterfly": 8000},
    24: {"Globe": 7200, "Ball": 9400, "Butterfly": 11500},
    30: {"Globe": 11000, "Ball": 14300, "Butterfly": 17500},
    36: {"Globe": 16000, "Ball": 20800, "Butterfly": 25500},
    42: {"Globe": 22000, "Ball": 28600, "Butterfly": 35000},
    48: {"Globe": 28000, "Ball": 36400, "Butterfly": 44500},
    54: {"Globe": 36000, "Ball": 46800, "Butterfly": 57200},
    60: {"Globe": 45000, "Ball": 58500, "Butterfly": 71500},
    66: {"Globe": 54000, "Ball": 70200, "Butterfly": 85800},
    72: {"Globe": 65000, "Ball": 84500, "Butterfly": 103000},
}

# Vendor-specific data structure
VENDOR_DATABASE = {
    "Fisher": {
        "Globe": {
            "ED Series": {
                "FL": 0.92, "Kc": 0.72, "Xt": 0.77, "Rangeability": 50,
                "sizes": [1, 2, 3, 4, 6, 8],
                "trim_materials": ["316 SS", "Stellite", "Ceramic"],
                "cv_multiplier": 1.05  # Slightly higher than generic
            },
            "HPT Series": {
                "FL": 0.88, "Kc": 0.68, "Xt": 0.73, "Rangeability": 40,
                "sizes": [2, 3, 4, 6, 8, 10, 12],
                "trim_materials": ["316 SS", "Stellite", "Hastelloy"],
                "cv_multiplier": 1.10
            }
        }
    },
    "Emerson": {
        "Globe": {
            "WhisperTrim": {
                "FL": 0.95, "Kc": 0.78, "Xt": 0.82, "Rangeability": 35,
                "sizes": [2, 3, 4, 6, 8, 10],
                "trim_materials": ["316 SS", "Stellite"],
                "cv_multiplier": 0.95,
                "noise_reduction": 15  # dB reduction
            }
        }
    },
    "Samson": {
        "Globe": {
            "Type 241": {
                "FL": 0.89, "Kc": 0.69, "Xt": 0.74, "Rangeability": 50,
                "sizes": [1, 2, 3, 4, 6, 8, 10],
                "trim_materials": ["316 SS", "Stellite"],
                "cv_multiplier": 1.02
            }
        }
    }
}

def get_valve_data(valve_type, valve_style, vendor=None, series=None):
    """
    Enhanced valve data retrieval with vendor-specific options

    Args:
        valve_type: Type of valve
        valve_style: Style/trim type
        vendor: Optional vendor name
        series: Optional vendor series/model

    Returns:
        Dictionary of valve characteristics
    """
    # Start with generic data
    try:
        base_data = VALVE_COEFFICIENTS[valve_type][valve_style].copy()
    except KeyError:
        base_data = {
            "FL": 0.9, "Kc": 0.7, "Xt": 0.75, "Rangeability": 30,
            "Style": "Default general purpose values.",
            "Cv_efficiency": 0.85
        }

    # Override with vendor-specific data if available
    if vendor and series:
        try:
            vendor_data = VENDOR_DATABASE[vendor][valve_type][series]
            base_data.update(vendor_data)
            base_data["vendor"] = vendor
            base_data["series"] = series
        except KeyError:
            pass  # Use generic data

    # Add travel-dependent curves if available
    try:
        travel_data = TRAVEL_DEPENDENT_COEFFICIENTS[valve_type][valve_style]
        base_data.update(travel_data)
    except KeyError:
        pass  # No travel-dependent data available

    return base_data

def get_valve_styles(valve_type):
    """Returns available styles for a valve type"""
    try:
        return list(VALVE_COEFFICIENTS[valve_type].keys())
    except KeyError:
        return ["Default Style"]

def get_rated_cv(valve_size, valve_type="Globe"):
    """
    Enhanced Cv retrieval with valve type consideration

    Args:
        valve_size: Nominal valve size (inches)
        valve_type: Type of valve

    Returns:
        Rated Cv for the valve size and type
    """
    try:
        return VALVE_RATED_CVS[valve_size][valve_type]
    except KeyError:
        # Fallback to Globe valve or estimate
        base_cv = VALVE_RATED_CVS.get(valve_size, {}).get("Globe", 50)

        # Apply type-specific multipliers
        multipliers = {"Globe": 1.0, "Ball": 1.3, "Butterfly": 1.6}
        return int(base_cv * multipliers.get(valve_type, 1.0))

def get_travel_dependent_coefficient(valve_type, valve_style, coefficient, opening_percent):
    """
    Get travel-dependent coefficient value

    Args:
        valve_type: Type of valve
        valve_style: Style of valve
        coefficient: 'FL', 'Kc', or 'Xt'
        opening_percent: Valve opening percentage (0-100)

    Returns:
        Interpolated coefficient value
    """
    try:
        curve_key = f"{coefficient}_curve"
        curve_data = TRAVEL_DEPENDENT_COEFFICIENTS[valve_type][valve_style][curve_key]

        return interpolate_coefficient_curve(opening_percent, curve_data)
    except KeyError:
        # Return base value if no curve available
        base_data = get_valve_data(valve_type, valve_style)
        return base_data.get(coefficient, 0.9 if coefficient == 'FL' else 0.7)

def interpolate_coefficient_curve(opening_percent, curve_data):
    """
    Interpolate coefficient value from curve data

    Args:
        opening_percent: Valve opening (0-100%)
        curve_data: Dictionary of {opening: coefficient}

    Returns:
        Interpolated coefficient value
    """
    if not curve_data:
        return None

    openings = sorted(curve_data.keys())

    # Bound the opening percentage
    opening_percent = max(openings[0], min(openings[-1], opening_percent))

    # Find surrounding points
    for i in range(len(openings) - 1):
        if openings[i] <= opening_percent <= openings[i + 1]:
            x1, x2 = openings[i], openings[i + 1]
            y1, y2 = curve_data[x1], curve_data[x2]

            # Linear interpolation
            if x2 - x1 != 0:
                return y1 + (y2 - y1) * (opening_percent - x1) / (x2 - x1)
            else:
                return y1

    # If exact match
    return curve_data.get(opening_percent, curve_data[openings[0]])

def get_available_vendors():
    """Get list of available vendors"""
    return list(VENDOR_DATABASE.keys())

def get_vendor_series(vendor, valve_type):
    """Get available series for a vendor and valve type"""
    try:
        return list(VENDOR_DATABASE[vendor][valve_type].keys())
    except KeyError:
        return []

def validate_valve_selection(valve_type, valve_size, pressure_class, temperature, service_conditions):
    """
    Validate valve selection against service conditions

    Args:
        valve_type: Type of valve
        valve_size: Valve size
        pressure_class: Pressure rating
        temperature: Operating temperature
        service_conditions: Dict of service parameters

    Returns:
        Dictionary with validation results
    """
    warnings = []
    recommendations = []

    # Size limitations
    if valve_type == "Globe" and valve_size > 24:
        warnings.append(f"Globe valves >24 are uncommon. Consider ball or butterfly valve.")

    if valve_type == "Butterfly" and valve_size < 3:
        warnings.append(f"Butterfly valves <3 have poor rangeability. Consider globe valve.")

    # Temperature limitations
    valve_data = get_valve_data(valve_type, "Standard")
    temp_range = valve_data.get("Temperature_range", [-20, 400])

    if temperature < temp_range[0] or temperature > temp_range[1]:
        warnings.append(f"Temperature {temperature}°C outside typical range {temp_range[0]}-{temp_range[1]}°C")

    # Pressure class validation
    available_classes = valve_data.get("Pressure_class", ["150", "300"])
    if pressure_class not in available_classes:
        warnings.append(f"Pressure class {pressure_class} not standard for this valve type")

    # Service-specific recommendations
    if service_conditions.get("cavitation_risk", False):
        recommendations.append("Consider anti-cavitation trim for cavitating service")

    if service_conditions.get("noise_sensitive", False):
        recommendations.append("Consider low-noise trim for noise-sensitive applications")

    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "recommendations": recommendations
    }
