import os, nuke

def targetNode():
    n=nuke.selectedNode()
    nodeName = n['name'].value()
    return nodeName

# get path fragments values from file name
def getFilePathInfo():

    fullPath = nuke.Root().knob('name').getValue()
    pathFragments = fullPath.split('/')
    baseDir = '/'.join(pathFragments[:-2])+'/renders/'
    basename = os.path.basename(fullPath)
    name = os.path.splitext(basename)[0]
    nameFragments = name.split('_')
    numberFormat = "%04d"

    #get show,scene,shot,layer,version from script name
    try:
        if len(nameFragments) == 3:
            show,shot,version = name.split('_')
            layer = ''
            scene = ''

        elif len(nameFragments) == 4:
            show,shot,layer,version = name.split('_')
            scene = ''

        elif len(nameFragments) == 5:
            show,scene,shot,layer,version = name.split('_')

        return baseDir,show,scene,shot,layer,version

    except:
        nuke.message('Script not saved in proper format\n\nRequires script to named in one of the following formats:\n\n "show_scene_shot_layer_version"\n "show_shot_layer_version"\n "show_shot_version"')
          

def createPathTab(selection):    
    #get this py script name for use in the reset button
    thisFile = os.path.basename(__file__).split('.')[0]
    for n in selection:
        if 'Render Path' not in n.knobs():
            tabKnob = nuke.Tab_Knob('Render Path')
            showKnob = nuke.EvalString_Knob('showKnob', 'show')
            lockShow = nuke.Boolean_Knob('lockShow', 'lock')
            sceneKnob = nuke.EvalString_Knob('sceneKnob', 'scene')
            lockScene = nuke.Boolean_Knob('lockScene', 'lock')
            shotKnob = nuke.EvalString_Knob('shotKnob', 'shot')
            lockShot = nuke.Boolean_Knob('lockShot', 'lock')
            layerKnob = nuke.EvalString_Knob('layerKnob', 'layer')
            lockLayer = nuke.Boolean_Knob('lockLayer', 'lock')
            versionKnob = nuke.EvalString_Knob('versionKnob', 'version')
            lockVersion = nuke.Boolean_Knob('lockVersion', 'lock')
            fileTypeKnob = nuke.Enumeration_Knob('fileTypeKnob', 'file type', ['cin', 'dpx', 'exr', 'hdr', 'jpeg', 'mov', 'null', 'pic', 'png', 'sgi', 'targa', 'tiff', 'xpm', 'yuv'])
            lockFileType = nuke.Boolean_Knob('lockFileType', 'lock')
            folderKnob = nuke.Enumeration_Knob('folderKnob', 'folder', ['none', 'OUT', 'WIP', 'PRECOMP', 'PLATES','CUSTOM'])
            customFolderKnob = nuke.EvalString_Knob('customFolderKnob', 'custom')
            lockFolder = nuke.Boolean_Knob('lockFolder', 'lock')
            baseDirKnob = nuke.File_Knob('baseDirKnob', 'base directory')
            lockDir = nuke.Boolean_Knob('lockDir', 'lock')
            subFolder = nuke.Boolean_Knob('subFolder', 'save in sub folder')
            pathKnob = nuke.EvalString_Knob('pathKnob', 'path')
            lockPath = nuke.Boolean_Knob('lockPath', 'lock')
            resetButtonKnob = nuke.PyScript_Knob('resetButton', 'reset', '%s.updatePathFragments()' % thisFile)
            dividerFolderKnob = nuke.Text_Knob('','<b>folder options','')
            dividerPathKnob = nuke.Text_Knob('','<b>generated path','')
    
            for k in [tabKnob, showKnob, lockShow, sceneKnob, lockScene, shotKnob, lockShot, layerKnob, lockLayer, versionKnob, lockVersion, fileTypeKnob, lockFileType, dividerFolderKnob, folderKnob, customFolderKnob, lockFolder, subFolder, baseDirKnob, dividerPathKnob, lockDir, pathKnob, lockPath, resetButtonKnob]:
                n.addKnob(k)

            #make custom folder knob invisible. Made visible if folderKnob is set to 'CUSTOM'
            n['customFolderKnob'].setVisible(False)
            n['customFolderKnob'].clearFlag(nuke.STARTLINE)
            
            #move these to new lines
            n['subFolder'].setFlag(nuke.STARTLINE)
            n['resetButton'].setFlag(nuke.STARTLINE)
            
            setPathTab()
    
