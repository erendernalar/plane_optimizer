import os
import msgpackrpc.error
from xflrpy import xflrClient, enumApp, Polar, enumAnalysisMethod, AnalysisSettings3D,enumPolarType, AnalysisSettings2D, enumWPolarResult, enumSequenceType, enumPolarResult, WPolar
import sys
import logging
import msgpackrpc as rpc
import time
import subprocess
from colorlog import ColoredFormatter
import xml.etree.ElementTree as ET
import msgpackrpc 
#get current dicrectory
project_workspace = os.getcwd()


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

file_name = "test.xfl"
xflr_file_path = os.path.join(project_workspace, "xfl files" , file_name)

airfoils_folder_name = "airfoils"
airfoils_file_path = os.path.join(project_workspace, airfoils_folder_name)

xml_planes_folder_name = "planes"
xml_planes_folder_path = os.path.join(project_workspace, xml_planes_folder_name)

formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger("my_logger")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class xflrpyGUI:
    def __init__(self):
        self.program_path = "/home/eren/xflrpy/xflr5v6/xflrpy"
        self.xflrpy = xflrClient(connect_timeout=100)
        for _ in range(2):
            try:
                if self.xflrpy.ping():
                    logger.info("Connected to the GUI")
                    break
            except Exception as e:
                logger.warning(f"Connection attempt failed with error: {e}. Retrying...")
                time.sleep(2)
        else:
            logger.critical("xflrpy GUI unable to start!!! Trying to force start...")
            self.force_start_gui()

    def force_start_gui(self):
        try:
            self.process = subprocess.Popen([self.program_path], start_new_session=True)  # Start GUI without blocking
            logger.info("Program started successfully as a background process.")
            time.sleep(2)
            self.xflrpy = xflrClient(connect_timeout=100)
        except FileNotFoundError:
            logger.error(f"Could not find the program at {self.program_path}. Please check the path and try again.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    def force_stop_gui(self):
        self.process.kill()

    #### later change these functions to single fucntion which called gui_screen_set and take the object which contain avaible screen options###
    def screen_set_direct_foil_design(self):
        self.xflrpy.setApp(enumApp.DIRECTDESIGN)

    def screen_set_inverse_design(self):
        self.xflrpy.setApp(enumApp.DIRECTDESIGN)

    def screen_set_xfoil_direct_design(self):
        self.xflrpy.setApp(enumApp.XFOILANALYSIS)

    def screen_set_wing_design(self):
        self.xflrpy.setApp(enumApp.MIAREX)

    def screen_set_empty(self):
        self.xflrpy.setApp(enumApp.NOAPP)

    ###########

    def get_xfoil(self):
        return self.xflrpy.getApp(enumApp.XFOILANALYSIS)
    
    def get_miarex(self):
        return self.xflrpy.getApp(enumApp.MIAREX)

    def load_the_project(self, project_path):
        try:
            logger.info(f"Loading project from {project_path}..")
            self.xflrpy.loadProject(project_path, save_current=True)
            logger.info("Project loaded succesfully..")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Failed the load project {e}")

class TwoDAnalysis:
    def __init__(self, xflr_file: str, gui: xflrpyGUI):
        self.gui = gui
        self.xflr_file_path = xflr_file
        self.xdirect = self.gui.get_xfoil()
        self.foil_mgr = None
        self.settings = None
        # Reynolds numbers for analysis
        self.reynolds_nums = (30000, 40000, 60000, 80000, 100000, 130000, 160000, 200000, 300000, 500000, 1000000, 3000000)
    
    def get_all_foil_names(self):
        self.foil_dict = self.xdirect.foil_mgr.foilDict()
        return self.foil_dict.keys()
    
    def check_all_foil_names(self):
        foil_names = self.get_all_foil_names()
        total_count = len(foil_names)

        for name in foil_names:
            logger.info(name)

        logger.info(f"Total airfoils: {total_count}")

    def get_the_foil(self, foil_name):
        return self.xdirect.foil_mgr.getFoil(foil_name)

    def import_foils_from_folder(self, airfoils_folder_path):
        airfoil_files = [f for f in os.listdir(airfoils_folder_path) if f.endswith('.dat') and 
                        os.path.isfile(os.path.join(airfoils_folder_path, f))]
        for file_name in airfoil_files:
            file_path = os.path.join(airfoils_folder_path, file_name)
            self.gui.xflrpy.loadProject(file_path)

    def set_setting(self):
        # Set analysis settings
        self.settings = AnalysisSettings2D()
        self.settings.keep_open_on_error = False
        self.settings.is_sequence = True
        self.settings.sequence_type = enumSequenceType.ALPHA
        self.settings.sequence = (-20.0, 20.0, 0.5)  # start, end, delta
        self.settings.init_BL = True
        return self.settings

    def start_the_2d_analysis(self):
        self.my_settings = self.set_setting()
        for self.foil_name in self.get_all_foil_names():
             self.foil = self.get_the_foil(self.foil_name)

             for re in self.reynolds_nums:
                self.polar = Polar(name = f"{self.foil.name} {re}", foil_name=self.foil.name)
                self.polar.spec.reynolds = int(re)
                self.polar.spec.polar_type = enumPolarType.FIXEDSPEEDPOLAR

                self.xdirect.define_analysis(self.polar)
                logger.debug(self.my_settings)
                # Run the analysis
                self.polar.result = self.xdirect.analyze(self.my_settings, result_list=[enumPolarResult.ALPHA, enumPolarResult.CL])

                logger.debug(f"Analysis for {self.foil_name} at Reynolds number {re} completed.")

        logger.info("2d Analysis of the foils are completed!!")

class Three_D_Plane:
    def __init__(self):
        self.min_wing_span = None
        self.max_wing_span = None
        self.wing_span_increment = None
        self.min_chord = None
        self.max_chord = None
        self.chord_increment = None
        self.twist_value = None

    def set_wing_span(self, min_wing_span, max_wing_span, wing_span_increment):
        self.min_wing_span = min_wing_span
        self.max_wing_span = max_wing_span
        self.wing_span_increment = wing_span_increment

    def set_chord(self, min_chord, max_chord, chord_increment):
        self.min_chord = min_chord
        self.max_chord = max_chord
        self.chord_increment = chord_increment

    def set_twist(self, twist_value):
        self.twist_value = twist_value

    def get_properties(self):
        return {
            "min_wing_span": self.min_wing_span,
            "max_wing_span": self.max_wing_span,
            "wing_span_increment": self.wing_span_increment,
            "min_chord": self.min_chord,
            "max_chord": self.max_chord,
            "chord_increment": self.chord_increment,
            "twist_value": self.twist_value
        }

class XmlPlaneGenerator:
    def __init__(self, plane: Three_D_Plane, planes_file_path: str, airfols: TwoDAnalysis):
        self.airfoils = airfols
        self.planes_file_path = planes_file_path
        self.plane = plane
        self.min_wing_span = plane.min_wing_span
        self.max_wing_span = plane.max_wing_span
        self.wing_span_increment = plane.wing_span_increment
        self.min_chord = plane.min_chord
        self.max_chord = plane.max_chord
        self.chord_increment = plane.chord_increment
        self.twist_value = plane.twist_value
        self.xml_template = """<explane version="1.0">
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
        
    def save_to_xml(self, plane_name, span, chord, twist, airfoil):
        half_span = span / 2
        xml_content = self.xml_template.format(
            plane_name = plane_name,
            chord_value = chord,
            twist_value = twist,
            foil_name=airfoil,
            half_span=half_span
        )
        xml_filename = os.path.join(self.planes_file_path, f"{plane_name}.xml")
        with open(xml_filename, 'w') as xml_file:
            xml_file.write(xml_content)
            xml_file.close()

    def plane_generator(self):
        span_value = self.min_wing_span
        while span_value <= self.max_wing_span:
            for foil_name in self.airfoils.get_all_foil_names():
                chord_value = self.min_chord               
                while chord_value <= self.max_chord:
                    formatted_span_value = "{:.3f}".format(span_value)
                    formatted_chord_value = "{:.3f}".format(chord_value)
                    plane_name = f"{float(formatted_span_value)}_{formatted_chord_value}_{twist_value}_{foil_name}"
                    self.save_to_xml(plane_name, span_value, chord_value,twist_value,foil_name)
                    chord_value += self.chord_increment
            span_value += wing_span_increment
            

class ThreeDAnalysis:
    def __init__(self, gui: xflrpyGUI, foil: TwoDAnalysis, xml_folder_path):
        self.gui = gui
        self.foil = foil
        self.xml_folder_path = xml_folder_path
        self.xml_planes = None
        self.results_list = []
        
    def get_all_xml_planes(self):
        xml_planes = [f for f in os.listdir(self.xml_folder_path) if f.endswith('.xml')]
        return xml_planes

    def parse_single_xml_for_geometry(self, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        sections = root.findall(".//Section")
        if not sections:
            logger.critical(f"No sections found {self.xml_folder_path}")

        span_value = 2 * float(sections[-1].find("y_position").text)
        chord_value = float(sections[0].find("Chord").text)  
        return span_value, chord_value

    def ThreeDAnalysis(self):
        self.gui.screen_set_wing_design()
        miarex = self.gui.get_miarex()
        for xml_file in self.get_all_xml_planes():
            plane_name = os.path.splitext(xml_file)[0]
            xml_file_path = os.path.join(self.xml_folder_path, xml_file)

            try:
                span_value, chord_value = self.parse_single_xml_for_geometry(xml_file_path)
                wing_area = span_value * chord_value
                aspect_ratio = span_value ** 2 / wing_area

                wpolar_name = f"polar_{plane_name}"
                wpolar = WPolar(name=wpolar_name, plane_name=plane_name)
                wpolar.spec.polar_type = enumPolarType.FIXEDSPEEDPOLAR
                wpolar.spec.free_stream_speed = 24 ## make this variable
                wpolar.spec.analysis_method = enumAnalysisMethod.LLTMETHOD

                miarex.define_analysis(wpolar=wpolar)

                analysis_settings = AnalysisSettings3D(is_sequence=False, sequence=(0,10,1))

                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        time.sleep(0.5)
                        results = miarex.analyze(wpolar_name, plane_name, analysis_settings,
                                                result_list=[enumWPolarResult.ALPHA, enumWPolarResult.CLCD, enumWPolarResult.FZ]) #varible name can be confusing fix it later
                        
                        logger.debug(f"Raw results for plane {plane_name}:")
                        logger.debug(results)

                        alpha_values = results.alpha
                        clcd_value = results.ClCd
                        fz_value = results.FZ
                        
                        logger.info(fz_value)

                        for alpha, clcd , fz in zip(alpha_values, clcd_value, fz_value):
                            logger.info(fz)
                            if fz > 1: ## make this variable
                                self.results_list.append((plane_name, alpha, clcd, fz, aspect_ratio))#varible name can be confusing fix it later
                        break
                    except msgpackrpc.error.TransportError as e:
                        logger.warning(f"Error: {e}. Retrying {attempt + 1}/{max_retries}...")
                else:
                    logger.warning(f"Failed to analyze {plane_name} after {max_retries} attempts.")
            except Exception as e:
                logger.warning(f"Failed to parse XML for plane {plane_name}: {e}")

        return self.results_list #varible name can be confusing fix it later

class ResultViewer():
    def __init__(self):
        self.results = None
        self.sorted_results = None

    def load_the_results(self, results):
        logger.info(results)
        if results:
            self.results = results
        else:
            logger.critical("There is 0 possible planes based on constrains or there is error in contrains!!!")
            self.results = []

    def sort_the_results(self):
        self.sorted_results = sorted(self.results, key=lambda x: x[2], reverse=True)

    def top_10_result(self):
        top_10 = self.sorted_results[:10]
        return top_10

gui = xflrpyGUI()
gui.load_the_project(xflr_file_path)

analysisTwoD = TwoDAnalysis(xflr_file_path, gui)
# analysisTwoD.import_foils_from_folder(airfoils_file_path)
analysisTwoD.check_all_foil_names()

logger.info(analysisTwoD.get_all_foil_names())

# analysisTwoD.start_the_2d_analysis()

# my_plane = Three_D_Plane()
# my_plane.set_chord(0.2, 0.3, 0.1)
# my_plane.set_twist(0)
# my_plane.set_wing_span(1,1.2,0.2)


# PlaneGen = XmlPlaneGenerator(my_plane, xml_planes_folder_path, analysisTwoD)
# PlaneGen.plane_generator()

input("enter when ready")

threeD = ThreeDAnalysis(gui, analysisTwoD, xml_planes_folder_path)
results = threeD.ThreeDAnalysis()

resultviewer = ResultViewer()
resultviewer.load_the_results(results)
resultviewer.sort_the_results()
best = resultviewer.top_10_result()




























# for i, result in enumerate(top_10, start=1):
#     span, chord, twist, foil, alpha, clcd, fz, aspect_ratio = result
    # print(f"{i}. CL/CD: {clcd}, FZ: {fz} | Span: {span}m, Chord: {chord}m, Twist: {twist}°, Airfoil: {foil}, Alpha: {alpha}°, Aspect Ratio: {aspect_ratio}")

# max_result = sorted[0]
# max_span, max_chord, max_twist, max_foil_name, max_alpha, max_clcd, max_fz, max_aspect_ratio = max_result

# print(f"\nThe highest CL/CD value is {max_clcd} with FZ value {max_fz} for a wing span of {max_span} meters, chord {max_chord} meters, twist {max_twist} degrees, airfoil {max_foil_name}, alpha {max_alpha} degrees, and aspect ratio {max_aspect_ratio}.")
