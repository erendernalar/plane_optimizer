from xflrpy import xflrClient, enumApp, Plane, WingSection, WPolar, enumPolarType, AnalysisSettings3D, enumWPolarResult, enumAnalysisMethod
import time
import msgpackrpc  # Importing msgpackrpc to handle TransportError

# Change these values accordingly
# Using a valid path is your responsibility
project_name = "hasan.xfl"
project_path = "/home/linux/Desktop/xflr/"

# Define wing span range and increment
min_wing_span = 2.4
max_wing_span = 3.6
wing_span_increment = 0.2

# Define chord range and increment
min_chord = 0.1
max_chord = 0.3
chord_increment = 0.05

# Fixed twist value (since we are removing the iteration over twist)
twist_value = 0

xp = xflrClient(connect_timeout=100)

# Gives useful information about the mainframe class in xflr5
print(xp.state)

# Load project
xp.loadProject(project_path + project_name)

# Switch to XFOILANALYSIS application to get the foils
xp.setApp(enumApp.XFOILANALYSIS)
xfoil_analysis = xp.getApp()

# Get all foil names
foil_dict = xfoil_analysis.foil_mgr.foilDict()
foil_names = foil_dict.keys()

# Switch to MIAREX application for 3D analysis
xp.setApp(enumApp.MIAREX)
miarex = xp.getApp()

# To store results
results_list = []

# Iterate over wing span
span_value = min_wing_span
while span_value <= max_wing_span:
    # Iterate through each airfoil
    for foil_name in foil_names:
        # Iterate over chord value
        chord_value = min_chord
        while chord_value <= max_chord:
            # Calculate the aspect ratio
            wing_area = span_value * chord_value
            aspect_ratio = span_value**2 / wing_area

            # Create a new custom plane
            plane_name = f"custom_plane_{span_value}_{chord_value}_{twist_value}_{foil_name}"
            plane = Plane(name=plane_name)

            # Define wing sections
            sec0 = WingSection(y_position= 0,chord=chord_value, right_foil_name=foil_name, left_foil_name=foil_name, offset=0, dihedral=0, twist=twist_value)
            sec1 = WingSection(y_position=span_value / 2, chord=chord_value, offset=0, twist=twist_value, dihedral=0, right_foil_name=foil_name, left_foil_name=foil_name)

            # Add sections to the wing
            plane.wing.sections.append(sec0)
            plane.wing.sections.append(sec1)

            # Add the new plane to the plane manager
            miarex.plane_mgr.addPlane(plane)


            # Get plane data
            plane_data = miarex.plane_mgr.getPlaneData(plane_name)

            # Define a new polar for the plane
            wpolar_name = f"polar_{span_value}_{chord_value}_{twist_value}_{foil_name}"
            wpolar = WPolar(name=wpolar_name, plane_name=plane_name)
            wpolar.spec.polar_type = enumPolarType.FIXEDSPEEDPOLAR
            wpolar.spec.free_stream_speed = 25
            wpolar.spec.analysis_method = enumAnalysisMethod.LLTMETHOD

            # Define the analysis
            miarex.define_analysis(wpolar=wpolar)

            # Analysis settings
            analysis_settings = AnalysisSettings3D(is_sequence=False, sequence=(0, 10, 1))

            # Perform the analysis with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    time.sleep(1)
                    results = miarex.analyze(wpolar_name, plane_name, analysis_settings, result_list=[enumWPolarResult.ALPHA, enumWPolarResult.CLCD, enumWPolarResult.FZ])
                    
                    # Debug print to check the raw results
                    print(f"Raw results for span {span_value}, chord {chord_value}, twist {twist_value}, airfoil {foil_name}:")
                    print(results)

                    # Extract ALPHA, CL/CD, and FZ values
                    alpha_values = results.alpha
                    clcd_values = results.ClCd
                    fz_values = results.Fz

                    # Ensure the fz values are greater than 160
                    for alpha, clcd, fz in zip(alpha_values, clcd_values, fz_values):
                        if fz > 160:
                            results_list.append((span_value, chord_value, twist_value, foil_name, alpha, clcd, fz, aspect_ratio))
                    
                    # Print processed results
                    print(f"Processed results for span {span_value} meters, chord {chord_value} meters, twist {twist_value} degrees, and airfoil {foil_name}:")
                    print(f"Alpha: {alpha_values}, CL/CD: {clcd_values}, FZ: {fz_values}")
                    break  # Break if analysis is successful
                except msgpackrpc.error.TransportError as e:
                    print(f"Error: {e}. Retrying {attempt + 1}/{max_retries}...")
                    time.sleep(1)  # Wait a bit before retrying
            else:
                print(f"Failed to analyze {foil_name} at span {span_value}, chord {chord_value}, and twist {twist_value} after {max_retries} attempts.")
            
            # Increment chord value
            chord_value += chord_increment

    # Increment wing span value
    span_value += wing_span_increment

# Sort results by CL/CD value in descending order
sorted_results = sorted(results_list, key=lambda x: x[5], reverse=True)

# Get the top 10 results
top_10_results = sorted_results[:10]

# Print the top 10 results
print("Top 10 CL/CD values and corresponding configurations with FZ values greater than 160:")
for i, result in enumerate(top_10_results, start=1):
    span, chord, twist, foil, alpha, clcd, fz, aspect_ratio = result
    print(f"{i}. CL/CD: {clcd}, FZ: {fz} | Span: {span}m, Chord: {chord}m, Twist: {twist}°, Airfoil: {foil}, Alpha: {alpha}°, Aspect Ratio: {aspect_ratio}")

# Find the highest CL/CD value and corresponding wing span, chord, twist, airfoil, alpha, and aspect ratio
max_result = sorted_results[0]
max_span, max_chord, max_twist, max_foil_name, max_alpha, max_clcd, max_fz, max_aspect_ratio = max_result

print(f"\nThe highest CL/CD value is {max_clcd} with FZ value {max_fz} for a wing span of {max_span} meters, chord {max_chord} meters, twist {max_twist} degrees, airfoil {max_foil_name}, alpha {max_alpha} degrees, and aspect ratio {max_aspect_ratio}.")
