"""
Enhanced materials selection with comprehensive compatibility database
and detailed recommendations based on service conditions
"""

# Comprehensive material compatibility database
MATERIAL_COMPATIBILITY = {
    "Water": {
        "temperature_range": (-10, 150),  # °C
        "body_materials": ["Carbon Steel", "Ductile Iron", "Bronze", "Stainless Steel"],
        "trim_materials": ["316 SS", "Bronze", "Stellite"],
        "preferred": {"body": "Carbon Steel", "trim": "316 SS"}
    },
    "Steam": {
        "temperature_range": (100, 600),
        "body_materials": ["Carbon Steel", "Chrome-Moly", "Stainless Steel"],
        "trim_materials": ["316 SS", "Stellite", "Inconel"],
        "preferred": {"body": "Chrome-Moly", "trim": "Stellite"}
    },
    "Hydrocarbons": {
        "temperature_range": (-50, 400),
        "body_materials": ["Carbon Steel", "Stainless Steel"],
        "trim_materials": ["316 SS", "Stellite", "Hardened 316 SS"],
        "preferred": {"body": "Carbon Steel", "trim": "316 SS"}
    },
    "Acids": {
        "temperature_range": (-20, 200),
        "body_materials": ["316L SS", "Hastelloy C", "Alloy 20", "PTFE Lined"],
        "trim_materials": ["Hastelloy C", "Alloy 20", "Ceramic"],
        "preferred": {"body": "316L SS", "trim": "Hastelloy C"}
    },
    "Caustics": {
        "temperature_range": (0, 150),
        "body_materials": ["316 SS", "Inconel", "Monel"],
        "trim_materials": ["Inconel", "Monel", "Stellite"],
        "preferred": {"body": "316 SS", "trim": "Inconel"}
    },
    "Hydrogen": {
        "temperature_range": (-200, 500),
        "body_materials": ["316L SS", "Inconel", "Chrome-Moly"],
        "trim_materials": ["Inconel", "Stellite", "316L SS"],
        "preferred": {"body": "316L SS", "trim": "Inconel"},
        "special_requirements": ["NACE MR0175 compliance", "Low-temp impact testing"]
    }
}

# Detailed material specifications
MATERIAL_SPECIFICATIONS = {
    "Carbon Steel": {
        "specification": "ASTM A216 WCB",
        "temperature_range": (-29, 427),  # °C
        "pressure_rating": "Up to ANSI 2500",
        "advantages": ["Low cost", "Good mechanical properties", "Widely available"],
        "limitations": ["Corrosion susceptible", "Limited high-temp use"],
        "applications": ["General water service", "Hydrocarbons", "Steam < 400°C"]
    },
    "316 SS": {
        "specification": "ASTM A351 CF8M",
        "temperature_range": (-196, 816),
        "pressure_rating": "Up to ANSI 2500",
        "advantages": ["Excellent corrosion resistance", "Wide temp range", "Good strength"],
        "limitations": ["Higher cost", "Chloride stress cracking susceptible"],
        "applications": ["General chemical service", "Food grade", "Marine environments"]
    },
    "316L SS": {
        "specification": "ASTM A351 CF3M",
        "temperature_range": (-196, 454),
        "pressure_rating": "Up to ANSI 2500",
        "advantages": ["Low carbon content", "Improved weldability", "Better corrosion resistance"],
        "limitations": ["Lower strength than 316", "Higher cost"],
        "applications": ["Sour service", "High-purity applications", "Cryogenic service"]
    },
    "Chrome-Moly": {
        "specification": "ASTM A217 C5/C12",
        "temperature_range": (-29, 649),
        "pressure_rating": "Up to ANSI 2500",
        "advantages": ["High temperature strength", "Good thermal properties"],
        "limitations": ["Requires PWHT", "Hydrogen attack susceptible"],
        "applications": ["High-temp steam", "Refinery service", "Power generation"]
    },
    "Hastelloy C": {
        "specification": "UNS N10276",
        "temperature_range": (-196, 1093),
        "pressure_rating": "Up to ANSI 1500",
        "advantages": ["Excellent chemical resistance", "High temperature capability"],
        "limitations": ["Very high cost", "Difficult machining"],
        "applications": ["Severe chemical service", "High-temp acids", "Chlorine service"]
    },
    "Stellite": {
        "specification": "Cobalt-Chrome Alloy",
        "temperature_range": (-196, 980),
        "pressure_rating": "Trim application",
        "advantages": ["Extreme hardness", "Cavitation resistance", "High-temp strength"],
        "limitations": ["Expensive", "Difficult machining", "Brittle"],
        "applications": ["Cavitating service", "Abrasive media", "High-temp trim"]
    }
}

