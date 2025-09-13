# Enhanced unit conversion constants and functions
BAR_TO_PSI = 14.5038
M3HR_TO_GPM = 4.40287
NM3HR_TO_SCFH = 37.324  # Approximate, based on standard engineering practice
KG_M3_TO_LB_FT3 = 0.062428
CELSIUS_TO_KELVIN = 273.15
CELSIUS_TO_RANKINE = lambda c: (c + 273.15) * 9/5

def convert_pressure(value, from_system, to_unit):
    """Enhanced pressure conversion with absolute pressure handling"""
    if from_system == 'Metric':
        if to_unit == 'psi':
            return value * BAR_TO_PSI
        elif to_unit == 'psia':
            return value * BAR_TO_PSI  # Assuming input is absolute bar
        elif to_unit == 'bara':
            return value  # Already in bara
    elif from_system == 'Imperial':
        if to_unit == 'bar':
            return value / BAR_TO_PSI
        elif to_unit == 'bara':
            return value / BAR_TO_PSI  # Assuming input is psia
        elif to_unit == 'psia':
            return value  # Already in psia
    return value  # No conversion needed

def convert_flow_liquid(value, from_system, to_unit):
    """Enhanced liquid flow conversion"""
    if from_system == 'Metric' and to_unit == 'gpm':
        return value * M3HR_TO_GPM
    elif from_system == 'Imperial' and to_unit == 'm³/hr':
        return value / M3HR_TO_GPM
    return value

def convert_density(value, from_system, to_unit):
    """Enhanced density conversion"""
    if from_system == 'Metric' and to_unit == 'SG':
        return value / 1000.0
    elif from_system == 'Imperial' and to_unit == 'kg/m³':
        return value * 1000.0
    elif from_system == 'Metric' and to_unit == 'lb/ft³':
        return value * KG_M3_TO_LB_FT3
    elif from_system == 'Imperial' and to_unit == 'kg/m³' and value < 10:  # Assuming SG input
        return value * 1000.0
    return value

def convert_temperature(value, from_system, to_unit):
    """Enhanced temperature conversion with absolute temperature support"""
    if from_system == 'Metric':
        if to_unit == '°F':
            return (value * 9/5) + 32
        elif to_unit == 'R':  # Rankine
            return (value + 273.15) * 9/5
        elif to_unit == 'K':  # Kelvin
            return value + 273.15
    elif from_system == 'Imperial':
        if to_unit == '°C':
            return (value - 32) * 5/9
        elif to_unit == 'K':  # Kelvin
            return ((value - 32) * 5/9) + 273.15
        elif to_unit == 'R':  # Rankine
            return value + 459.67
    return value

def convert_flow_gas(value, from_system, to_unit):
    """Enhanced gas flow conversion"""
    if from_system == 'Metric' and to_unit == 'scfh':
        return value * NM3HR_TO_SCFH
    elif from_system == 'Imperial' and to_unit == 'Nm³/hr':
        return value / NM3HR_TO_SCFH
    return value

def convert_force(value, from_system, to_unit):
    """Force conversion between metric and imperial"""
    if from_system == 'Metric' and to_unit == 'lbf':
        return value / 4.44822  # N to lbf
    elif from_system == 'Imperial' and to_unit == 'N':
        return value * 4.44822  # lbf to N
    return value

def convert_torque(value, from_system, to_unit):
    """Torque conversion between metric and imperial"""
    if from_system == 'Metric' and to_unit == 'ft-lbf':
        return value / 1.35582  # Nm to ft-lbf
    elif from_system == 'Imperial' and to_unit == 'Nm':
        return value * 1.35582  # ft-lbf to Nm
    return value

def get_absolute_pressure(gauge_pressure, atmospheric_pressure=14.7):
    """Convert gauge pressure to absolute pressure"""
    return gauge_pressure + atmospheric_pressure

def convert_all_units(data, target_system):
    """
    Convert all units in a data dictionary to target system

    Args:
        data: Dictionary containing process data
        target_system: 'Metric' or 'Imperial'

    Returns:
        Dictionary with converted units
    """
    converted_data = data.copy()

    if data['unit_system'] == target_system:
        return converted_data  # No conversion needed

    # Pressure conversions
    pressure_keys = ['p1', 'p2', 'pv', 'pc', 'dp']
    for key in pressure_keys:
        if key in data:
            converted_data[key] = convert_pressure(data[key], data['unit_system'], 
                                                 'bar' if target_system == 'Metric' else 'psi')

    # Temperature conversion
    if 't1' in data:
        converted_data['t1'] = convert_temperature(data['t1'], data['unit_system'],
                                                 '°C' if target_system == 'Metric' else '°F')

    # Flow rate conversion
    if 'flow_rate' in data:
        if data['fluid_type'] == 'Liquid':
            converted_data['flow_rate'] = convert_flow_liquid(data['flow_rate'], data['unit_system'],
                                                            'm³/hr' if target_system == 'Metric' else 'gpm')
        else:
            converted_data['flow_rate'] = convert_flow_gas(data['flow_rate'], data['unit_system'],
                                                         'Nm³/hr' if target_system == 'Metric' else 'scfh')

    # Density conversion
    if 'rho' in data:
        converted_data['rho'] = convert_density(data['rho'], data['unit_system'],
                                              'kg/m³' if target_system == 'Metric' else 'SG')

    converted_data['unit_system'] = target_system
    return converted_data
