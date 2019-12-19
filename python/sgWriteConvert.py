import sgtk

def sgWriteConvert():
    try:
        eng = sgtk.platform.current_engine()
        app = eng.apps["tk-nuke-writenode"]
        if app:
            app.convert_to_write_nodes()
    except:
        nuke.message('No Shotgun Write nodes found')