### set path fragments 
def setPathTab():
    baseDir,show,scene,shot,layer,version = getFilePathInfo()

    # standard values for creation
    fileType = "dpx"
    folder = "none"

    selection = nuke.selectedNodes('Write')
    if selection == []:
        nuke.message('Please select a Write node')

    for n in selection:
        if 'Render Path' in n.knobs():
            # if knobs are present try to update what's not been locked
       
            if n['lockShow'].value() == 0:
                n['showKnob'].setValue(show)

            if n['lockScene'].value() == 0:
                n['sceneKnob'].setValue(scene)

            if n['lockShot'].value() == 0:
                n['shotKnob'].setValue(shot)

            if n['lockLayer'].value() == 0:
                n['layerKnob'].setValue(layer)

            if n['lockVersion'].value() == 0:
                n['versionKnob'].setValue(version)

            if n['lockFileType'].value() == 0:
                n['fileTypeKnob'].setValue(fileType)

            if n['lockFolder'].value() == 0:
                n['folderKnob'].setValue(folder)

            if n['lockDir'].value() == 0:
                n['baseDirKnob'].setValue(baseDir)

            updatePath(n)
            
        else:
            createPathTab(selection)


def updatePath(n):

    renderDir = n['baseDirKnob'].value()

    #folderknob -- if set to custom show custom text knob otherwise hide it
    if n['folderKnob'].value() != 'none':
        if n['folderKnob'].value() == 'CUSTOM':
            n['customFolderKnob'].setVisible(True)
            n['customFolderKnob'].setFlag(nuke.STARTLINE)
            rFolder = n['customFolderKnob'].value()+'/'
        elif n['folderKnob'].value() != 'CUSTOM':
            n['customFolderKnob'].setVisible(False)
            n['customFolderKnob'].clearFlag(nuke.STARTLINE)
            rFolder = n['folderKnob'].value()+'/'
    else:
        rFolder = ''
        n['customFolderKnob'].setVisible(False)
        n['customFolderKnob'].clearFlag(nuke.STARTLINE)

    # check if path fragment is empty and assign value to render path fragment
    #show
    if n['showKnob'].value() != '':
        rShow = n['showKnob'].value() + '_'
    else:
        rShow = n['showKnob'].value()

    #scene
    if n['sceneKnob'].value() != '':
        rScene = n['sceneKnob'].value() + '_' 
    else:
        rScene = n['sceneKnob'].value()

    #shot
    if n['shotKnob'].value() != '':
        rShot = n['shotKnob'].value() + '_' 
    else:
        rShot = n['shotKnob'].value()

    #layer
    if n['layerKnob'].value() != '':
        rLayer = n['layerKnob'].value() + '_' 
    else:
        rLayer = n['layerKnob'].value()

    #version
    if n['versionKnob'].value() != '' and n['fileTypeKnob'].value().lower() !='mov':
        rVersion = n['versionKnob'].value() + '_' 
    else:
        rVersion = n['versionKnob'].value()

    #version for folder path
    rfVersion = n['versionKnob'].value()
    
    #file type
    rFileType = n['fileTypeKnob'].value()

    #frame padding
    numberFormat = "%04d"

    # build render path
    if n['lockPath'].value() == 0:
        if n['fileTypeKnob'].value().lower() != 'mov':
            if n['subFolder'].value() == 0:
                rPath = renderDir + rFolder + rShow + rScene + rShot + rLayer + rVersion + numberFormat + '.' + rFileType
            else:
                rPath = renderDir + rFolder + rShow + rScene + rShot + rLayer + rfVersion + '/' + rShow + rScene + rShot + rLayer + rVersion + numberFormat + '.' + rFileType
        else:
            if n['subFolder'].value() == 0:
                rPath = renderDir + rFolder + rShow + rScene + rShot + rLayer + rVersion + '.' + rFileType
            else:
                rPath = renderDir + rFolder + rShow + rScene + rShot + rLayer + rfVersion + '/' + rShow + rScene + rShot + rLayer + rVersion + '.' + rFileType
    
    n['pathKnob'].setValue(rPath)
    n['file'].setValue(rPath)
    n['file_type'].setValue(rFileType)
        

def updatePathFragments():
    n = nuke.thisNode()
    n.setSelected(True)
    setPathTab()


def autoUpdatePath():
    n = nuke.thisNode()
    nn = n.name()
    tk = nuke.thisKnob().name()
    pathFrags = ['showKnob', 'sceneKnob', 'shotKnob', 'layerKnob', 'versionKnob',  'fileTypeKnob', 'folderKnob', 'customFolderKnob', 'subFolder', 'baseDirKnob', 'lockDir']
    if tk in pathFrags:
        updatePath(n)


nuke.addKnobChanged(autoUpdatePath, nodeClass='Write')