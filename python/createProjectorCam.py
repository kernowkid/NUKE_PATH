###this script would work only when a Camera node is selected at the moment you execute it
import nuke

def createProjectorCam():
    n = nuke.selectedNode()

    if 'Camera' in n.Class():
        n.setSelected(False)
        origCamName = str(n.name())
        xofset = n['xpos'].value() + 50
        yofset = n['ypos'].value() + 50
        curFrame = nuke.frame()

        ##add user tab with framehold controls
        frameHoldTab = nuke.Tab_Knob('frameHoldTab', 'frame hold')
        frameHoldKnob = nuke.Int_Knob('frameHold', 'frame')
        createFh = nuke.PyScript_Knob('createFrameHold', 'create linked FrameHold node')
        createFh.setCommand( 'tn = nuke.thisNode()\nln = tn.name()\nxp=tn[\'xpos\'].value()+100\nyp=tn[\'ypos\'].value()+20\nfh = nuke.createNode(\'FrameHold\')\nfh.setInput(0, None)\nfh[\'tile_color\'].setValue(4259839)\nfh[\'xpos\'].setValue(xp)\nfh[\'ypos\'].setValue(yp)\nfh[\'first_frame\'].setExpression(\'%s.frameHold\' %ln) ' )

        projCam = nuke.createNode('Camera2')
        projCam.addKnob(frameHoldTab)
        projCam.addKnob(frameHoldKnob)
        projCam.addKnob(createFh)
        projCam['frameHold'].setValue(curFrame)

        ##link knobs to selected camera
        for i in ['translate', 'rotate', 'scaling', 'focal', 'haperture', 'vaperture', 'near', 'far', 'winroll',
                  'focal_point', 'fstop']:
            cp = n[i].name()
            projCam['%s' % cp].setExpression('%s.%s(frameHold)' % (origCamName, cp))

        ##make projection camera blue and offset it's position
        projCam.setInput(0, None)
        projCam['xpos'].setValue(xofset)
        projCam['ypos'].setValue(yofset)
        projCam['tile_color'].setValue(4259839)
        projCam['gl_color'].setValue(4259839)
        projCam['label'].setValue('Projector from %s\nframe [value knob.frameHold]' % origCamName)

    else:
        nuke.message('Please select a camera')
