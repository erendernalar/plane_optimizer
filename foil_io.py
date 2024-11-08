from xflrpy import xflrClient, enumApp
import os
import matplotlib.pyplot as plt

# Change these values accordingly
# Using a valid path is your responsibility
project_path = "/home/linux/Desktop/xflr/airfoils/"

xp = xflrClient(connect_timeout=100)

# Gives useful information about the mainframe class in xflr5
print(xp.state)
xp.setApp(enumApp.DIRECTDESIGN) # set to airfoil design application

# Get a list of all .dat files in the project_path directory
airfoil_files = [f for f in os.listdir(project_path) if f.endswith('.dat') and os.path.isfile(os.path.join(project_path, f))]

# Load each airfoil file
for file_name in airfoil_files:
    file_path = os.path.join(project_path, file_name)
    xp.loadProject(file_path)

afoil = xp.getApp() # Get the current application

# Get all foil names and display them
foil_dict = afoil.foil_mgr.foilDict()
foil_names = list(foil_dict.keys())

print("Foil names:")
for name in foil_names:
    print(name)
