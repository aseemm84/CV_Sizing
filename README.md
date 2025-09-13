# Enhanced Control Valve Sizing Application

## Professional-Grade Valve Sizing with Industry Standards

This enhanced application implements industry-leading standards and methodologies for control valve sizing and selection.

### Key Features

#### Enhanced Technical Standards
- **ISA RP75.23 Sigma Method**: Five-level cavitation analysis with damage potential assessment
- **Reynolds Number Correction**: FR factor calculation for non-turbulent flow conditions
- **IEC 60534-8-3 Noise Model**: Professional-grade noise prediction alongside simplified estimation
- **Travel-Dependent Coefficients**: FL, Kc, and Xt variations with valve opening percentage
- **Enhanced FF Factor Calculation**: Proper liquid critical pressure ratio factor computation

#### Professional Sizing Features
- **Industry-Standard Valve Opening Validation**: 20-80% operating range recommendations
- **Multi-Scenario Flow Analysis**: Validation across minimum, normal, design, maximum, and emergency flows
- **Enhanced Safety Factor Recommendations**: Based on service criticality and future expansion plans
- **Comprehensive Actuator Sizing**: Proper safety factors, spring force calculations, and detailed force/torque analysis

#### Vendor Integration
- **Manufacturer-Specific Data**: Integration with vendor databases for precise valve characteristics
- **Travel-Dependent Performance**: Coefficient curves based on actual valve test data
- **Material Compatibility Database**: Comprehensive material selection with compliance checking

#### Advanced Analysis
- **Gas Flow Enhancements**: Mach number, Reynolds number, and choking analysis
- **Valve Authority Calculation**: System pressure drop interaction analysis
- **Comprehensive Material Selection**: Service-specific recommendations with testing requirements
- **Enhanced Reporting**: Professional PDF reports with detailed technical analysis

### Installation

1. Install Python 3.8 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

```bash
streamlit run app.py
```

### Standards Compliance

- ISA S75.01 / IEC 60534-2-1 (Flow Equations)
- ISA RP75.23 (Cavitation Evaluation)
- IEC 60534-8-3 (Noise Prediction)
- API 6D (Pipeline Valves)
- NACE MR0175 (Sour Service)
- ASME B16.34 (Valve Design)

### Technical Enhancements Over Standard Version

1. **Cavitation Analysis**: Replaced simplified calculation with full ISA RP75.23 five-level sigma methodology
2. **Reynolds Correction**: Added FR factor calculation for viscous flow conditions
3. **Actuator Sizing**: Enhanced with proper safety factors (1.5-2.0) and spring force calculations
4. **Noise Prediction**: Options for both simplified estimation and detailed IEC 60534-8-3 analysis
5. **Valve Selection**: Industry-standard opening validation and multi-scenario analysis
6. **Material Selection**: Comprehensive database with service-specific recommendations
7. **Vendor Integration**: Support for manufacturer-specific valve data and characteristics

### Professional Use

This application is designed for professional engineers and should be used in conjunction with manufacturer-specific software for final valve selection. While the calculations follow industry standards, final selections should always be verified against specific service conditions and manufacturer recommendations.

### Version Information

Enhanced Valve Sizing Application v2.0
Professional-Grade Implementation