# Service-specific material recommendations
SERVICE_RECOMMENDATIONS = {
    "Clean Water": {
        "body": "Carbon Steel (ASTM A216 WCB)",
        "trim": "316 SS",
        "bolting": "ASTM A193 B7 / A194 2H",
        "gasket": "Spiral Wound 316SS/Graphite",
        "coating": "None required"
    },
    "Seawater": {
        "body": "316 SS (ASTM A351 CF8M)",
        "trim": "Super Duplex SS",
        "bolting": "ASTM A193 B8M / A194 8M",
        "gasket": "Spiral Wound Super Duplex/PTFE",
        "coating": "None required"
    },
    "Sour Service": {
        "body": "316L SS (ASTM A351 CF3M)",
        "trim": "Inconel 625",
        "bolting": "ASTM A193 B8MLCuN / A194 8MLCuN", 
        "gasket": "Spiral Wound Inconel/PTFE",
        "coating": "None required",
        "standards": ["NACE MR0175", "ISO 15156"]
    },
    "High Temperature": {
        "body": "Chrome-Moly (ASTM A217 C12)",
        "trim": "Stellite overlay on 316 SS",
        "bolting": "ASTM A193 B16 / A194 4",
        "gasket": "RTJ or Spiral Wound 316SS/Mica",
        "coating": "High-temp resistant"
    },
    "Cryogenic": {
        "body": "316L SS (ASTM A351 CF3M)",
        "trim": "316L SS",
        "bolting": "ASTM A193 B8M / A194 8M",
        "gasket": "Spiral Wound 316L/PTFE",
        "coating": "None required",
        "testing": "Charpy impact testing required"
    }
}

def select_materials(data):
    """
    Enhanced material selection based on comprehensive analysis

    Args:
        data: Process data including fluid, temperature, pressure, service conditions

    Returns:
        Detailed material recommendations with justification
    """
    fluid_name = data.get('fluid_name', 'Water').strip()
    fluid_nature = data.get('fluid_nature', 'Clean')
    temp = data.get('t1', 25)
    pressure = data.get('p1', 10)

    # Determine service category
    service_category = determine_service_category(fluid_name, fluid_nature, temp, pressure)

    # Get base recommendations
    if service_category in SERVICE_RECOMMENDATIONS:
        base_materials = SERVICE_RECOMMENDATIONS[service_category].copy()
    else:
        base_materials = SERVICE_RECOMMENDATIONS["Clean Water"].copy()

    # Apply temperature-based adjustments
    base_materials = apply_temperature_adjustments(base_materials, temp)

    # Apply pressure-based adjustments  
    base_materials = apply_pressure_adjustments(base_materials, pressure)

    # Apply fluid-specific adjustments
    base_materials = apply_fluid_adjustments(base_materials, fluid_name, fluid_nature)

    # Generate compliance check
    compliance_info = generate_compliance_check(base_materials, service_category, data)

    # Additional recommendations
    additional_recommendations = generate_additional_recommendations(data, service_category)

    return {
        "recommendations": {
            "Body Material": base_materials["body"],
            "Trim Material": base_materials["trim"],
            "Bolting": base_materials["bolting"],
            "Gasket": base_materials["gasket"]
        },
        "service_category": service_category,
        "compliance_check": compliance_info,
        "additional_recommendations": additional_recommendations,
        "material_justification": generate_material_justification(base_materials, data),
        "alternative_materials": get_alternative_materials(service_category),
        "testing_requirements": get_testing_requirements(service_category, temp, pressure)
    }

