import os
import nuke


toolbar = nuke.toolbar("Nodes")
moonrakerMenu = toolbar.addMenu("moonrakerMenu", icon="moonraker_plain.png")

# this gets the folder name that contains this menu.py file
here = os.path.dirname(__file__)

# iterate over all the files in this folder
for filename in os.listdir(here):
    # if the file does not end in gizmo then skip it and move on to the next
    if not filename.endswith("gizmo"):
        continue

    # gizmo name is the file name with the extension removed
    gizmo_name = filename.split(".")[0]

    # add this to the menu
    moonrakerMenu.addCommand(gizmo_name, 'nuke.createNode("%s")' % gizmo_name)

