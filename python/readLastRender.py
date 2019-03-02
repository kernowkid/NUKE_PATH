
############
import nuke
import os
import os.path
import math
import glob
import re

def getSequence():

    ### create list of all nuke Write nodes a
    nodes = [n for n in nuke.selectedNodes() if n.Class() == 'Write']

    ### if nodes list is not empty
    if nodes != []:

        for r in nodes:
            
		##get the path and directory

		##get and set path
		path = r['file'].value()
		##get and setdirectory
		spl = path.split('/')[:-1]
		dir = '/'.join(spl)

		##create read node.

		##if path to file exists deselect the write node, leaving the nodes with unrendered paths selected
		if os.path.isdir(dir):
			n = nuke.nodes.Read(file = path)
			r['selected'].setValue(False)
	
			#position generated read below relavant Write/RenderFarmWrite node
			xp = r['xpos'].value()
			yp = r['ypos'].value() + 50
			n['xpos'].setValue(xp)
			n['ypos'].setValue(yp)
			
		##message to inform which read node has no file
		else:
			nuke.message("The path in %s file doesn't exist!" % r["name"].value())   

		##getting framerange from the directory
		if path:
			imgDir = os.path.dirname(path)
			
			if os.path.exists(imgDir):
				imgFiles = os.listdir(imgDir)
				sortList = sorted(imgFiles)
				firstFile = sortList[0]
				lastFile = sortList[-1]
				
				startFrame = int(firstFile.split('.')[-2])
				endFrame = int(lastFile.split('.')[-2])

				n.knob('first').setValue(startFrame)
				n.knob('last').setValue(endFrame)
			else:
				nuke.message("%s doesn't exisit, please double check" % imgDir)
		else:
			nuke.message("%s is not a path" % path)

    ## message to inform if nothing was selected 
    else:
        nuke.message('Please select a write node or nodes')
    
               
    
  