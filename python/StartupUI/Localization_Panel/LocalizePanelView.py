import os
import nuke
from LocalizePanelModel import Roles, Status, HEADERS_LABELS, header_list
from LocalizationHelpers import IN_NUKE, IconPaths, SettingsKeys, logger
from PySide2 import QtWidgets, QtCore, QtGui


# When Nuke launches and executes panel code in the startup workspace,
# the hiero package is not yet available, so delay the import a little.
if IN_NUKE:
    QtCore.QTimer.singleShot(1000, lambda: __import__('hiero'))
else:
    import hiero

def RgbaToQColor(c):
    return QtGui.QColor( ((c & 0xff) << 24) | (c >> 8) )

class Constants:
    COL_BG               = QtGui.QColor(75, 75, 75)
    COL_NOT_LOCALIZED    = QtGui.QColor(179, 179, 179)
    COL_DISABLED         = QtGui.QColor(80, 227, 194)
    TEXT_UP_TO_DATE          = 'Up to date'
    TEXT_OUT_OF_DATE         = 'Out of date'
    TEXT_READING_FROM_SOURCE = 'Reading from source'
    TEXT_NOT_LOCALIZED       = 'Not localized'
    TEXT_DISABLED            = 'Disabled'
    STATUS_BAR_PADDING = 35
    THUMB_SIZE = QtCore.QSize(84, 54)

class ContextMenu(QtWidgets.QMenu):
    """Menu to show when right clicking on a row"""
    def __init__(self, selection, parent=None):
        super(ContextMenu, self).__init__(parent)

        if IN_NUKE:
            self.selected_items = [i.data(Roles.ItemRole) for i in selection]
        else:
            # grabbing custom object from index doesn't work with Hiero's Clip items (PySide bug)
            source_model = selection[0].model()
            self.selected_items = [source_model.data(i, Roles.ItemRole).readNode() for i in selection]

        logger.debug('creating actions for: %s', [n.name() for n in self.selected_items])
        self.__createActions()
        # if the menu only opened on one item check the action according to the node's current policy
        if len(self.selected_items) == 1:
            item = self.selected_items[0]
            self.actions()[int(item['localizationPolicy'].getValue())].setChecked(True)

    def __createActions(self):
        self.addAction(QtWidgets.QAction('on',                      self, checkable=True, triggered=lambda: [n['localizationPolicy'].setValue(0) for n in self.selected_items]))
        self.addAction(QtWidgets.QAction('from auto-localize path', self, checkable=True, triggered=lambda: [n['localizationPolicy'].setValue(1) for n in self.selected_items]))
        self.addAction(QtWidgets.QAction('on demand',               self, checkable=True, triggered=lambda: [n['localizationPolicy'].setValue(2) for n in self.selected_items]))
        self.addAction(QtWidgets.QAction('off',                     self, checkable=True, triggered=lambda: [n['localizationPolicy'].setValue(3) for n in self.selected_items]))

class LocalizeItemDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate to draw node name and progress bar.
    Unfortunately 'setItemDelegateForColumn' crashes Nuke so we have to deal with all columns in here.
    See bug TP 355573
    """
    def __init__(self, view, parent=None):
        super(LocalizeItemDelegate, self).__init__(parent)
        self.view = view

    def __openInFileBrowser(self, node):
        print node
        raise NotImplementedError

    def __deleteLocalFiles(self, node):
        print node
        raise NotImplementedError

    def __generateStripe(self, baseColor, size):
        """Paint code for stripes"""
        image = QtGui.QImage(size, QtGui.QImage.Format_ARGB32)
        image.fill(baseColor)
        rect = QtCore.QRect(0, 0, size.width(), size.height())
        lockedBrush = QtGui.QLinearGradient()
        lockedBrush.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
        lockedBrush.setColorAt(0.499, QtGui.QColor(0, 0, 0, 0))
        lockedBrush.setColorAt(0.5, QtGui.QColor(32, 32, 32, 100))
        lockedBrush.setColorAt(1.0, QtGui.QColor(32, 32, 32, 100))
        lockedBrush.setStart(0, 12)
        lockedBrush.setFinalStop(-12, 0)
        lockedBrush.setSpread(QtGui.QGradient.RepeatSpread)
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setClipping(False)
        painter.fillRect(rect, lockedBrush)
        return image

    def __generateBullsEye(self, radius):
        image = QtGui.QImage(QtCore.QSize(radius*3, radius*3), QtGui.QImage.Format_ARGB32)
        image.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = painter.pen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QtGui.QColor(244, 198, 91))
        painter.drawEllipse(image.rect().center(), radius, radius)
        painter.setBrush(QtGui.QColor(0, 0, 0))
        painter.setPen(QtCore.Qt.transparent)
        painter.drawEllipse(image.rect().center(), radius*.5, radius*.5)
        return image
        
    def __paint_thumb(self, painter, option, index):
        """Paint the thumbnail column"""
        thumb = index.data(Roles.ThumbnailRole)
        scaled_thumb = index.data(Roles.ThumbnailRole).scaled(Constants.THUMB_SIZE.width(),
                                                              Constants.THUMB_SIZE.height(),
                                                              QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        thumb_rect = QtCore.QRect(0, 0, scaled_thumb.rect().width(), scaled_thumb.rect().height())
        thumb_rect.moveCenter(option.rect.center())
        painter.drawPixmap(thumb_rect, scaled_thumb)

        # paint bullseye for rows under cursor
        if index.row() == self.view.row_under_cursor:
            # dim the thumbnail
            #painter.fillRect(option.rect, QtGui.QColor(100,100,100,100))
            # draw bullseye
            bullseye = self.__generateBullsEye(8)
            painter.drawImage(option.rect.topLeft(), bullseye)
            self.view.bullseye_area = bullseye.rect() # set the active area for a click

    def __paint_status(self, painter, option, index):
        """Paint the status bar column"""
        progress = index.data(Roles.ProgressRole)
        progress_rect = option.rect.adjusted(Constants.STATUS_BAR_PADDING, 0, -Constants.STATUS_BAR_PADDING, 0)
        progress_rect.setHeight(7)
        progress_rect.moveTop(option.rect.top() + option.rect.height() * .7)
        
        #logger.debug('current status role is: %s', ['IN_PROGRESS', 'OUT_OF_DATE', 'READ_FROM_SOURCE', 'UP_TO_DATE', 'DISABLED'][index.data(Roles.StatusRole)])

        # set colours, patterns and rect width based on status   
        if index.data(Roles.StatusRole) == Status.DISABLED:
            brush = QtGui.QBrush(Constants.COL_DISABLED)
            text = Constants.TEXT_DISABLED
        if index.data(Roles.StatusRole) == Status.OUT_OF_DATE:
            brush = QtGui.QBrush(self.view.COL_OUT_OF_DATE)
            text = Constants.TEXT_OUT_OF_DATE
        elif index.data(Roles.StatusRole) == Status.READ_FROM_SOURCE:
            brush = QtGui.QBrush(self.__generateStripe(self.view.COL_OUT_OF_DATE, option.rect.size()))
            text = Constants.TEXT_READING_FROM_SOURCE
            #progress = 1.0 # draw full bar regardless of node progress
        elif progress == 0:
            brush = QtGui.QBrush(Constants.COL_NOT_LOCALIZED)
            text = Constants.TEXT_NOT_LOCALIZED
            progress = 1.0 # draw full bar regardless of node progress. I'd actually prefer not doing this
        elif progress < 1:
            brush = QtGui.QBrush(self.view.COL_IN_PROGRESS)
            text = '{0:.2f}%'.format(progress * 100.0)
        elif index.data(Roles.StatusRole) == Status.UP_TO_DATE:
            brush = QtGui.QBrush(self.view.COL_UP_TO_DATE)
            text = Constants.TEXT_UP_TO_DATE

        ## paint progress bar BG
        painter.save()
        painter.setPen(QtCore.Qt.transparent)
        painter.setBrush(Constants.COL_BG)
        painter.drawRoundedRect(progress_rect, progress_rect.height()*.5, progress_rect.height()*.4)    
        painter.restore()

        ## draw text
        painter.drawText(option.rect, QtCore.Qt.AlignCenter, text)

        ## paint progress bar colour
        painter.setPen(QtCore.Qt.transparent)
        painter.setBrush(brush)
        progress_rect.setWidth(progress_rect.width() * progress)
        painter.drawRoundedRect(progress_rect, progress_rect.height()*.5, progress_rect.height()*.4)

    def paint(self, painter, option, index):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.save()
        header_label = index.model().headerData(index.row(), QtCore.Qt.Horizontal)

        # make text black when rows are selected
        if index in self.view.selectedIndexes():
            painter.setPen(QtCore.Qt.black)
        
        # paint thumbnail        
        if index.column() == header_list.index(HEADERS_LABELS.THUMBNAIL):
            self.__paint_thumb(painter, option, index)

        # paint file name
        elif index.column() == header_list.index(HEADERS_LABELS.FILE_NAME):
            fm = QtGui.QFontMetrics(painter.font())
            painter.drawText(option.rect,
                             QtCore.Qt.AlignCenter,
                             fm.elidedText(index.data(Roles.FileNameRole),
                                           QtCore.Qt.TextElideMode.ElideMiddle,
                                           option.rect.width()))

        # paint version
        elif index.column() == header_list.index(HEADERS_LABELS.VERSION):
            painter.drawText(option.rect,
                             QtCore.Qt.AlignCenter,
                             index.data(Roles.VersionRole))

        # paint node name in Nuke / shot name in Hiero
        elif index.column() == header_list.index(HEADERS_LABELS.ITEM_NAME):
            fm = QtGui.QFontMetrics(painter.font())
            painter.drawText(option.rect,
                             QtCore.Qt.AlignCenter,
                             fm.elidedText(index.data(Roles.ItemNameRole),
                                           QtCore.Qt.TextElideMode.ElideRight,
                                           option.rect.width()))            
        # paint status / progressbar
        elif index.column() == header_list.index(HEADERS_LABELS.STATUS):
            self.__paint_status(painter, option, index)

        # mute row if item's localization is paused
        if nuke.localization.isLocalizationPaused() and index.data(Roles.StatusRole) != Status.UP_TO_DATE:
            painter.fillRect(option.rect, QtGui.QColor(255, 255, 255, 35))

        painter.restore()

    def sizeHint(self, option, index):
        if index.column() == 5:
            return QtCore.QSize(10,100)

class LocalizeView(QtWidgets.QTableView):
    """Table view to visualize the current localozation status of nodes"""
    SECTION_HEIGHT = 70

    def __init__(self, parent=None):
        #super(LocalizeView, self).__init__(parent)   # why does Hiero not like super() calls??????
        QtWidgets.QTableView.__init__(self, parent)
        #SS_no_selection_border = '''QTableView::item {outline: none}'''
        #self.setStyleSheet(SS_no_selection_border)
        self.setStyleSheet('''QTableView {border: 1px solid black;}''')
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.setAlternatingRowColors(True)
        self.setGridStyle(QtCore.Qt.PenStyle.NoPen)
        self.setSortingEnabled(True)
        self.setShowGrid(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.show_header_menu)
        self.verticalHeader().setDefaultSectionSize(self.SECTION_HEIGHT)
        self.verticalHeader().hide()
        ################ setItemDelegateForColumn crashes Nuke - see bug TP 355573
        #self.setItemDelegateForColumn(0 ,LocalizeItemDelegate(self)) #
        ################################################################################
        self.setItemDelegate(LocalizeItemDelegate(self))
        self.setMouseTracking(True)
        self.row_under_cursor = None
        self.bullseye_area = None #
        self.update_colours_from_prefs()
            
    def __find_node(self, node):
        """Select and zoom to fit the node. Open containing group if necessary"""
        logger.debug('trying to find %s', node)
        with nuke.root() as group:
            #group = nuke.root()
            name_parts = node.fullName().split('.')
            if len(name_parts) > 1:
                group = nuke.toNode('.'.join(name_parts[:-1]))
            node.selectOnly()
            with group:
                nuke.showDag(group)
                nuke.zoomToFitSelected(node)    

    def setModel(self, model):
        #super(LocalizeView, self).setModel(model) # why does Hiero not like super() calls??????
        QtWidgets.QTableView.setModel(self, model)
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        # keep reference to source model for convenience
        self.source_model = model.sourceModel()

    def show_header_menu(self, pos):
        global_pos = self.mapToGlobal(pos)
        menu = QtWidgets.QMenu(self)
        for i in xrange(self.horizontalHeader().count()):
            label = self.source_model.headerData(i, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole)
            act = QtWidgets.QAction(label, menu, checkable=True, triggered=lambda x=i: self.toggle_column(x))
            act.setChecked(not self.horizontalHeader().isSectionHidden(i))
            menu.addAction(act)
        menu.popup(global_pos)

    def toggle_column(self, index):
        """Toggles the visibility of the column with the given index"""
        header = self.horizontalHeader()
        header.setSectionHidden(index, not header.isSectionHidden(index))

        # save settings to ~/.nuke/uistate.ini
        column_data = [i for i in xrange(header.count()) if not header.isSectionHidden(i)]
        self.parent().settings.setValue(SettingsKeys.columns, column_data)

    def update_colours_from_prefs(self):
        """Read the preferences for the correct colours.
        This is a slot that is called via callbacks on the respective preference knobs."""
        logger.debug('new colours')
        self.COL_UP_TO_DATE  = RgbaToQColor(nuke.toNode('preferences')['localizationCompletedColor'].value())
        self.COL_IN_PROGRESS = RgbaToQColor(nuke.toNode('preferences')['localizationProgressColor'].value())
        self.COL_OUT_OF_DATE = RgbaToQColor(nuke.toNode('preferences')['localizationOutdatedColor'].value())        
        self.viewport().update()

    def leaveEvent(self, event):
        """Clear hover effect on rows"""
        #super(LocalizeView, self).leaveEvent(event) # why does Hiero not like super() calls??????
        QtWidgets.QTableView.leaveEvent(self, event)
        self.row_under_cursor = None
        
    def contextMenuEvent(self, event):
        """Pop up context menu to allow setting localisation modes on all selected rows"""
        #selection = self.selectionModel().selectedRows(column=0) or [self.indexAt(event.pos())]
        selection = self.selectionModel().selectedRows(column=0)
        selection_mapped = [self.model().mapToSource(i) for i in selection]
        try:
            menu = ContextMenu(selection_mapped, self)
            menu.popup(QtGui.QCursor.pos())
            event.accept()
        except AttributeError:
            # rightl click happened in empty space
            pass

    def mouseReleaseEvent(self, event):
        #super(LocalizeView, self).mouseReleaseEvent(event) # why does Hiero not like super() calls??????
        QtWidgets.QTableView.mouseReleaseEvent(self, event)
        if event.button() == QtCore.Qt.LeftButton:
            # open item
            clicked_index = self.indexAt(event.pos())
            if self.rowAt(event.pos().y()) == -1 or\
               clicked_index.column() != header_list.index(HEADERS_LABELS.THUMBNAIL):
                # click happened under last row, so ignore it
                event.ignore()
                return
            #item = clicked_index.data(Roles.ItemRole) # known PySide bug where custom objects in index.data() are lost. workaround:
            self.bullseye_area.moveTop(self.rowViewportPosition(self.rowAt(event.pos().y())))
            if self.bullseye_area.contains(event.pos()):
                # if the click is in the bullseye area do react to it
                #item = self.source_model.data(clicked_index, Roles.ItemRole)
                item = self.source_model.data(self.model().mapToSource(clicked_index), Roles.ItemRole)
                logger.debug('clicked index: %s', clicked_index)
                logger.debug('clicked item: %s', type(item))
                if IN_NUKE:
                    nuke.show(item)
                    self.__find_node(item)
                else:
                    hiero.ui.openInNewViewer(item.binItem())

    def mouseMoveEvent(self, event):
        """Highlight rows under cursor to indicate they can be clicked
        by overlaying a bullseye image onto the thumbnail"""
        #super(LocalizeView, self).mouseMoveEvent(event) # why does Hiero not like super() calls??????
        QtWidgets.QTableView.mouseMoveEvent(self, event)
        self.row_under_cursor = self.rowAt(event.pos().y())
        self.source_model.dataChanged.emit(self.source_model.index(self.row_under_cursor, header_list.index(HEADERS_LABELS.THUMBNAIL)),
                                           self.source_model.index(self.row_under_cursor, header_list.index(HEADERS_LABELS.THUMBNAIL)))