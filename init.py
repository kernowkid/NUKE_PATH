import nuke

nuke.pluginAddPath("./gizmos")
nuke.pluginAddPath("./gizmos/pixelfudger")
nuke.pluginAddPath("./icons")
nuke.pluginAddPath("./python")
nuke.pluginAddPath("./tcl")
nuke.pluginAddPath("./python/StartupUI/Localization_Panel/")


##rollingautosave
import rollingAutoSave

###########SET NODE KNOB DEFAULTS##########
## default format and frame rate
nuke.knobDefault('Root.fps', '25')
nuke.knobDefault("Camera2.frame_rate", "25")

## Project Settings > Default format: HD 1920x1080  
nuke.knobDefault('Root.format', 'HD_1080')  

## Viewer Settings > Optimize viewer during playback: on  
#nuke.knobDefault("Viewer.freezeGuiWhenPlayBack", "1")  

## Write > Default for EXR files: 16bit Half, No Compression. 'Create directories' checked as default   
#nuke.knobDefault("Write.exr.compression","0")
nuke.knobDefault("Write.create_directories","1") 

## Exposure Tool > Use stops instead of densities  
nuke.knobDefault("EXPTool.mode", "0")  

## RotoPaint > feather setting to smooth  
#nuke.knobDefault("RotoPaint.toolbox", '''clone {
#{ brush ltt 0 }
#{ clone ltt 0}
#}''')
nuke.knobDefault("RotoPaint.feather_type", "smooth")
nuke.knobDefault("RotoPaint.cliptype", "no clip")
nuke.knobDefault('RotoPaint.toolbox','createBezier')

##Roto feather setting to smooth 
nuke.knobDefault("Roto.feather_type", "smooth")
nuke.knobDefault("Roto.cliptype", "no clip")

##shuffle add 'value in' dispay to comment field 
nuke.knobDefault("Shuffle.label", '[value in]')

##scanline renderer extra channels off 
#nuke.knobDefault("ScanlineRender", '''MB_channel {
#{ "none" }
#{ "off" }
#}''')
#nuke.knobDefault("ScanlineRender.MB_channel","none")
nuke.knobDefault("ScanlineRender.motion_vectors_type","off")

##delete viewers on startup
def killViewers():
    for v in nuke.allNodes("Viewer"):
        nuke.delete(v)
nuke.addOnScriptLoad(killViewers)

##Project Settings
def setProjsettings():
    ##theWitcher
    n = nuke.root()
    if 'theWitcher' in n['name'].value():
        n['fps'].setValue(24)
        n['colorManagement'].setValue('OCIO')
        n['OCIO_config'].setValue('custom')
        n['customOCIOConfigPath'].setValue('P:/Projects/theWitcher/ingest/20190906_primary_TO_003/the_witcher_2100024_baked_ocio_configuration_2019-04-29/the_witcher_2100024_baked_ocio_configuration_2019-04-29/baked_config-win.ocio')
        theWitcher4k = '4268 2400 theWitcher 4k'
        nuke.addFormat( theWitcher4k )
        n['format'].setValue('theWitcher 4k')
nuke.addOnScriptSave(setProjsettings)

