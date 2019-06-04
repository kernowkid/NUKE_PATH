import time
import shutil
import os
import nuke
from nuke import localization
from resources import resources
from PySide2 import QtWidgets, QtCore, QtGui
from LocalizePanelModel import LocalizeModel, LocalizeProxyModel, Status, Roles
from LocalizationHelpers import SignalHelper, IN_NUKE, IconPaths, SettingsKeys, NodeItem, logger
from LocalizePanelView import LocalizeView

# When Nuke launches and executes panel code in the startup workspace,
# the hiero package is not yet available, so delay the import a little.
if IN_NUKE:
    QtCore.QTimer.singleShot(1000, lambda: __import__('hiero'))
else:
    import hiero

def _open_delete_dialog():
    """Opens the 'delete unused local files' dialog"""
    import hiero
    hiero.ui.findMenuAction('foundry.project.clearlocalcacheNuke').trigger()

def _open_prefs():
    """Open the preferences panel at localization index.
    This is super hacky."""

    # open preferences window
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(obj, QtWidgets.QMenu):
            for act in obj.actions():
                if act.text() == ('Preferences...'):
                    act.trigger()
    
    # once it's open, find the widget
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if obj.objectName() == 'foundry.hiero.preferencesdialog':
            pref_widget = obj
            break
    
    # loop through the widget to find the tree view and it's model
    for w in pref_widget.children():
        if isinstance(w, QtGui.QStandardItemModel):
            model = w
        if w.isWidgetType() and not isinstance(w, QtWidgets.QDialogButtonBox):
            for cw in w.children():
                if isinstance(cw, QtWidgets.QTreeView):
                    tree_view = cw

    # find index for localization preferences and set it as current (which switches to the respective widget)
    def find_loc_index(parent=QtCore.QModelIndex()):
        for r in xrange(model.rowCount(parent)):
            index = model.index(r, 0, parent)
            if model.data(index) == 'Localization':
                tree_view.setCurrentIndex(index)
            if model.hasChildren(index):
                find_loc_index(index)
    find_loc_index()    

class LocalizePanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """Localization panel to monitor ongoing localization progress of all nodes"""
        super(LocalizePanel, self).__init__(parent)
        self.setObjectName('foundry.localization.localizationpanel')
        self.setWindowTitle('Localization Panel')
        settings_path = os.path.expanduser('~/.nuke/uistate.ini')
        self.settings = QtCore.QSettings(settings_path, QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)     
        self.setMinimumWidth(10)
        self.proxy_model = LocalizeProxyModel()
        self.model = LocalizeModel()
        self.proxy_model.setSourceModel(self.model)
        self.session_has_callbacks = None
        self.init_UI()
        self.__read_settings() # read uistate.ini
        self.__init_signal_helper()
        # Delay signal connection a little to ensure the Cache/Localization menu is fully loaded
        # so the panel can be connected to it's signals.
        QtCore.QTimer.singleShot(500, self.connect_signals)
        
    def __init_signal_helper(self):
        """Create a signal helper instance if it doesn't already exist.
        This is so we can have callbacks emit signals when things change in Nuke.
        Having a signal/slot flow makes it easier to keep multiple instances of the panel updated.
        """
        try:
            # check if signals instance already exists (this happens if multiple panel instances are created)
            nuke.localizationPanelSignals
        except:
            # create a new instance of the signal helper and connect it to the panel widget.
            # only happens once per Nuke session
            nuke.localizationPanelSignals = SignalHelper()

            # register a callbacks that will emit the signal helpers signals
            nuke.addKnobChanged(nuke.localizationPanelSignals.emit_state_changes, node=nuke.toNode('preferences'))
            nuke.addKnobChanged(nuke.localizationPanelSignals.emit_colour_pref_changes, node=nuke.toNode('preferences'))
        
    def __delete_all_local_files(self):
        """Deletes everything in the local cach path."""
        local_path = nuke.toNode('preferences')['localCachePath'].evaluate()
        if nuke.ask("@b;This will delete all localized files from \n{}\n\nYou can't undo this action!".format(local_path)):
            import shutil
            self.model.beginResetModel()
            localization.setMode('off')
            for file_name in os.listdir(local_path):
                file_path = os.path.join(local_path, file_name)
                try:
                    logger.debug('deleting: {}'.format(file_path))
                    if os.path.isfile(file_path):
                        # delete files
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        # delete directories recursively
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.error(e)
            
            # turn localisation off to avoid undoing the deleting of all files
            localization.setMode('off')
            localization.checkForUpdates()
            self.model.endResetModel()
            #self.model.dataChanged.emit(self.model.index(0,0), self.model)

    def __scroll_view(self, index):
        if self.autoScrollCB.isChecked():
            self.itemView.scrollTo(index, QtWidgets.QAbstractItemView.PositionAtTop)

    def __force_update_selected(self):
        if IN_NUKE:
            localization.forceUpdateSelectedNodes()
        else:
            # it's not possible to select bin items via Python in Hiero
            # so we have to do this manually
            selection = [self.proxy_model.mapToSource(i) for i in self.itemView.selectionModel().selectedRows(column=0)]
            for node in [self.model.data(i, Roles.ItemRole).readNode() for i in selection]:
                logger.debug('localizing %s', node.name())
                node.forceUpdateLocalization()

    def __set_mode(self, value):
        """Set localization mode (same as using the Cache menu)"""
        # update Nuke
        localization.setMode(str(value.lower()))
        # update panel UI
        logger.debug('disabling pause button: %s', value=='Off')
        # if the localization mode is off diasble pause and force widgets
        self.pauseBtn.setDisabled(value == 'Off')
        self.updateBtn.setDisabled(value == 'Off')
        self.__update_pause_icon()

    def __toggle_pause(self, value):
        """Pause/resume localization"""
        logger.debug('!! toggling pause state !! {}'.format(value))
        #self.pBar.setDisabled(value)
        #self.itemView.set_paused(value)
        self.pauseBtn.setChecked(value)
        #self.pauseBtn.setIcon(_get_pause_resume_icons(not value))
        if value:
            # pause localization
            localization.pauseLocalization()
        else:
            # resume localization
            localization.resumeLocalization()
        # update the buton icons
        self.__update_pause_icon()
        # redraw table view
        self.itemView.repaint()

    def __update_pause_btn(self, value):
        """Update the pause button without triggering any action.
        This is required to keep the button state in sync with Nuke's pause state
        """
        self.pauseBtn.blockSignals(True)
        self.pauseBtn.setChecked(value)
        self.__update_pause_icon()
        self.pauseBtn.blockSignals(False)
        
    def __update_pause_icon(self):
        """Set the icon for the pause button based on the button's state
        as well as the global localization mode.
        """
        if self.modeComboBox.currentText() == 'Off':
            if self.pauseBtn.isChecked():
                icon = IconPaths.ICON_UNPAUSE_DISABLED
            else:
                icon = IconPaths.ICON_PAUSE_DISABLED
        else:
            if self.pauseBtn.isChecked():
                icon = IconPaths.ICON_UNPAUSE
            else:
                icon = IconPaths.ICON_PAUSE
        self.pauseBtn.setIcon(QtGui.QIcon(icon))

    def __trigger_filter(self, act):
        """Manage actions' check states in filter menus, then trigger the proxy filter with the respective status list"""
        filter_actions = act.parent().actions()
        # manage menu check state
        if act is self.act_filter_all:
            # copy check state of "All" action to other actions
            [a.setChecked(act.isChecked()) for a in filter_actions if a is not act]

        elif act.isChecked():
            # if all items are checked or unchecked make sure the "All" option is checked
            self.act_filter_all.setChecked(len(list(set([a.isChecked() for a in filter_actions if a is not self.act_filter_all]))) == 1)

        elif not act.isChecked():
            # if any other action is unchecked uncheck "All" action as well
            self.act_filter_all.setChecked(False)

        # trigger proxy filter with new check states
        filter_data = [a.data() for a in filter_actions if a.isChecked() and a.data() is not None]
        self.proxy_model.set_current_filter([a.data() for a in filter_actions if a.isChecked()])
        # save settings to ~/.nuke/uistate.ini
        self.settings.setValue(SettingsKeys.filter, filter_data)

    def __read_settings(self):
        # filter menu
        try:
            filter_data = [int(v) for v in self.settings.value(SettingsKeys.filter)]
            [act.setChecked(act.data() in filter_data) for act in self.filterMenu.actions()]
            # if all items are checked or unchecked make sure the "All" option is checked
            self.act_filter_all.setChecked(len(list(set([a.isChecked() for a in self.filterMenu.actions() if a is not self.act_filter_all]))) == 1)
        except TypeError:
            # fallback to checking all filters
            [act.setChecked(True) for act in self.filterMenu.actions()]
            
        self.proxy_model.set_current_filter([a.data() for a in self.filterMenu.actions() if a.isChecked()])
        
        # columns
        header = self.itemView.horizontalHeader()
        try:
            column_data = [int(v) for v in self.settings.value(SettingsKeys.columns)]
            [header.setSectionHidden(i, i not in column_data) for i in xrange(header.count())]
        except TypeError:
            # fallback to checking all columns
            [header.setSectionHidden(i, False) for i in xrange(header.count())]

    def selection_changed(self, selected, deselected):
        if IN_NUKE:
            nuke.selectAll()
            nuke.invertSelection()
            for i in self.itemView.selectionModel().selectedRows(column=0):
                item = i.data(Roles.ItemRole)
                item.setSelected(True)
        else:
            # still trying to figure out how to do this in Hiero
            pass

    def connect_signals(self):
        """Connect internal signals and slots"""
        # row selection
        selectionModel = self.itemView.selectionModel()
        selectionModel.selectionChanged.connect(self.selection_changed)
        # pause action
        self.pauseBtn.toggled.connect(self.__toggle_pause)       
        # open prefs action
        self.prefBtn.clicked.connect(_open_prefs)
        # mode action
        self.modeComboBox.currentTextChanged.connect(self.__set_mode)       
        # filter action
        self.filterMenu.triggered.connect(self.__trigger_filter)
        # update actions
        self.act_forceUpdateAll.triggered.connect(localization.forceUpdateAll)
        #self.act_forceUpdateSelectedNodes.triggered.connect(localization.forceUpdateSelectedNodes)
        self.act_forceUpdateSelectedNodes.triggered.connect(self.__force_update_selected)
        self.act_forceUpdateOnDemand .triggered.connect(localization.forceUpdateOnDemand)

        # do the signals coming from Nuke
        if IN_NUKE:
            # ugly way to find the action since the hiero module is not available in time for
            # a docked panel in the startup workspace
            for act in nuke.menu('Nuke').findItem('Cache/Localization').action().menu().actions():
                if act.objectName() == 'foundry.project.localcachetoggleNuke':
                    pause_action = act
                    break
        else:
            pause_action = hiero.ui.findMenuAction('foundry.project.localcachetoggle')

        # connect signals for localization state and pause so they can stay in sync
        pause_action.toggled.connect(self.__update_pause_btn)
        nuke.localizationPanelSignals.modeChanged.connect(self.modeComboBox.setCurrentText)
        nuke.localizationPanelSignals.inputUpdated.connect(self.model.knob_cb_updates_row)
        # connect signals for colour preferences so changes are live
        nuke.localizationPanelSignals.new_color_values.connect(self.itemView.update_colours_from_prefs)
        # update panel UI to reflect current state
        self.modeComboBox.setCurrentText(localization.mode().capitalize())
        self.__update_pause_btn(localization.isLocalizationPaused())
        # auto scroll
        self.model.localizing_index.connect(self.__scroll_view)
        
        if IN_NUKE:
            # If we are in Nuke we can run the callbacks now because Nuke instantiates the panel on the fly
            # which means the required objects we want to connect are available.
            # In Hiero this is not run until a project has been loaded or a new one created.
            self.add_callbacks()
        
    def init_hiero_project(self, event):
        """Populate the panel after a project was loaded or created.
        Connected to events.EventType.kAfterProjectLoad and events.EventType.kAfterNewProjectCreated"""
        if event.project not in hiero.core.projects(hiero.core.Project.kStartupProjects) and event.project.name() != 'Tag Presets': # Why is the "Tag Presets" project not of type kStartupProjects?????
            # Remove OnCreate callback so it doesn't double up with the kAfterProjectLoad event
            all_clips = []
            for clip in event.project.clips():
                all_clips.extend([v.item() for v in clip.binItem().items()])
            
            logger.debug('Registering %s clips from loaded project "%s" (currently holding %s clips)', len(all_clips),
                                                                                                     event.project.name(),
                                                                                                     self.model.rowCount())
            for i, loaded_clip in enumerate(all_clips):
                self.model.add_item(NodeItem(loaded_clip.readNode(), loaded_clip))
                logger.debug('registered {}/{} clips'.format(i, len(all_clips)))

            logger.debug('Finished registering loaded clips')
            # make sure new clips will be added as well:
            if self.session_has_callbacks:
                logger.debug('Adding back onCreate callback that was temporarily removed')
                nuke.addOnCreate(nuke.localizationPanelSignals.register_node)
                logger.debug('Already registered all other callbacks, skipping...')
            else:
                self.add_callbacks()
                self.session_has_callbacks = True               

    def add_callbacks(self):
        """This is run after any clips in loaded projects are added to the model and
        deals with adding nodes/clips to the panel that the user creates during the session."""
        logger.debug('-' * 50)
        logger.debug('Connecting callbacks (should only ever happen once during a session)')
        logger.debug('-' * 50)

        nuke.addOnCreate(nuke.localizationPanelSignals.register_node)
        localization.addFileCallback(self.model.file_cb_updates_row)
        localization.addReadCallback(self.model.update_node_status)
        nuke.localizationPanelSignals.newItem.connect(self.model.add_item)
        nuke.addOnDestroy(self.model.remove_node)

    def remove_callbacks(self, event):
        """Connected to events.EventType.kBeforeProjectLoad to disable the onCreate callback,
        because in the case of a projectload the self.init_hiero_project method is responsible for dealing
        with the incoing nodes as well as adding the onCreate callaback back in when it's done"""
        logger.debug('Temporarily removing onCreate to avoid double up with kAfterProjectLoad event')
        nuke.removeOnCreate(nuke.localizationPanelSignals.register_node)        

    def init_UI(self):
        """Create all widgets and layouts"""
        # widgets
        self.modeComboBox = QtWidgets.QComboBox()
        self.updateBtn = QtWidgets.QPushButton('Force Update')
        self.pauseBtn = QtWidgets.QPushButton()
        self.pauseBtn.setCheckable(True)

        self.clearBtn = QtWidgets.QPushButton()
        self.clearBtn.setIcon(QtGui.QIcon(IconPaths.ICON_CLEAR_FILES))
        self.filterBtn = QtWidgets.QToolButton()
        self.filterBtn.setIcon(QtGui.QIcon(IconPaths.ICON_FILTER))
        self.filterBtn.setMinimumWidth(35)
        self.filterBtn.setStyleSheet('QToolButton::menu-indicator {subcontrol-position: center right; height: 7px}')
        self.filterBtn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.prefBtn = QtWidgets.QToolButton()
        self.prefBtn.setIcon(QtGui.QIcon(IconPaths.ICON_SETTINGS))
        #self.pBar = QtWidgets.QProgressBar()
        self.itemView = LocalizeView()
        self.itemView.setModel(self.proxy_model)
        self.autoScrollCB = QtWidgets.QCheckBox('Auto scroll to localizing files')
        self.autoScrollCB.setChecked(True)

        # tweak sizes so the widgets all line up vertically with Nuke's style
        self.modeComboBox.setMinimumHeight(self.updateBtn.sizeHint().height())
        self.pauseBtn.setMaximumSize(self.updateBtn.sizeHint())
        self.clearBtn.setMaximumSize(self.updateBtn.sizeHint())

        # mode menu
        self.modeLabel = QtWidgets.QLabel('Mode')
        self.modeComboBox.addItems(['On', 'Manual', 'Off'])

        # update menu
        self.updateMenu = QtWidgets.QMenu()
        self.act_forceUpdateAll = QtWidgets.QAction('All', self)
        self.act_forceUpdateSelectedNodes = QtWidgets.QAction('Selected', self)
        self.act_forceUpdateOnDemand = QtWidgets.QAction('On demand only', self)       
        self.updateMenu.addAction(self.act_forceUpdateAll)
        self.updateMenu.addAction(self.act_forceUpdateSelectedNodes)
        self.updateMenu.addAction(self.act_forceUpdateOnDemand)
        self.updateBtn.setMenu(self.updateMenu)

        # clear menu
        self.clearMenu = QtWidgets.QMenu()
        self.clearMenu.addAction(QtWidgets.QAction('All local files',    self, triggered=self.__delete_all_local_files))
        self.clearMenu.addAction(QtWidgets.QAction('Unused local files', self, triggered=_open_delete_dialog))
        self.clearBtn.setMenu(self.clearMenu)

        # filter menu
        self.filterMenu = QtWidgets.QMenu(self.filterBtn)
        self.act_filter_all           = QtWidgets.QAction('All',                 self.filterMenu, checkable=True)
        self.act_filter_in_progress   = QtWidgets.QAction('In Progress',         self.filterMenu, checkable=True)
        self.act_filter_up_to_date    = QtWidgets.QAction('Up to date',          self.filterMenu, checkable=True)
        self.act_filter_out_of_date   = QtWidgets.QAction('Out of date',         self.filterMenu, checkable=True)
        self.act_filter_from_source   = QtWidgets.QAction('Reading from source', self.filterMenu, checkable=True)
        self.act_filter_disabled      = QtWidgets.QAction('Disabled',            self.filterMenu, checkable=True)
        self.act_filter_not_localized = QtWidgets.QAction('Not Localized',       self.filterMenu, checkable=True)

        self.act_filter_in_progress.setData(Status.IN_PROGRESS)
        self.act_filter_up_to_date.setData(Status.UP_TO_DATE)
        self.act_filter_out_of_date.setData(Status.OUT_OF_DATE)
        self.act_filter_from_source.setData(Status.READ_FROM_SOURCE)
        self.act_filter_disabled.setData(Status.DISABLED)
        self.act_filter_not_localized.setData(Status.NOT_LOCALIZED)
        for act in (self.act_filter_all, self.act_filter_in_progress, self.act_filter_up_to_date, self.act_filter_out_of_date,
                    self.act_filter_from_source, self.act_filter_disabled, self.act_filter_not_localized):
            self.filterMenu.addAction(act)
        self.filterBtn.setMenu(self.filterMenu)

        # tooltips
        self.modeComboBox.setToolTip('Sets the global localization mode.\nThis is the same as using the options in the Cache/Localization/Mode menu.')
        self.updateBtn.setToolTip('Forces the update of localized files.\nThis is the same as using the options in the Cache/Localization/Force Update menu.')
        self.pauseBtn.setToolTip('Pauses/Resumes file localization.\nThis is the same as Cache/Localization/Pause.')
        self.clearBtn.setToolTip('''Allows for clearing localized files.\nTwo modes are supported:
        "All local files" - this will delete all files in {}
        "Unused local files" - this will only delete unused local files (same as Cache/Localization/Clear Unused Local Files)'''.format(nuke.toNode('preferences')['localCachePath'].evaluate()))
        self.filterBtn.setToolTip('Sets a view filter the table.')
        self.prefBtn.setToolTip('Open the preferences.')

        # layouts
        layout = QtWidgets.QVBoxLayout()
        btnLayout = QtWidgets.QHBoxLayout()
        btnLayout.addWidget(self.modeLabel)
        btnLayout.addWidget(self.modeComboBox)
        btnLayout.addWidget(self.updateBtn)
        btnLayout.addWidget(self.pauseBtn)
        btnLayout.addWidget(self.clearBtn)
        btnLayout.addStretch()
        btnLayout.addWidget(self.filterBtn)
        btnLayout.addWidget(self.prefBtn)
        layout.addLayout(btnLayout)
        #layout.addWidget(self.pBar)
        layout.addWidget(self.itemView)
        layout.addWidget(self.autoScrollCB)
        layout.setAlignment(self.autoScrollCB, QtCore.Qt.AlignRight)
        self.setLayout(layout)

    def update_list_view(self):
        """Updates the list view's status bars"""
        self.model.dataChanged.emit(self.model.index(0, 1),
                                    self.model.index(len(self.model.data_list), 1))
        #self.pBar.setValue(localization.localizationProgress() * 100)

    def sizeHint(self):
        return QtCore.QSize(600, 500)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication([])
    w = LocalizePanel()
    for n in nuke.allNodes():
        w.model.add_item(NodeItem(n, None))
    w.show()
    sys.exit(app.exec_())
