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

def setProjsettings():
    try:
        import sgtk
        #get context from shotgun 
        # get the engine we are currently running in
        currentEngine = sgtk.platform.current_engine()

        # get the current context so we can find the highest version in relation to the context
        ctx = currentEngine.context
        
        # Get a template object using the name of the template
        template = currentEngine.sgtk.templates["nuke_shot_work"]

        # Now resolve the fields needed to build the template path using the context
        fields = ctx.as_template_fields(template,validate=True)

        #setLUT = 'Shot_%s' %fields['Shot']

        os.environ["SHOT"] = fields['Shot']

        #Set proj settings
        n = nuke.root()
        if 'theWitcher' in n['name'].value():
            n['fps'].setValue(24)
            n['colorManagement'].setValue('OCIO')
            theWitcher4k = '4268 2400 theWitcher 4k'
            nuke.addFormat( theWitcher4k )
            n['format'].setValue('theWitcher 4k')
        #Set VIEWER_INPUT
            try:
                vi = nuke.toNode('VIEWER_INPUT')
                vi['out_colorspace'].setValue('ShotGrades')
            except:
                pass
    except:
        pass
    


nuke.addOnScriptLoad(setProjsettings)



##delete viewers on startup
def killViewers():
    for v in nuke.allNodes("Viewer"):
        nuke.delete(v) 
nuke.addOnScriptLoad(killViewers)

