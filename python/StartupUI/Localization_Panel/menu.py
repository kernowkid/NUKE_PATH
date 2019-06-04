from LocalizationHelpers import IN_NUKE
if IN_NUKE: # prevent Hiero from running this code on startup
    import nukescripts
    from LocalizePanel import LocalizePanel

    # Add the panel to the main UI
    # Avoiding multiple instances of the panel
    nuke.localization_panel = LocalizePanel()
    
    class LocalizePanelWrapper(nukescripts.PythonPanel):
        def __init__(self):
            super(LocalizePanelWrapper, self).__init__(title='Localization Panel',
                                                       id='com.ohufx.LocalizePanel',
                                                       scrollable=False)
            self.pyKnob = nuke.PyCustom_Knob("", "", "pyKnob()")
            self.addKnob(self.pyKnob)
    
    class pyKnob(object):
        '''Custom knob to draw the PySide widget as the UI for the wrapper class'''
        
        def makeUI(self):
            return nuke.localization_panel
    
    def load_localization_panel():
        """Create an instance and load it as a panel, or re-use teh existing one """
        wrapper = LocalizePanelWrapper()
        return wrapper.addToPane()
    
    nukescripts.registerPanel('com.ohufx.LocalizePanel', load_localization_panel)
    nuke.menu('Pane').addCommand('Localization Panel', load_localization_panel)