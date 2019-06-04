from LocalizePanel import LocalizePanel
from LocalizationHelpers import IN_NUKE

#  add the panel to the main UI
from hiero.ui import windowManager
from hiero.core import events
## add panel to Hiero
localisation_panel = LocalizePanel()
wm = windowManager()
wm.addWindow(localisation_panel, wm.kApplicationSection)

events.registerInterest(events.EventType.kBeforeProjectLoad, localisation_panel.remove_callbacks)
events.registerInterest(events.EventType.kAfterProjectLoad, localisation_panel.init_hiero_project)
events.registerInterest(events.EventType.kAfterNewProjectCreated, localisation_panel.init_hiero_project)
