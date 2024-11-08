from xflrpy import xflrClient, enumApp
import os

# Change these values accordingly
# Using a valid path is your responsibility
project_name = "hasan.xfl"
project_path = "/home/linux/Desktop/xflr/planes"

# Define wing span range and increment
min_wing_span = 2
max_wing_span = 2.6
wing_span_increment = 0.1

# Define chord range and increment
min_chord = 0.2
max_chord = 0.3
chord_increment = 0.02

# Fixed twist value
twist_value = 0

# Template for the XML content
xml_template = """<explane version="1.0">
<Units>
<length_unit_to_meter>1</length_unit_to_meter>
<mass_unit_to_kg>0.453592</mass_unit_to_kg>
</Units>
<Plane>
<Name>{plane_name}</Name>
<Description/>
<Inertia/>
<has_body>false</has_body>
<wing>
<Name>Main Wing</Name>
<Type>MAINWING</Type>
<Color>
<red>179</red>
<green>150</green>
<blue>157</blue>
<alpha>255</alpha>
</Color>
<Description/>
<Position> 0, 0, 0</Position>
<Tilt_angle> 0.000</Tilt_angle>
<Symetric>true</Symetric>
<isFin>false</isFin>
<isDoubleFin>false</isDoubleFin>
<isSymFin>false</isSymFin>
<Inertia>
<Volume_Mass> 0.000</Volume_Mass>
</Inertia>
<Sections>
<Section>
<y_position> 0.000</y_position>
<Chord> {chord_value:.3f}</Chord>
<xOffset> 0.000</xOffset>
<Dihedral> 0.000</Dihedral>
<Twist> {twist_value:.3f}</Twist>
<x_number_of_panels>13</x_number_of_panels>
<x_panel_distribution>COSINE</x_panel_distribution>
<y_number_of_panels>19</y_number_of_panels>
<y_panel_distribution>INVERSE SINE</y_panel_distribution>
<Left_Side_FoilName>{foil_name}</Left_Side_FoilName>
<Right_Side_FoilName>{foil_name}</Right_Side_FoilName>
</Section>
<Section>
<y_position> {half_span:.3f}</y_position>
<Chord> {chord_value:.3f}</Chord>
<xOffset> 0.000</xOffset>
<Dihedral> 0.000</Dihedral>
<Twist> {twist_value:.3f}</Twist>
<x_number_of_panels>13</x_number_of_panels>
<x_panel_distribution>COSINE</x_panel_distribution>
<y_number_of_panels>5</y_number_of_panels>
<y_panel_distribution>UNIFORM</y_panel_distribution>
<Left_Side_FoilName>{foil_name}</Left_Side_FoilName>
<Right_Side_FoilName>{foil_name}</Right_Side_FoilName>
</Section>
</Sections>
</wing>
</Plane>
</explane>"""

# Define function to save XML file
def save_xml(plane_name, span_value, chord_value, twist_value, foil_name):
    half_span = span_value / 2
    xml_content = xml_template.format(
        plane_name=plane_name,
        chord_value=chord_value,
        twist_value=twist_value,
        foil_name=foil_name,
        half_span=half_span
    )
    xml_filename = os.path.join(project_path, f"{plane_name}.xml")
    with open(xml_filename, 'w') as xml_file:
        xml_file.write(xml_content)

# Initialize xflrClient
xp = xflrClient(connect_timeout=100)

# Load project
xp.loadProject(os.path.join(project_path, project_name))

# Switch to XFOILANALYSIS application to get the foils
xp.setApp(enumApp.XFOILANALYSIS)
xfoil_analysis = xp.getApp()

# Get all foil names
foil_dict = xfoil_analysis.foil_mgr.foilDict()
foil_names = foil_dict.keys()

# Iterate over wing span
span_value = min_wing_span
while span_value <= max_wing_span:
    # Iterate through each airfoil
    for foil_name in foil_names:
        # Iterate over chord value
        chord_value = min_chord
        while chord_value <= max_chord:
            # Create a new custom plane name
            plane_name = f"custom_plane_{span_value}_{chord_value}_{twist_value}_{foil_name}"

            # Save the XML file for this plane configuration
            save_xml(plane_name, span_value, chord_value, twist_value, foil_name)

            print(f"Created XML for plane with span {span_value} meters, chord {chord_value} meters, twist {twist_value} degrees, and airfoil {foil_name}.")

            # Increment chord value
            chord_value += chord_increment

    # Increment wing span value
    span_value += wing_span_increment

print("XML file creation process completed.")
