from xflrpy import xflrClient, enumApp, Polar, enumPolarType, AnalysisSettings2D, enumSequenceType, enumPolarResult

# Change these values accordingly
# Using a valid path is your responsibility
project_name = "hasan.xfl"
project_path = "/home/linux/xflr/"

xp = xflrClient(connect_timeout=100)
# Load the project
xp.loadProject(project_path + project_name, save_current=False)

# Set the application to XFOILANALYSIS
xdirect = xp.getApp(enumApp.XFOILANALYSIS)

# Get all foil names
foil_dict = xdirect.foil_mgr.foilDict()
foil_names = foil_dict.keys()

# Reynolds numbers for analysis
reynolds_nums = (30000, 40000, 60000, 80000, 100000, 130000, 160000, 200000, 300000, 500000, 1000000, 3000000)

# Iterate through each airfoil
for foil_name in foil_names:
    foil = xdirect.foil_mgr.getFoil(foil_name)
    
    # Iterate through each Reynolds number
    for re in reynolds_nums:
        polar = Polar(name=f"{foil.name} {re}", foil_name=foil.name)
        polar.spec.reynolds = int(re)
        polar.spec.polar_type = enumPolarType.FIXEDSPEEDPOLAR
        
        # Define the analysis
        xdirect.define_analysis(polar)
        
        # Set analysis settings
        settings = AnalysisSettings2D()
        settings.keep_open_on_error = False
        settings.is_sequence = True
        settings.sequence_type = enumSequenceType.ALPHA
        settings.sequence = (-20.0, 20.0, 0.5)  # start, end, delta
        settings.init_BL = True
        
        # Run the analysis
        polar.result = xdirect.analyze(settings, result_list=[enumPolarResult.ALPHA, enumPolarResult.CL])
        
        # Optionally, print or save the results here
        print(f"Analysis for {foil_name} at Reynolds number {re} completed.")

# Display all foil names at the end
print("Foil names analyzed:")
for name in foil_names:
    print(name)
