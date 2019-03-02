import os
import nuke

##import python scripts
import opendir
import backdropWithLabel
import createProjectorCam
import readLastRender
import openDJV
import setPathTab
import animatedSnap3D


## Nodes Menu
topMenu = nuke.menu("Nuke")
primaryMenu = topMenu.addMenu("PrimaryVFX")

##PrimaryVFX plugz

primaryMenu.addCommand('Open Explorer', 'opendir.openInExplorer()', 'shift+e')
primaryMenu.addCommand('Open DJV', 'openDJV.openReadInDJV()', 'shift+r')
primaryMenu.addCommand('Render Path Tab', 'setPathTab.setPathTab()', 'shift+w') 
#primaryMenu.addCommand('Load Render', 'readLastRender.getSequence()', 'alt+r')
primaryMenu.addCommand('Utils/Backdrop With Label', 'backdropWithLabel.customBackdrop()', 'alt+b', icon='Backdrop.png')  
primaryMenu.addCommand('Utils/Create Projector Camera', 'createProjectorCam.createProjectorCam()')

## shared_toolsets
# SharedToolSets setup folder

import sys
if nuke.GUI:

  import shared_toolsets
  
  sharedToolSetsPaths = {
    "linux2" : "/mnt/some/nice/place/SharedToolSets",   #LINUX
    "win32"  : "C:/appLibrary/nuke/NUKE_PATH/SharedToolSets",     #WINDOWS
    "darwin" : "/Volume/some/nice/place/SharedToolSets" #MACOS
  }

  def toolSetsFilenameFilter(filename):
      if nuke.env['MACOS']:
          # uppercase
          filename = filename.replace( 'P:', '/Volumes/Project' )
          # lowercase
          filename = filename.replace( 'p:', '/Volumes/Project' )
      elif nuke.env['WIN32']:
          # lowercase
          filename = filename.replace( 'D:', 'C:' )
          filename = filename.replace( '/Volumes/Project', 'P:' )
      elif nuke.env['LINUX']:
          filename = filename.replace( 'P:', '/mnt/project' )
          filename = filename.replace( '/Volumes/Project', '/mnt/project' )
      return filename

  platform = sys.platform

  sharedToolSetsPath = sharedToolSetsPaths[platform]
  shared_toolsets.setSharedToolSetsPath(sharedToolSetsPath)
  shared_toolsets.addFileFilter(toolSetsFilenameFilter)

  toolbar = nuke.menu("Nodes")
  shared_toolsets.createToolsetsMenu(toolbar)
