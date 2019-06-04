import os
import nuke
import nukescripts
import re
from LocalizationHelpers import IN_NUKE, IconPaths, get_all_clips, logger
from PySide2 import QtCore, QtGui

# When Nuke launches and executes panel code in the startup workspace,
# the hiero package is not yet available, so delay the import a little.
if IN_NUKE:
    QtCore.QTimer.singleShot(1000, lambda: __import__('hiero'))
else:
    import hiero

def get_clip_version(path):
    """Get the version info ala Nuke.
    I assume this should be using Hiero's VertionScanner?!
    """
    try:
        version_info = nukescripts.version_get(path, 'v')
        return ''.join(version_info)
    except ValueError:
        return 'N/A'

def findNodes(path):
    """NOTE:
       nuke.localization.findNodes(path) does not work in Hiero 11.2v3 so this is a workaround.
       Trying to use as much of Hiero's code as possible.
       Ideally nuke.localization.findNodes fill be made to work in Hiero so this function
       can be removed.
       """
    if IN_NUKE:
        return nuke.localization.findNodes(path)
    else:
        file_head = os.path.splitext(hiero.core.VersionScanner.VersionScanner().getFileHead(os.path.basename(path)))[0].rstrip('.')
        return [clip.readNode() for clip in get_all_clips() if hiero.core.FnExporterBase.mediaSourceExportFileHead(clip.mediaSource()) == file_head]

class HEADERS_LABELS:
    THUMBNAIL = 'Thumbnail'
    FILE_NAME = 'File name'
    VERSION   = 'Version'
    ITEM_NAME = 'Read name' if IN_NUKE else 'Clip name'
    STATUS    = 'Status'

class Roles:
    """Custom roles"""
    ThumbnailRole, FileNameRole, VersionRole, ItemNameRole,\
    StatusRole, ProgressRole, ShowRole, ItemRole, NoMedia = xrange(QtCore.Qt.UserRole+1, QtCore.Qt.UserRole+10)

class Status:
    """Possible node statuses"""
    IN_PROGRESS, OUT_OF_DATE, READ_FROM_SOURCE, UP_TO_DATE, DISABLED, NOT_LOCALIZED = xrange(6)

class LocalizeProxyModel(QtCore.QSortFilterProxyModel):
    '''Proxy model for filtering'''
    def __init__(self, parent=None):
        #super(LocalizeProxyModel, self).__init__(parent) # why does Hiero not like super() calls??????
        QtCore.QSortFilterProxyModel.__init__(self, parent)
        self.setDynamicSortFilter(True)
        self.filter_list = []

    def set_current_filter(self, filter_list):
        self.filter_list = filter_list
        self.invalidate()

    def filterAcceptsRow(self, source_row, source_parent):
        """Filter by status, hide offline clips and nodes in error"""
        return self.sourceModel().index(source_row, 0).data(Roles.StatusRole) in self.filter_list\
               and not self.sourceModel().index(source_row, 0).data(Roles.NoMedia)

    def lessThan(self, source_left, source_right):
        """Custom sorting"""
        col = QtCore.QCollator()
        col.setCaseSensitivity(QtCore.Qt.CaseSensitive.CaseInsensitive)
        col.setNumericMode(True)
        
        if header_list[source_left.column()] == HEADERS_LABELS.STATUS:
            return source_left.data(Roles.ProgressRole) < source_right.data(Roles.ProgressRole) or\
                   source_left.data(Roles.StatusRole) < source_right.data(Roles.StatusRole)
        
        elif header_list[source_left.column()] == HEADERS_LABELS.FILE_NAME:
            return col.compare(source_left.data(Roles.FileNameRole), source_right.data(Roles.FileNameRole)) < 0
        
        elif header_list[source_left.column()] == HEADERS_LABELS.VERSION:
            return col.compare(source_left.data(Roles.VersionRole), source_right.data(Roles.VersionRole)) < 0        
    
        elif header_list[source_left.column()] == HEADERS_LABELS.ITEM_NAME:
            return col.compare(source_left.data(Roles.ItemNameRole), source_right.data(Roles.ItemNameRole)) < 0

    def setSourceModel(self, model):
        model.dataChanged.connect(self.invalidate)
        model.proxyModel = self
        #super(LocalizeProxyModel, self).setSourceModel(model)   # why does Hiero not like super() calls??????
        QtCore.QSortFilterProxyModel.setSourceModel(self, model)
        
