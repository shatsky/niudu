import os
import sys
from PySide2.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMenuBar, QMenu, QTreeView,\
QTabWidget, QFileSystemModel, QVBoxLayout, QComboBox, QLabel, QStatusBar
from PySide2.QtCore import Qt, QItemSelectionModel, QSignalBlocker
from PySide2.QtGui import QStandardItem, QStandardItemModel, QBrush, QIcon, QPainter, QPixmap
import subprocess
import json
#import .store
#import .derivation
#import .contents
import pydenticon
import PIL.ImageQt
import ctypes


ctypes_wrapper = ctypes.cdll.LoadLibrary('./ctypes_friendly_wrapper.so')
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

app = QApplication(sys.argv)
app.setWindowIcon(QIcon.fromTheme('nix-snowflake'))
app.setApplicationName('Nix Explorer')
status_bar = QStatusBar()

def colorify_icon(icon, hash):
    pixmap = icon.pixmap(20)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.setBrush(Qt.red)
    painter.setPen(Qt.red)
    painter.drawRect(pixmap.rect())
    painter.end()
    return QIcon(pixmap)

#
# STORE TREE
#

store_model = QStandardItemModel()
store_view = QTreeView()
store_view.setModel(store_model)
store_view.setHeaderHidden(True)
store_view.setSelectionMode(QTreeView.ExtendedSelection)
store_view.setMouseTracking(True)
store_path_icon = QIcon('puzzle-piece-solid.svg')
store_icon_pixmap = QPixmap()

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

# Every path should have dummy child element to be expandable
def add_store_path(path, parent=store_model.invisibleRootItem()):
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

# On item expand its store path is queried for dependencies
def store_view__expanded(index):
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
        child_item = add_store_path(child_path, parent_item)
        # If same store path as current selection, add to selection
        if child_path == current_store_path:
            store_view.selectionModel().select(child_item.index(), QItemSelectionModel.Select)
store_view.expanded.connect(store_view__expanded)
store_view.entered.connect(lambda index: status_bar.showMessage(store_model.itemFromIndex(index).data()))

store_view__selection_changed__blocked = False

#def store_view__selection_model__selection_changed(current, previous):
def store_view__selection_model__current_changed(current, previous):
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
    global store_view__selection_changed__blocked
    store_view__selection_changed__blocked = True
    if store_model.itemFromIndex(previous) and store_model.itemFromIndex(current).data() != store_model.itemFromIndex(previous).data():
        print('New path, clearing selection')
        # TODO: somewhy this doesn't work if mouse button is not released
        store_view.selectionModel().clearSelection()
        #return
    store_path = store_model.itemFromIndex(current).data()
    current_item = store_model.itemFromIndex(current)
    derivation_dict = get_derivation(store_path)
    derivation_model.removeRows(0, 1)
    for key, val in derivation_dict.items():
        add_dict_item(key, val, derivation_model.invisibleRootItem())
    derivation_view.expandAll()
    contents_model.setRootPath(store_path)
    contents_view.setRootIndex(contents_model.index(store_path))
    # Highlight output path matching selected store path
    derivation_item = derivation_model.invisibleRootItem().child(0)
    for i in range(derivation_item.rowCount()):
        if derivation_item.child(i).text() == 'outputs':
            outputs_item = derivation_item.child(i)
            for i in range(outputs_item.rowCount()):
                path_item = outputs_item.child(i).child(0)
                if path_item.text() == 'path: "' + store_path + '"':
                    print(path_item)
                    derivation_view.selectionModel().select(path_item.index(), QItemSelectionModel.ClearAndSelect)
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
    store_view__selection_changed__blocked = False
#store_view.selectionModel().selectionChanged.connect(store_view__selection_model__selection_changed)
store_view.selectionModel().currentChanged.connect(store_view__selection_model__current_changed, Qt.QueuedConnection)

