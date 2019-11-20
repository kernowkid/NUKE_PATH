import sgtk

def sgWriteConvert():
    eng = sgtk.platform.current_engine()
    app = eng.apps["tk-nuke-writenode"]
    if app:
        app.convert_to_write_nodes()