class LocalizeModelBase(QtCore.QAbstractTableModel):
    """Base model to deal with the required data to visualize the localization state.
    This is inherited by the main model to then deal with any data differences.
    """
    localizing_index = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        #super(LocalizeModelBase, self).__init__(parent) # why does Hiero not like super() calls??????
        QtCore.QAbstractTableModel.__init__(self, parent)
        ###############################################################################################################################
        # For the model data hold a list of items with "node" and "clip" attribute (in Hiero)
        # In Nuke the "clip" attribute will always be None
        # Getting a node's clip in Hiero involves looping over all available clips so I only want to do that once when the node is
        # added rather than in the data() method
        self.item_list = []
        ###############################################################################################################################
        self.proxyModel = None
        self.deleted_item = None # keep track of the last deleted item to prevent Nuke's localization event from ading it again

    def file_cb_updates_row(self, path, event_id):
        """Added as callback via nuke.localization.addFileCallback to drive status bars and update the file labels."""
        for node in findNodes(path):
            # for each node who's file is currently being localized update the status bar in the view
            logger.debug('updating: %s', node.name())
            i = self.item_list.index(node)        
            self.localizing_index.emit(self.proxyModel.mapFromSource(self.index(i, 0)))
            self.dataChanged.emit(i, i)

    def knob_cb_updates_row(self, node):
        """Added as callback via nuke.knobChanged to drive status bars and update the file labels.
        We need this extra case to react to verison changes between versions that don't trigger the nuke.localization.addFileCallback"""
        logger.debug('updating: %s', node.name())
        try:
            i = self.item_list.index(node)        
            self.localizing_index.emit(self.proxyModel.mapFromSource(self.index(i, 0)))
            self.dataChanged.emit(i, i)
        except ValueError:
            # node has not yet been registered and added to the list - probbaly still waiting for it's clip to be created
            pass

    def update_node_status(self, node, event_id):
        """Added as callback via nuke.localization.addReadCallback to update any change in node status"""
        success = False
        if node is self.deleted_item:
            logger.debug("ReadStatus event came from a deleted node, ignoring...")
            return
        try:
            i = self.item_list.index(node)
            self.dataChanged.emit(i, i)
        except ValueError:
            # node has not yet been added - probbaly still looking for it's clip...
            pass

    def add_item(self, item, exclude=['.nk']):
        """Added as callback via nuke.addOnCreate. Exclude nk files for Hiero/NS"""
        if item.clip and os.path.splitext(item.clip.mediaSource().fileinfos()[0].filename())[-1] in exclude:
            # ignore excluded file extensions
            return
        logger.debug('about to add %s', item.node.name())
        if item in self.item_list:
            logger.debug('node already exists - skipping.')
            # this should not be required but Hiero seems to trigger onCreate callbacks twice for each created item
            # so we need to explicitly avoid double ups in the model
            return
        logger.debug('\t'+'+' * 20)
        logger.debug('\t   ++++++++++++ adding %s  ++++++++++++', item.node.name())
        self.item_list.append(item)
        new_index = self.index(self.item_list.index(item), 0)
        self.dataChanged.emit(new_index, new_index)
        logger.debug('current list has (%s) items:', len(self.item_list))
        logger.debug(self.item_list)
        logger.debug('\t'+'+' * 20)

    def remove_node(self):
        """Used for nuke.onDestroy callback"""
        node = nuke.thisNode()
        # keep track of the node that was just deleted so we can identify it and 
        # ignore it's final localization.ReadStatus.LOCALIZATION_DISABLED signal
        # in self.update_node_status (which woudl lead to a dead lock)
        self.deleted_node = node
        try:
            row = self.item_list.index(node)
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            self.item_list.remove(node)
            self.deleted_item = node
            self.endRemoveRows()
            logger.debug('\t\t' + '-'*20)
            logger.debug('\t\tremoved %s', node.name())
            logger.debug('\t\t' + '-'*20)
        except ValueError:
            # node is not a localizable node and thus not part of the model
            pass

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return header_list[section]

    def columnCount(self, index=None):
        return len(header_list)

    def rowCount(self, index=None):
        return len(self.item_list)