def store_view__selection_model__selection_changed(selected, deselected):
    # Selection should only happen automatically via currentChanged handler
    # it blocks selection signal, so triggered signal is unwanted
    global store_view__selection_changed__blocked
    if store_view__selection_changed__blocked:
        return
    print('Selection changed')
    print('selected indexes', selected.indexes())
    print('deselected indexes', deselected.indexes())
    for index in deselected.indexes():
        store_view.selectionModel().select(index, QItemSelectionModel.Select)
store_view.selectionModel().selectionChanged.connect(store_view__selection_model__selection_changed)

#
# SUMMARY TREE
#

summary_model = QStandardItemModel()
summary_view = QTreeView()
summary_view.setModel(summary_model)
summary_view.setHeaderHidden(True)

def build_summary_tree():
    current_store_path = None
    summary_model.appendRow(QStandardItem('Store path: '+current_store_path))
    deps_direct = QStandardItem('Dependencies (direct)')
    for immediate_reverse_dependency in iter_command_stdout_lines('nix-store --query --referrers '+current_store_path):
        for reverse_dependency in iter_command_stdout_lines('nix-store --query --referrers-closure '+immediate_reverse_dependency):
            print(immediate_reverse_dependency)
            if reverse_dependency in root_paths:
                print('(in closure of '+reverse_dependency+')')
    summary_model.appendRow(deps_direct)

#
# DERIVATION TREE
#

derivation_model = QStandardItemModel()
derivation_view = QTreeView()
derivation_view.setModel(derivation_model)
derivation_view.setHeaderHidden(True)

def get_derivation(path):
    command = 'nix show-derivation ' + path
    process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE)
    (output, _) = process.communicate()
    _ = process.wait()
    if _ == 0:
        return json.loads(output.decode())
    return {}

def add_dict_item(key, val, parent):
    if type(val) is dict:
        child = QStandardItem('"'+key+'": { ... }')
        for key, val in val.items():
            add_dict_item(key, val, child)
    elif type(val) is list:
        child = QStandardItem('"'+key+'": [ ... ]')
        for item in val:
            child.appendRow(QStandardItem('"'+item+'"'))
    else:
        child = QStandardItem('"'+key+'": "'+str(val)+'"')
    parent.appendRow(child)


#
# CONTENTS TREE
#

class CustomFileSystemModel(QFileSystemModel):

    def data(self, index, role):
        if index.isValid():
            if role == Qt.ForegroundRole:
                # Gray text color for symlinks pointing to out-of-current-store-path locations and files accessible via them
                current_store_path = store_model.itemFromIndex(store_view.selectionModel().selectedIndexes()[-1]).data()
                current_path = self.filePath(index)
                if not os.path.realpath(current_path).startswith(current_store_path):
                    return QBrush(Qt.gray)
        return super().data(index, role)


contents_model = CustomFileSystemModel()
contents_view = QTreeView()
contents_view.setModel(contents_model)
contents_view.setMouseTracking(True)
contents_view.entered.connect(lambda index: status_bar.showMessage(contents_model.filePath(index)))

def get_borrowed_file_store_path_item(path):
    # Files are borrowed via symlinks; packages owning destination objects are deps of ones containing symlinks
    # Follow chain of borrowing and select appropriate target store path item
    # Problem: it may not be loaded yet; solution: expand
    current_store_path_item = store_model.itemFromIndex(store_view.selectionModel().selectedIndexes()[-1])
    current_store_path = current_store_path_item.data()
    path_components = path[len(current_store_path)+1:].split('/')
    path_tmp = path[:len(current_store_path)]
    store_path_item_tmp = current_store_path_item
    for path_component in path_components:
        store_view.expand(store_path_item_tmp.index())
        path_tmp = path_tmp + '/' + path_component
        real_path_tmp = os.path.realpath(path_tmp)
        store_path_tmp = '/'.join(real_path_tmp.split('/')[:4])
        print(path_tmp, real_path_tmp, store_path_tmp)
        for i in range(store_path_item_tmp.rowCount()):
            print(i)
            if store_path_item_tmp.child(i) and store_path_item_tmp.child(i).data() == store_path_tmp:
                store_path_item_tmp = store_path_item_tmp.child(i)
                print(store_path_item_tmp.data())
                break
    if not os.path.realpath(path).startswith(store_path_item_tmp.data()):
        raise
    # let currentChanged handler do the selection
    store_view.selectionModel().setCurrentIndex(store_path_item_tmp.index(), QItemSelectionModel.NoUpdate)
    store_view.scrollTo(store_path_item_tmp.index())
    #contents_view.expand(contents_model.index(os.path.realpath(path)))
    contents_view.selectionModel().select(contents_model.index(os.path.realpath(path)), QItemSelectionModel.ClearAndSelect)
    contents_view.scrollTo(contents_model.index(os.path.realpath(path)))


