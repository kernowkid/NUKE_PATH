import os
import time
import logging
import nuke
from PySide2 import QtGui, QtCore

IN_NUKE = not (nuke.env['hiero'] or nuke.env['studio'])

# When Nuke launches and executes panel code in the startup workspace,
# the hiero package is not yet available, so delay the import a little.

############# logging
#logging.basicConfig(filename='/tmp/localization_log', filemode='w')
logging.basicConfig()
logger = logging.getLogger('LocalizePanel')
logger.setLevel(logging.CRITICAL)
####################################################################################

def get_all_clips():
    """Get all clips from all open projects, including inactive version clips"""
    # the hiero package can't be imported at the top of this module as it is not available in time
    # when launching NukeStudio
    import hiero 
    all_clips = []
    clip_sets = [p.clips() for p in hiero.core.projects()]
    clip_bin_items = [clip.binItem() for clip_set in clip_sets for clip in clip_set]
    for bin_item in clip_bin_items:
        all_clips.extend([version.item() for version in bin_item.items()])
    return all_clips

class Worker(QtCore.QObject, QtCore.QRunnable):
    """Worker class to process in an extra background thread via the global event queue.
    Used to repeatedly try to find a node's clip until it exists."""
    preparedItem = QtCore.Signal(object)
    DELAY = 0.2 # seconds to wait after failed attempt to find node/clip pair before trying again
    MAX_TRIES = 10 # if this many tries still don't find a node's clip we assume it's a node in the NukeStudio DAG and retur None
                   # This is rather ugly but I don't see another way to differentiate between Nuke Read nodes and Hiero Read nodes
    
    def __init__(self):
        QtCore.QRunnable.__init__(self)
        QtCore.QObject.__init__(self)
        self.node = None
        self.all_clips = get_all_clips()

    def set_node(self, node):
        logger.debug('preparing to find clip for %s', node.name())
        self.node = node

    def run(self):
        """Try to get the clip that self.node belongs to until it's available."""
        success = False
        logger.debug('...clips list to search: %s', self.all_clips)
        tries = 0
        while not success:
            try:
                if tries < self.MAX_TRIES:
                    logger.debug('...trying to retrieve clip for %s...', self.node.name())
                    clip = [clip for clip in self.all_clips if clip.readNode() is self.node][0]
                    logger.debug('!!!!  FOUND CLIP: %s' % clip)
                else:
                    logger.debug('...Node has no Clip yet, MAX_TTRIES reached. Assuming NukeStudio DAG node and returning None for clip')
                    clip = None
                item = NodeItem(self.node, clip)
                success = True
                    
            except IndexError:
                logger.debug('...Node has no Clip yet, try again...')
                tries += 1
                time.sleep(self.DELAY)
                continue

            except RuntimeError:
                logger.debug('...A Clip has no Read yet, try again...')
                time.sleep(self.DELAY)
                continue
            except ValueError as e:
                if e.message == 'A PythonObject is not attached to a node':
                    logger.debug('Ignoring "PythonObject is not attached to a node" error')
                    continue
            except Exception as e:
                logger.debug('!'*50)
                logger.debug('Unexpected error in clip finder thread (Worker): %s', e.message)
                logger.debug('!'*50)
                break
            
        logger.debug('emitting clip signal with %s' % item)
        self.preparedItem.emit(item)

class IconPaths:
    """Just for dev. The icons should be part of Nuke's QResource for teh release"""
    ICON_CLEAR_FILES      = ':/clear_unused_local_files.png'
    ICON_FILTER           = ':/filter.png'
    ICON_PAUSE            = ':/pause.png'
    ICON_UNPAUSE          = ':/un_pause.png'
    ICON_PAUSE_DISABLED   = ':/disabled_pause.png'
    ICON_UNPAUSE_DISABLED = ':/disabled_un_pause.png'
    THUMB_3D              = ':/thumb_3D.png'
    THUMB_AUDIO           = ':/thumb_audio.png'
    THUMB_IMAGE           = ':/thumb_image.png'
    THUMB_VIDEO           = ':/thumb_video.png'
    THUMB_MISC            = ':/thumb_misc.png'
    THUMB_ERROR           = ':/thumb_error.png'
    THUMB_NUKE           = ':/thumb_nuke.png'
    ICON_SETTINGS         = ':qrc/images/SettingsButton.png'

