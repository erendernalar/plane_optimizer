from xflrpy import xflrClient, enumApp, WPolar, enumPolarType, AnalysisSettings3D, enumWPolarResult, enumAnalysisMethod
import os
import time
import xml.etree.ElementTree as ET
import msgpackrpc  # Importing msgpackrpc to handle TransportError

# Change these values accordingly
# Using a valid path is your responsibility
project_name = "hasan.xfl"
project_path = "/home/linux/Desktop/xflr/"
xml_folder_path = "/home/linux/Desktop/xflr/planes/"  # Folder containing XML files

xp = xflrClient(connect_timeout=100)

# Gives useful information about the mainframe class in xflr5
print(xp.state)

# Load project
xp.loadProject(project_path + project_name)

# Switch to MIAREX application for 3D analysis
xp.setApp(enumApp.MIAREX)
miarex = xp.getApp()

# To store results
results_list = []

# List all XML files in the directory
xml_files = [f for f in os.listdir(xml_folder_path) if f.endswith('.xml')]

def parse_xml_for_geometry(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Assume that span is the distance from the first section's y_position to the last section's y_position * 2
    sections = root.findall(".//Section")
    if not sections:
        raise ValueError(f"No sections found in {xml_file_path}")

    span_value = 2 * float(sections[-1].find("y_position").text)
    chord_value = float(sections[0].find("Chord").text)  # Assuming uniform chord for simplicity

    return span_value, chord_value

for xml_file in xml_files:
    plane_name = os.path.splitext(xml_file)[0]
    xml_file_path = os.path.join(xml_folder_path, xml_file)

    try:
        span_value, chord_value = parse_xml_for_geometry(xml_file_path)
        wing_area = span_value * chord_value
        aspect_ratio = span_value ** 2 / wing_area

        # Define a new polar for the plane
        wpolar_name = f"polar_{plane_name}"
        wpolar = WPolar(name=wpolar_name, plane_name=plane_name)
        wpolar.spec.polar_type = enumPolarType.FIXEDSPEEDPOLAR
        wpolar.spec.free_stream_speed = 24
        wpolar.spec.analysis_method = enumAnalysisMethod.LLTMETHOD

        # Define the analysis
        miarex.define_analysis(wpolar=wpolar)

        # Analysis settings
        analysis_settings = AnalysisSettings3D(is_sequence=False, sequence=(0, 10, 1))

        # Perform the analysis with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(0.5)
                results = miarex.analyze(wpolar_name, plane_name, analysis_settings, result_list=[enumWPolarResult.ALPHA, enumWPolarResult.CLCD, enumWPolarResult.FZ])

                # Debug print to check the raw results
                print(f"Raw results for plane {plane_name}:")
                print(results)

                # Extract ALPHA, CL/CD, and FZ values
                alpha_values = results.alpha
                clcd_values = results.ClCd
                fz_values = results.Fz

                # Ensure the fz values are greater than 160
                for alpha, clcd, fz in zip(alpha_values, clcd_values, fz_values):
                    if fz > 180:
                        results_list.append((plane_name, alpha, clcd, fz, aspect_ratio))

                # Print processed results
                print(f"Processed results for plane {plane_name}:")
                print(f"Alpha: {alpha_values}, CL/CD: {clcd_values}, FZ: {fz_values}, Aspect Ratio: {aspect_ratio}")
                break  # Break if analysis is successful
            except msgpackrpc.error.TransportError as e:
                print(f"Error: {e}. Retrying {attempt + 1}/{max_retries}...")
                time.sleep(1)  # Wait a bit before retrying
        else:
            print(f"Failed to analyze {plane_name} after {max_retries} attempts.")
    except Exception as e:
        print(f"Failed to parse XML for plane {plane_name}: {e}")

# Sort results by CL/CD value in descending order
sorted_results = sorted(results_list, key=lambda x: x[2], reverse=True)

# Get the top 10 results
top_10_results = sorted_results[:30]

# Print the top 10 results
print("Top 10 CL/CD values and corresponding configurations with FZ values greater than 160:")
for i, result in enumerate(top_10_results, start=1):
    plane_name, alpha, clcd, fz, aspect_ratio = result
    print(f"{i}. CL/CD: {clcd}, FZ: {fz} | Plane: {plane_name}, Alpha: {alpha}°, Aspect Ratio: {aspect_ratio}")

# Find the highest CL/CD value and corresponding plane
max_result = sorted_results[0]
max_plane_name, max_alpha, max_clcd, max_fz, max_aspect_ratio = max_result

print(f"\nThe highest CL/CD value is {max_clcd} with FZ value {max_fz} for plane {max_plane_name} at alpha {max_alpha} degrees with an aspect ratio of {max_aspect_ratio}.")
