import os
from xflrpy import xflrClient, enumApp, Polar, enumPolarType, AnalysisSettings2D, enumSequenceType, enumPolarResult
import sys
import logging
import msgpackrpc as rpc
import time
import subprocess
from colorlog import ColoredFormatter
#get current dicrectory
project_workspace = os.getcwd()
file_name = "hasan.xfl"

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


xflr_file_path = os.path.join(project_workspace, file_name)

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

gui = xflrpyGUI()

class TwoDAnalysis:
    def __init__(self, xflr_file: str, gui: xflrpyGUI):
        self.gui = gui
        self.xflr_file_path = xflr_file
        self.xdirect = None
        self.foil_mgr = None
        self.settings = None
        # Reynolds numbers for analysis
        self.reynolds_nums = (30000, 40000, 60000, 80000, 100000, 130000, 160000, 200000, 300000, 500000, 1000000, 3000000)

    def import_airfoils(self):
        self.gui.screen_set_wing_design()

    def load_the_project(self):
        try:
            logger.info(f"Loading project from {self.xflr_file_path}")
            self.gui.xflrpy.loadProject(self.xflr_file_path, save_current=True)
            self.xdirect = self.gui.xflrpy.getApp(enumApp.XFOILANALYSIS)
            logger.info("Project loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
    
    def get_foil_names(self):
        self.foil_dict = self.xdirect.foil_mgr.foilDict()
        return self.foil_dict.keys()
    
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
        for self.foil_name in self.get_foil_names():
             self.foil = self.xdirect.foil_mgr.getFoil(self.foil_name)

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

    def test(self):
        mia = self.gui.xflrpy.getApp()
        mia.plane_mgr.addPlane()

analysisTwoD = TwoDAnalysis(xflr_file_path, gui)

# analysisTwoD.load_the_project()

# logger.info(analysisTwoD.get_foil_names())

# analysisTwoD.start_the_2d_analysis()

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

my_plane = Three_D_Plane()
my_plane.set_wing_span(2,5,0.5)
my_plane.set_chord(0.2,0.3,0.5)
my_plane.set_twist(0)
logger.info(my_plane.get_properties())

class XmlPlaneGenerator:
    def __init__(self, plane: Three_D_Plane, planes_file_path: str):
        self.planes_file_path = planes_file_path
        self.plane = plane
        self.min_wing_span = plane.min_wing_span
        self.max_wing_span = plane.max_wing_span
        self.wing_span_increment = plane.wing_span_increment
        self.min_chord = plane.min_chord
        self.max_chrod = plane.max_chord
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
                            <x_panel_dispan_valueplane>"""
        
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
            for foil_name in self.foil_names:
                chord_value = self.min_chord
                while chord_value <= max_chord:
                    plane_name = f"candidate_{span_value}_{chord_value}_{twist_value}_{foil_name}"
                    self.save_to_xml(plane_name, span_value, chord_value,twist_value,foil_name)
                    chord_value += self.chord_increment
            span_value += wing_span_increment

class ThreeDAnalysis:
    def __init__(self, gui: xflrpyGUI):
        self.gui = gui