class SettingsKeys:
    """The entry names for the uistate.ini"""
    filter  = 'LocalizePanel/filter'
    columns = 'LocalizePanel/columns'

class SignalHelper(QtCore.QObject):
    """Helper to provide signals that can be sent via callbacks which is more flexible than using the callbacks directly.
    This also acts as a relay for onCreate and addFileCallback so we can delay the reaction to a new node until it's clip exists as well.
    """
    modeChanged = QtCore.Signal(str)
    inputUpdated = QtCore.Signal(object)
    newItem = QtCore.Signal(QtCore.QObject)
    new_color_values = QtCore.Signal()
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.thread_pool = QtCore.QThreadPool()
        
    def emit_state_changes(self):
        """Emit a signal when knob values are changed in the Nuke UI that need to update the panel UI.
        This is used as a callback on the preferences node as well as evey incoming node.
        """
        knob = nuke.thisKnob()
        # preferences:
        if knob.name() == 'localizationMode':
            self.modeChanged.emit(knob.value().capitalize())

        # misc nodes
        if isinstance(nuke.thisKnob(), nuke.File_Knob): # is this check sufficient?
            logger.debug('Updating view because %s changed in %s', knob, nuke.thisNode().name())
            self.inputUpdated.emit(nuke.thisNode())

    def emit_colour_pref_changes(self):
        """Emit a signal when the localization colours are changed in the preferences
        so that the panel colours can update accordingly
        """
        knob = nuke.thisKnob()
        if knob.name() in ('localizationCompletedColor', 'localizationOutdatedColor', 'localizationProgressColor'):
            self.new_color_values.emit()

    def emit_new_item(self, item):
        """Pass signals from background threads to the main thread"""
        logger.debug('Received from background thread: %s', item)
        self.newItem.emit(item)

    def register_node(self):
        """Grab a new node and find it's corresponding clip object (in Hiero).
        Check if it should be part of the panel, if so, prep it and emit the required signals for the mode/view.
        This is added as a onCreate callback.
        """
        node = nuke.thisNode()
        logger.debug('checking node validity for %s', node.name())
        if not node.knob('localizationPolicy'):
            return      

        logger.debug('Adding knob changed callback to: %s', node.name())
        nuke.addKnobChanged(nuke.localizationPanelSignals.emit_state_changes, node=node)
        
        logger.debug('Trying to add a node via onCreate callback: %s', node.name())
        if IN_NUKE:
            # In Nuke just add any new nodes to the model straight away:
            item = NodeItem(node, None)
            self.emit_new_item(item)
            return
        else:
            # In Hiero we have to wait until a node's corresponding clip
            # object is available before we can add it to the model.
            # With large scripts it can take some time before the clip exists,
            # so we need to keep trying until we succeed
            # If there were a hiero.onClipCreate() callback this would be unnecessary
            
            logger.debug('active thread count ({}): {}/{}'.format(node.name(),
                                                                  QtCore.QThreadPool.globalInstance().activeThreadCount(),
                                                                  QtCore.QThreadPool.globalInstance().maxThreadCount()))
            worker = Worker()
            worker.set_node(node)
            worker.preparedItem.connect(self.emit_new_item)
            self.thread_pool.start(worker, priority=100)

class NodeItem(QtCore.QObject):
    """Item to hold a node and it's corresponding clip.
    Make it behave like the node in comparisons so list handling is the same"""
    def __init__(self, node, clip):
        QtCore.QObject.__init__(self)
        self.node = node
        self.clip = clip

    def __eq__(self, other):
        """Enable matching self with a Node instance"""
        return other == self.node
    
    def __repr__(self):
        return 'NodeItem(node={}, clip={})'.format(self.node.name(), self.clip)
        