class LocalizeModel(LocalizeModelBase):
    """This model only deals with the data differences between Nuke and Hiero."""
    GENERIC_DATA_ROLES = (QtCore.Qt.ToolTipRole,
                          Roles.ProgressRole,
                          Roles.VersionRole,
                          Roles.StatusRole)
    
    #def __init__(self, parent=None):
        ##super(LocalizeModel, self).__init__(parent) # why does Hiero not like super() calls??????
        #LocalizeModelBase

    def data(self, index, role):
        """Set the data method to use (Nuke or Hiero)."""
        # if the item list is empty there is nothing to do
        if not self.item_list:
            return
        
        node = self.item_list[index.row()].node
        logger.debug('-' * 20)
        logger.debug('\t>> Retrieving data for %s', node.name())
        if role in self.GENERIC_DATA_ROLES:
            # generic roles which work for both Nuke and Hiero
            if role == QtCore.Qt.ToolTipRole:
                if index.column() == header_list.index(HEADERS_LABELS.THUMBNAIL):
                    return 'Click to show {}'.format(self.data(index, Roles.ItemNameRole))
                elif index.column() == header_list.index(HEADERS_LABELS.STATUS):
                    return 'Localization policy for {}: {}'.format(self.data(index, Roles.ItemNameRole),
                                                                   node['localizationPolicy'].value())
            elif role == Roles.VersionRole:
                return get_clip_version(self.data(index, Roles.FileNameRole))
            
            elif role == Roles.ProgressRole:
                return node.localizationProgress()
            
            elif role == Roles.StatusRole:
                if node['localizationPolicy'].value() == 'off':
                    #print index.data(Roles.ItemNameRole) + ' is paused'
                    return Status.DISABLED
                elif node.localizationProgress() == 0:
                    return Status.NOT_LOCALIZED
                elif node.isLocalizationOutdated():
                    #print index.data(Roles.ItemNameRole) + ' is out of date'
                    if nuke.toNode('preferences')['LocalizationUseSourceWhenOutOfDate'].value():
                        return Status.READ_FROM_SOURCE
                    else:
                        return Status.OUT_OF_DATE
                elif node.localizationProgress() == 1.0:
                    return Status.UP_TO_DATE
                else:
                    #print index.data(Roles.ItemNameRole) + ' is up to date'
                    return Status.IN_PROGRESS

        # otherwise use application specific data handling
        elif IN_NUKE:
            logger.debug('using Nuke specific data for %s', node.name())
            return self.nuke_data(index, role)
        else:
            if nuke.toNode(node.name()):
                logger.debug('using Nuke specific data for %s', node.name())
                return self.nuke_data(index, role)
            logger.debug('using Hiero data for %s', node.name())
            return self.hiero_data(index, role)

    def hiero_data(self, index, role):
        '''Return required data for Hiero clips'''
        item = self.item_list[index.row()]
        node = item.node
        clip = item.clip
        logger.debug('\tnode:%s', node.name())
        logger.debug('\tclip:%s', clip)
        #try:
            #clip = item.clip
        #except AttributeError:
            ## happens because the clip item does not yet have a readNode() when the node is created
            ## therefore NodeItem.__get_clip_from_node has to be delayed which causes this error for a split second
            #return None

        if role == Roles.NoMedia:
            return clip.mediaSource().isOffline() or clip.mediaSource().isNull()

        if role == Roles.ThumbnailRole:
            # return the clip's thumbnail
            # audio clips don't support thumbnails yet so use a generic icon for now
            if clip.hasError() or clip.mediaSource().isOffline() or clip.mediaSource().isNull():
                return QtGui.QPixmap(IconPaths.THUMB_ERROR)
            elif os.path.splitext(clip.mediaSource().fileinfos()[0].filename())[1] == '.nk':
                return QtGui.QPixmap(IconPaths.THUMB_NUKE)
            elif not clip.mediaSource().hasVideo():
                # Use a generic audio icon until clip.thumbnail() is fixed for audio clips
                return QtGui.QPixmap(IconPaths.THUMB_AUDIO)
            else:
                try:
                    return QtGui.QPixmap(clip.thumbnail())
                except RuntimeError:
                    # sometimes the thumbnail doesn't seem to be available for a split second
                    pass

        elif role == Roles.FileNameRole:
            return os.path.basename(clip.mediaSource().fileinfos()[0].filename())

        elif role == Roles.ItemNameRole:
            return clip.binItem().name()

        elif role == Roles.ItemRole:
            return clip

    def nuke_data(self, index, role):
        '''Return required data for Nuke nodes'''
        node = self.item_list[index.row()].node

        if role == Roles.NoMedia:
            # calling hasError() causes expressions links to show up for all Read nodes - what is happening????
            #return node.hasError()
            return False
        
        if role == Roles.ThumbnailRole:
            # Return an icon based on node class
            if not nuke.filename(node) or node.hasError():
                return QtGui.QPixmap(IconPaths.THUMB_ERROR)
            if node.Class().startswith('ReadGeo'):
                return QtGui.QPixmap(IconPaths.THUMB_3D)
            elif node.Class().startswith('Read'):
                if os.path.isfile(nuke.filename(node)):
                    return QtGui.QPixmap(IconPaths.THUMB_IMAGE)
                else:
                    return QtGui.QPixmap(IconPaths.THUMB_VIDEO)
            else:
                return QtGui.QPixmap(IconPaths.THUMB_MISC)

        elif role == Roles.FileNameRole:
            try:
                return os.path.basename(nuke.filename(node))
            except:
                # node has no filename
                return
        
        elif role == Roles.ItemNameRole:
            return node.fullName().replace('.', '/')

        elif role == Roles.ItemRole:
            return node

# Define the order in which the columns are shown
header_list = [HEADERS_LABELS.THUMBNAIL,
               HEADERS_LABELS.FILE_NAME, 
               HEADERS_LABELS.VERSION,
               HEADERS_LABELS.ITEM_NAME,
               HEADERS_LABELS.STATUS]