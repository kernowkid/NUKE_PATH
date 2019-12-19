import os
import nuke

##import python scripts
import opendir
import backdropWithLabel
import createProjectorCam
import readLastRender
import setPathTab
import animatedSnap3D
import readFromWrite
import TrackToRoto
import openRV
import openDJV

#import shotgun api and tools
try:
    import sgtk
    import sgWriteConvert
except:
    pass

#import pixel fudger gizmos  
import pixelfudger

## Nodes Menu
topMenu = nuke.menu("Nuke")
primaryMenu = topMenu.addMenu("PrimaryVFX")

##PrimaryVFX plugz

#import shotgun tools
try:
    primaryMenu.addCommand('Convert SG Write Node ', 'sgWriteConvert.sgWriteConvert()', 'alt+w') 
except:
    pass
primaryMenu.addCommand('Open Explorer', 'opendir.openInExplorer()', 'shift+e')
primaryMenu.addCommand('Render Path Tab', 'setPathTab.setPathTab()', 'shift+w') 
primaryMenu.addCommand('Read from Write','readFromWrite.ReadFromWrite()','shift+r')
primaryMenu.addCommand('Open in RV','openRV.openReadInRV()','alt+r')
primaryMenu.addCommand('Open in DJV','openDJV.openReadInDJV()','alt+d')
primaryMenu.addCommand('Utils/Backdrop With Label', 'backdropWithLabel.customBackdrop()', 'alt+b', icon='Backdrop.png')  
primaryMenu.addCommand('Utils/Track To Roto', 'TrackToRoto.TrackToRoto()','alt+t')
primaryMenu.addCommand('Utils/Create Projector Camera', 'createProjectorCam.createProjectorCam()')


# DJV is a copyleft flipbook
os.environ['DJV_VIEW_EXECUTABLE'] = 'C:/Program Files/DJV-1.2.5-win64/bin/djv_view.exe'
import DJV
nukescripts.setFlipbookDefaultOption('flipbook', 'DJV')


##DEADLINE
import DeadlineNukeClient
menubar = nuke.menu("Nuke")
tbmenu = menubar.addMenu("&Thinkbox")
tbmenu.addCommand("Submit Nuke To Deadline", DeadlineNukeClient.main, "")


## shared_toolsets
# SharedToolSets setup folder

import sys
if nuke.GUI:

  import shared_toolsets
  
  sharedToolSetsPaths = {
    "linux2" : "/mnt/some/nice/place/SharedToolSets",   #LINUX
    "win32"  : "P:/Studio/software/appLibrary/nuke/NUKE_PATH/SharedToolSets",     #WINDOWS
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