def determine_service_category(fluid_name, fluid_nature, temp, pressure):
    """Determine service category based on fluid and conditions"""
    fluid_lower = fluid_name.lower()

    # Check for specific fluids
    if 'water' in fluid_lower and 'sea' not in fluid_lower:
        if temp > 100:
            return "High Temperature"
        elif temp < 0:
            return "Cryogenic"
        else:
            return "Clean Water"
    elif 'seawater' in fluid_lower or 'brine' in fluid_lower:
        return "Seawater"
    elif any(acid in fluid_lower for acid in ['acid', 'hcl', 'h2so4', 'sulfuric']):
        return "Sour Service"
    elif 'hydrogen' in fluid_lower or 'h2s' in fluid_lower:
        return "Sour Service"
    elif temp > 400:
        return "High Temperature"
    elif temp < -50:
        return "Cryogenic"

    # Check by fluid nature
    if fluid_nature == "Corrosive":
        return "Sour Service"
    elif fluid_nature == "Flashing/Cavitating":
        return "High Temperature"  # Assume high-energy service

    return "Clean Water"  # Default

def apply_temperature_adjustments(materials, temp):
    """Apply temperature-based material adjustments"""
    if temp > 500:
        materials["body"] = "Chrome-Moly (ASTM A217 C12)"
        materials["trim"] = "Stellite overlay on Inconel"
        materials["bolting"] = "ASTM A193 B16 / A194 4"
        materials["gasket"] = "RTJ Inconel"
    elif temp > 400:
        materials["body"] = "Chrome-Moly (ASTM A217 C5)"
        materials["trim"] = "Stellite overlay on 316 SS"
        materials["bolting"] = "ASTM A193 B8T / A194 8T"
        materials["gasket"] = "Spiral Wound 316SS/Mica"
    elif temp < -100:
        materials["body"] = "316L SS (ASTM A351 CF3M)"
        materials["trim"] = "316L SS"
        materials["bolting"] = "ASTM A193 B8M / A194 8M"
        materials["gasket"] = "Spiral Wound 316L/PTFE"
    elif temp < -29:
        materials["body"] = "316 SS (ASTM A351 CF8M)"
        materials["trim"] = "316 SS"
        materials["bolting"] = "ASTM A193 B8 / A194 8"

    return materials

def apply_pressure_adjustments(materials, pressure):
    """Apply pressure-based material adjustments"""
    # Convert pressure to approximate ANSI class
    if pressure > 100:  # Very high pressure
        materials["bolting"] = materials["bolting"].replace("B7", "B8M")
        materials["gasket"] = "RTJ or Metal Seal"
    elif pressure > 40:  # High pressure
        materials["gasket"] = "Spiral Wound with Centering Ring"

    return materials

def apply_fluid_adjustments(materials, fluid_name, fluid_nature):
    """Apply fluid-specific material adjustments"""
    fluid_lower = fluid_name.lower()

    if 'chlorine' in fluid_lower or 'cl2' in fluid_lower:
        materials["body"] = "Hastelloy C (UNS N10276)"
        materials["trim"] = "Hastelloy C"
        materials["bolting"] = "Hastelloy C bolting"
        materials["gasket"] = "PTFE envelope"
    elif 'ammonia' in fluid_lower or 'nh3' in fluid_lower:
        materials["body"] = "Carbon Steel (ASTM A216 WCB)"
        materials["trim"] = "316 SS"
        # Avoid copper alloys with ammonia
    elif fluid_nature == "Abrasive":
        materials["trim"] = "Stellite hard facing or Ceramic"

    return materials

