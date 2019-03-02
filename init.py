import nuke

nuke.pluginAddPath("./gizmos")
nuke.pluginAddPath("./icons")
nuke.pluginAddPath("./python")
nuke.pluginAddPath("./tcl")


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
nuke.knobDefault("Write.exr.compression","0")
nuke.knobDefault("Write.create_directories","1") 

## Exposure Tool > Use stops instead of densities  
nuke.knobDefault("EXPTool.mode", "0")  

## RotoPaint > feather setting to smooth  
#nuke.knobDefault("RotoPaint.toolbox", '''clone {
#{ brush ltt 0 }
#{ clone ltt 0}
#}''')
nuke.knobDefault("RotoPaint.feather_type", "smooth")
nuke.knobDefault('RotoPaint.toolbox','createBezier')

##Roto feather setting to smooth 
nuke.knobDefault("Roto.feather_type", "smooth")

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


