import os
from PySide2.QtWidgets import QTreeView
from PySide2.QtCore import Qt, QItemSelectionModel, QSignalBlocker
from PySide2.QtGui import QStandardItem, QStandardItemModel, QIcon, QPixmap
import subprocess
import pydenticon
import ctypes


ctypes_wrapper = ctypes.cdll.LoadLibrary(os.path.dirname(__file__)+'/ctypes_friendly_wrapper.so')
ctypes_wrapper.nix_build_hash_base32_to_base16_c_str.restype = ctypes.c_char_p


class FakeDigest:
    """
    Return hash passed to constructor, imitating parts of hashlib digest which are used by pydenticon
    """
    def __init__(self, val):
        self.val = val
    def hexdigest(self):
        # pydenticon checks if >23 bits are produced for 'test' input
        if len(self.val)<6:
            return (self.val + b''.join([b'0' for i in range(6)]))[:6]
        else:
            return self.val


pydenticon_generator = pydenticon.Generator(5, 5, digest=FakeDigest)


class StoreTreeView(QTreeView):

    def __init__(self, *args, **kwargs):
        self.status_bar = kwargs.pop('status_bar')
        super(StoreTreeView, self).__init__(*args, **kwargs)
        model = QStandardItemModel()
        self.setModel(model)
        self.setHeaderHidden(True)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.setMouseTracking(True)
        self.expanded.connect(self.expanded__handler)
        self.entered.connect(lambda index: self.status_bar.showMessage(self.model().itemFromIndex(index).data()))
        self.selectionModel().currentChanged.connect(self.selection_model__current_changed__handler, Qt.QueuedConnection)
        self.selectionModel().selectionChanged.connect(self.selection_model__selection_changed__handler)
        #self.selection_changed__blocked = False

    # On item expand its store path is queried for dependencies
    def expanded__handler(self, index):
        store_view = self
        store_model = self.model()
        parent_item = store_model.itemFromIndex(index)
        if parent_item.rowCount() and not parent_item.child(0).data():
            parent_item.removeRow(0)
        else:
            return
        #for child_path in iter_store_path_deps(parent_item.data()):
        child_paths = [child_path for child_path in iter_store_path_deps(parent_item.data())]
        child_paths.sort(key=lambda v: v[len('/nix/store/681354n3k44r8z90m35hm8945vsp95h1-'):])
        selected_indexes = store_view.selectionModel().selectedIndexes()
        if selected_indexes:
            current_store_path_item = store_model.itemFromIndex(store_view.selectionModel().selectedIndexes()[-1])
            current_store_path = current_store_path_item.data()
        else:
            current_store_path = None
        for child_path in child_paths:
            print(child_path)
            child_item = self.add_store_path(child_path, parent_item)
            # If same store path as current selection, add to selection
            if child_path == current_store_path:
                store_view.selectionModel().select(child_item.index(), QItemSelectionModel.Select)

    # Every path should have dummy child element to be expandable
    def add_store_path(self, path, parent=None):
        if parent is None:
            parent=self.model().invisibleRootItem()
        store_icon_pixmap = QPixmap()
        #hash = get_command_output('nix-hash --type sha1 --to-base16 '+path[11:11+32]).strip()
        hash = ctypes_wrapper.nix_build_hash_base32_to_base16_c_str(bytes(path[11:11+32], 'ascii'))[5:]
        store_icon_pixmap.loadFromData(pydenticon_generator.generate(hash.decode(), 20, 20))
        #print(image)
        store_path_icon = QIcon(store_icon_pixmap)
        item = QStandardItem(store_path_icon, path[len('/nix/store/681354n3k44r8z90m35hm8945vsp95h1-'):])
        #item.setIcon(colorify_icon(item.icon(), None))
        item.setData(path)
        parent.appendRow(item)
        dummy_item = QStandardItem('')
        item.appendRow(dummy_item)
        return item

    #def store_view__selection_model__selection_changed(current, previous):
    def selection_model__current_changed__handler(self, current, previous):
        store_view = self
        store_model = self.model()
        # If same store path but other item, do nothing
        # Need to distinct items which are selected programmaticaly and ignore
        print()
        print('Current changed')
        print('current', current)
        print('previous', previous)
        print('selected', store_view.selectionModel().selectedIndexes())
        print('Blocking signals')
        # Somewhy Qt signal blocking doesn't work
        #prev_state = store_view.blockSignals(True)
        #blocker = QSignalBlocker(store_view)
        self.selection_changed__blocked = True
        if store_model.itemFromIndex(previous) and store_model.itemFromIndex(current).data() != store_model.itemFromIndex(previous).data():
            print('New path, clearing selection')
            # TODO: somewhy this doesn't work if mouse button is not released
            store_view.selectionModel().clearSelection()
            #return
        store_path = store_model.itemFromIndex(current).data()
        current_item = store_model.itemFromIndex(current)
        self.derivation_view.update(store_path)
        self.contents_view.update(store_path)
        # Select other store items with same store path
        print('Looking for other items with same store path')
        #next_visible_item_index = store_view.indexAt(store_view.rect().topLeft())
        next_visible_item_index = store_model.index(0, 0)
        #last_visible_item_index = store_view.indexAt(store_view.rect().bottomLeft())
        #last_visible_item = store_model.itemFromIndex(last_visible_item_index)
        while next_visible_item_index:
            next_visible_item = store_model.itemFromIndex(next_visible_item_index)
            if next_visible_item is None: #last_visible_item:
                break
            #print('Selected indexes',  store_view.selectionModel().selectedIndexes())
            if next_visible_item.data() == store_path: #and next_visible_item.index() not in store_view.selectionModel().selectedIndexes():
                print('Selecting item with same store path')
                print('index', next_visible_item_index)
                print('path', next_visible_item.data())
                store_view.selectionModel().select(next_visible_item_index, QItemSelectionModel.Select)
                #break
            next_visible_item_index = store_view.indexBelow(next_visible_item_index)
        print('Unblocking signals')
        self.selection_changed__blocked = False
    #store_view.selectionModel().selectionChanged.connect(store_view__selection_model__selection_changed)
    #store_view.selectionModel().currentChanged.connect(store_view__selection_model__current_changed, Qt.QueuedConnection)

    def selection_model__selection_changed__handler(self, selected, deselected):
        # Selection should only happen automatically via currentChanged handler
        # it blocks selection signal, so triggered signal is unwanted
        if self.selection_changed__blocked:
            return
        print('Selection changed')
        print('selected indexes', selected.indexes())
        print('deselected indexes', deselected.indexes())
        for index in deselected.indexes():
            self.selectionModel().select(index, QItemSelectionModel.Select)
    #store_view.selectionModel().selectionChanged.connect(store_view__selection_model__selection_changed)


def iter_store_path_deps(path):
    command = 'nix-store --query --references ' + path
    process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE)
    (output, _) = process.communicate()
    _ = process.wait()
    for dep_path in output.decode().split('\n'):
        if dep_path and dep_path != path:
            yield dep_path

def get_command_output(command):
    process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE)
    (output, _) = process.communicate()
    _ = process.wait()
    return output

def iter_command_output_lines(command):
    for line in get_command_output(command).decode().split('\n'):
        if not line:
            break
        yield dep_path

store_view__selection_changed__blocked = False