def generate_compliance_check(materials, service_category, data):
    """Generate compliance check information"""
    compliance_standards = ["ASME B16.34", "API 6D"]

    if service_category == "Sour Service":
        compliance_standards.extend(["NACE MR0175", "ISO 15156"])

    if data.get('t1', 25) > 400:
        compliance_standards.append("ASME VIII Div 1 High Temperature")

    if data.get('p1', 10) > 100:
        compliance_standards.append("ASME B31.3 High Pressure")

    return f"Materials comply with {', '.join(compliance_standards)}. Final verification against specific service conditions required."

def generate_additional_recommendations(data, service_category):
    """Generate additional material-related recommendations"""
    recommendations = []

    temp = data.get('t1', 25)
    pressure = data.get('p1', 10)

    if temp > 300:
        recommendations.append("Post-weld heat treatment (PWHT) required for pressure boundary welds")

    if temp < -29:
        recommendations.append("Charpy impact testing required for low-temperature service")

    if service_category == "Sour Service":
        recommendations.append("Hardness testing (HRC ≤ 22) required for all pressure boundary materials")

    if pressure > 40:
        recommendations.append("Hydrostatic testing at 1.5x design pressure recommended")

    if data.get('fluid_nature') == "Abrasive":
        recommendations.append("Consider replaceable wear plates or hardening treatments")

    return recommendations

def generate_material_justification(materials, data):
    """Generate justification for material selection"""
    justifications = []

    body_material = materials["body"]
    if "Chrome-Moly" in body_material:
        justifications.append("Chrome-Moly selected for high-temperature strength and creep resistance")
    elif "316L SS" in body_material:
        justifications.append("316L SS selected for enhanced corrosion resistance and low-carbon content")
    elif "Carbon Steel" in body_material:
        justifications.append("Carbon Steel selected for cost-effectiveness in non-corrosive service")

    trim_material = materials["trim"]
    if "Stellite" in trim_material:
        justifications.append("Stellite trim selected for cavitation and erosion resistance")
    elif "Hastelloy" in trim_material:
        justifications.append("Hastelloy trim selected for severe chemical service resistance")
    elif "316 SS" in trim_material:
        justifications.append("316 SS trim selected for good corrosion resistance and cost balance")

    return "; ".join(justifications)

def get_alternative_materials(service_category):
    """Get alternative material options"""
    alternatives = {
        "Clean Water": {
            "body": ["Ductile Iron", "Bronze", "316 SS"],
            "trim": ["Bronze", "Stellite", "Hard Chrome"]
        },
        "Sour Service": {
            "body": ["Duplex SS", "Super Duplex SS", "Inconel 625"],
            "trim": ["Inconel 625", "Stellite 6", "Ceramic"]
        },
        "High Temperature": {
            "body": ["310 SS", "Inconel 600", "Chrome-Moly Grade 91"],
            "trim": ["Inconel 600", "Stellite 12", "Ceramic"]
        },
        "Cryogenic": {
            "body": ["304L SS", "Aluminum Bronze", "9% Nickel Steel"],
            "trim": ["304L SS", "316L SS", "Inconel 625"]
        }
    }

    return alternatives.get(service_category, alternatives["Clean Water"])

def get_testing_requirements(service_category, temp, pressure):
    """Get required testing based on service conditions"""
    tests = ["Hydrostatic test", "Visual inspection"]

    if temp < -29:
        tests.append("Charpy impact test at design temperature")

    if temp > 400:
        tests.append("Creep and stress rupture testing")

    if service_category == "Sour Service":
        tests.extend(["Hardness testing (HRC ≤ 22)", "SSC testing per NACE TM0177"])

    if pressure > 100:
        tests.append("Pneumatic test at 110% design pressure")

    return tests
