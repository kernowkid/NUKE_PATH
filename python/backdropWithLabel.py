import nuke
import nukescripts

def customBackdrop():
    n = len( nuke.selectedNodes() )
    if n == 0:
        nuke.message('No nodes selected')
    else:
        p = nuke.Panel('Create Backdrop for %s nodes' % n)
        #p.addNotepad('Add label', '')
        p.addSingleLineInput('Add label', '')
        p.addEnumerationPulldown('Font size', '12 24 44 100 200')
        p.addBooleanCheckBox('Bold', False)
        #p.addRGBColorChip('Colour', '1077952512')
        p.show()

        note = p.value('Add label')
        fSize = int(p.value('Font size'))
        #col = int(p.value('Colour'))
        col = nuke.getColor()
        
        ##build backdrop
        bd = nukescripts.autoBackdrop()
        bd['label'].setValue(note)
        bd['tile_color'].setValue(col)
        bd['note_font_size'].setValue(fSize)

        if p.value('Bold') == False:
            bd['note_font'].setValue('Verdana')
        else:
            bd['note_font'].setValue('Verdana Bold')