contents_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
def contents_view__custom_contents_menu_requested(point):
    current_store_path = store_model.itemFromIndex(store_view.selectionModel().selectedIndexes()[-1]).data()
    current_path = contents_model.filePath(contents_view.selectionModel().selectedIndexes()[-1])
    context_menu = QMenu()
    if not os.path.realpath(current_path).startswith(current_store_path) and os.path.realpath(current_path).startswith('/nix/store/'):
        action_to_origin = context_menu.addAction('Go to origin store path')
    chosen_action = context_menu.exec_(contents_view.mapToGlobal(point))
    if chosen_action == action_to_origin:
        get_borrowed_file_store_path_item(contents_model.filePath(contents_view.selectionModel().selectedIndexes()[-1]))
contents_view.customContextMenuRequested.connect(contents_view__custom_contents_menu_requested)

profile_dropdown = QComboBox()
profile_generation_dropdown = QComboBox()
for name in os.listdir('/nix/var/nix/profiles'):
    if name.startswith('system'):
        if len(name) == len('system'):
            pass
        else:
            #system_profile_number = name[len('system')+1:]
            system_profile_path = os.path.realpath('/nix/var/nix/profiles/'+name)
            profile_dropdown.addItem('/nix/var/nix/profiles/'+name) #+(' (current)' if os.path.realpath('/run/current-system') else ''))
for username in os.listdir('/nix/var/nix/profiles/per-user'):
    for name in os.listdir('/nix/var/nix/profiles/per-user/'+username):
        if name.startswith('profile'):
            if len(name) == len('profile'):
                pass
            else:
                #system_profile_number = name[len('profile')+1:]
                system_profile_path = os.path.realpath('/nix/var/nix/profiles/per-user/'+username+'/'+name)
                profile_dropdown.addItem('/nix/var/nix/profiles/per-user/'+username+'/'+name)

def profile_dropdown__activated(index):
    system_profile_path = os.path.realpath(profile_dropdown.currentText())
    store_model.removeRows(0, 1)
    print('adding root path', system_profile_path)
    item = add_store_path(os.path.realpath(system_profile_path))
    store_view.selectionModel().select(item.index(), QItemSelectionModel.ClearAndSelect)
profile_dropdown.activated.connect(profile_dropdown__activated)

add_store_path(os.path.realpath('/nix/var/nix/profiles/system'))

layout_base = QVBoxLayout()
layout_selectors = QHBoxLayout()
layout_selectors.addWidget(QLabel('Profile: '))
layout_selectors.addWidget(profile_dropdown)
layout = QHBoxLayout()
layout_base.addLayout(layout_selectors)
layout_base.addLayout(layout)
layout_base.addWidget(status_bar)
layout.addWidget(store_view)
right_tabbed = QTabWidget()
right_tabbed.addTab(derivation_view, 'Derivation')
right_tabbed.addTab(contents_view, 'Contents')
layout.addWidget(right_tabbed)
window = QWidget()
window.setLayout(layout_base)
window.show()
app.exec_()
