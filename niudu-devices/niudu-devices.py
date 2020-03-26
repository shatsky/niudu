#import pyudev
import os
import sys
from PySide2.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMenuBar, QMenu, QTreeView
from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItem, QStandardItemModel #, QTreeView

import subsystems
from util import get_file_contents, get_symlink_path
from device import GenericDevice
from device import iter_props_tree_items as iter_device_props_tree_items
from device import update_dict as update_device_dict


app = QApplication(sys.argv)
device_props_tree_widget = QTreeWidget()
#device_props_tree_widget.setExpanded(True)

# for addressing QTreeWidgetItem items in to device_props_tree_widget by device paths
items_dict = {}

# for addressing dicts holding reusable data mostly obtained from sysfs by device paths
devices_dict = {}

#udev_context = pyudev.Context()
#for device in udev_context.list_devices():
#    add_device(device, items_dict)
# libudev enumeration isn't acceptable
# it skips various devices, e. g. USB hub interface ports
def iter_devices():
    for path, subdirs, files in os.walk('/sys/devices'):
        # we can yield paths here
        if 'uevent' in files:
            yield path
        # or we can nested loop over subdirs and yield (parent_path, subdir_path) tuples

def get_parent(device_path):
    return '/'.join(device_path.split('/')[:-1])

devices_model = QStandardItemModel()
devices_view = QTreeView()
devices_view.setModel(devices_model)

# given 2 paths, function has to choose one which goes first
# this is expected to handle complex cases, e. g. to place sound card input nodes next to matching sound devices
def get_upper_path(path1, path2):
    if '/devices/system' in (path1, path2):
        return '/devices/system'
    elif '/devices/platform' in (path1, path2):
        return '/devices/platform'
    elif '/devices/LNXSYSTM:00' in (path1, path2):
        return '/devices/LNXSYSTM:00'
    elif '/devices/pnp0' in (path1, path2):
        return '/devices/pnp0'
    elif '/devices/pci0000:00' in (path1, path2):
        return '/devices/pci0000:00'
    elif path1 == '/devices/virtual' and 'name' in dir(devices_dict['/sys'+path2]):
        return path2
    elif path2 == '/devices/virtual' and 'name' in dir(devices_dict['/sys'+path1]):
        return path1
    else:
        return min(path1, path2)

def get_device_position(item, device_parent):
    device_path = item.data()
    i = 0
    while i < device_parent.rowCount():
        #if device_parent.child(i).text() > item.text():
        if '/sys'+get_upper_path(device_parent.child(i).data()[len('/sys'):], item.data()[len('/sys'):]) == item.data():
            break
        i += 1
    return i

def add_device(device_path, device_parent=None):
    print('adding', device_path, device_parent.data() if device_parent else None)
    device_dict = {}
    update_device_dict(device_path, device_dict)
    devices_dict[device_path] = device_dict
    #return {'device_path': device_path}
    if not device_parent:
        device_parent = devices_model.invisibleRootItem()
    item = QStandardItem(device_dict['name'])
    item.setData(device_path)
    i = 0
    while i < device_parent.rowCount():
        if device_parent.child(i).text() > item.text():
            break
        i += 1
    i = get_device_position(item, device_parent)
    print('position: ', i)
    #device_parent.appendRow(item)
    # insertRow(i, item) gives weird results
    device_parent.insertRow(i, [])
    device_parent.setChild(i, item)
    items_dict[device_path] = item
    return item

# simplification: there should always be prev_item
# initial value is model's invisible_root_node
def add_devices():
    base_path = '/sys/devices'
    parent_items = []
    prev_item = devices_model.invisibleRootItem()
    prev_item.setData(base_path)
    for device_path in iter_devices():
        print('new device: ', device_path)
        if get_parent(device_path).startswith(prev_item.data()):  # if previous item was current ones parent (down to first child of prev)
            parent_items += [prev_item]
        elif not get_parent(prev_item.data()) == get_parent(device_path): # (up+forward[+down] to next sibling of some ancestor of prev or its child)
            while not (parent_items[-1].data() == get_parent(device_path) or parent_items[-1].data() in get_parent(device_path)):
                parent_items = parent_items[:-1]
            # in the last case, last item in parent_items can be a non-device; if it is, all child nodes down to current item should be added as well
            if 'uevent' not in os.listdir(parent_items[-1].data()):
                print('adding parent directories')
                device_path_components = device_path.split('/')
                #              /sys/devices: 3              /sys/devices/system/cpu: 5
                for i in range(len((base_path if not parent_items else parent_items[-1].data()).split('/'))+1, len(device_path_components)):
                    parent_items += [add_device('/'.join(device_path_components[:i]), parent_items[-1] if parent_items else None)]
        #else: pass  # if previous items parent is current ones parent (forward to next sibling of prev)
        prev_item = add_device(device_path, parent_items[-1] if parent_items else None)


add_devices()

clipboard = QApplication.clipboard()
    
def context_menu_handler(point):
    #device = treeWidget.currentItem().data(0, -1)
    device_path = devices_model.itemFromIndex(devices_view.selectionModel().selectedIndexes()[-1]).data()
    context_menu = QMenu()
    action_copy_path = context_menu.addAction('Copy path')
    device_listdir = os.listdir(device_path)
    if 'firmware_node' in device_listdir:
        action_to_firmware = context_menu.addAction('Go to firmware node')
    elif 'physical_node' in device_listdir:
        action_to_physical = context_menu.addAction('Go to physical node')
    chosen_action = context_menu.exec_(devices_view.mapToGlobal(point))
    if chosen_action == action_copy_path:
        clipboard.setText(device_path)
    elif 'firmware_node' in device_listdir and chosen_action is action_to_firmware:
        target_device_path = os.path.abspath(os.path.join(device_path, os.readlink(os.path.join(device_path, 'firmware_node'))))[len('/sys'):]
        #treeWidget.setCurrentItem(items_dict[device_path])
        devices_view.selectionModel().select(items_dict[target_device_path].index())
    elif 'physical_node' in device_listdir and chosen_action is action_to_physical:
        target_device_path = os.path.abspath(os.path.join(device_path, os.readlink(os.path.join(device_path, 'physical_node'))))[len('/sys'):]
        tree_view.setCurrentItem(items_dict[target_device_path])

#treeWidget.currentItemChanged.connect(tree_item_clicked)
#treeWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
#treeWidget.customContextMenuRequested.connect(context_menu_handler)

devices_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
devices_view.customContextMenuRequested.connect(context_menu_handler)

def devices_view_item_clicked(current, previous):
    device_path = devices_model.itemFromIndex(current.indexes()[-1]).data()
    device_props_tree_widget.clear()
    device_props_tree_widget.addTopLevelItems([item for item in iter_device_props_tree_items(device_path, devices_dict[device_path])])
    device_props_tree_widget.expandAll()

devices_view.selectionModel().selectionChanged.connect(devices_view_item_clicked)

#top_menu = QMenuBar()
#device_menu = top_menu.addMenu('Device')

window = QWidget()
layout = QHBoxLayout()
#layout.addWidget(top_menu)
#layout.addWidget(treeWidget)
layout.addWidget(devices_view)
#layout.addWidget(tableWidget)
layout.addWidget(device_props_tree_widget)
window.setLayout(layout)
window.show()
print('executing')
app.exec_()
