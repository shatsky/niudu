#import pyudev
import os
from PySide2.QtWidgets import QApplication, QMenu, QTreeView
from PySide2.QtCore import Qt, QItemSelectionModel, QThread, Signal, Slot, QObject
from PySide2.QtGui import QStandardItem, QStandardItemModel, QIcon

import subsystems
from device import iter_props_tree_items as iter_device_props_tree_items
from device import update_dict as update_device_dict
from ui_device_props_view import device_props_tree_widget
import logging


logging.basicConfig(format="%(threadName)s:%(message)s")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# for addressing QStandardItem items in devices_view by device paths
items_dict = {}

# for addressing dicts holding reusable data mostly obtained from sysfs by device paths
devices_dict = {}

last_added_device = None

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


#devices_model = QStandardItemModel()


# In Qt app GUI items can only be changed from the main thread,
# so for asynchronously adding/removing tree items we have to implement class with method which will run in background thread and emit signals
# telling handler in main thread to add/remove items
class DeviceMonitor(QObject):
    
    device_signal = Signal(object)
    
    @Slot()
    def monitor_devices(self):
        import pyudev
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        for device in iter(monitor.poll, None):
            logging.debug(' '.join(['emitting device event:', str(device.action), str(device)]))
            self.device_signal.emit(device)


class DevicesView(QTreeView):
    def __init__(self, *args, **kwargs):
        QTreeView.__init__(self)
        
        self.model = QStandardItemModel()
        self.setModel(self.model)
        
        self.device_monitor = DeviceMonitor()
        self.thread = QThread(self)
        self.device_monitor.device_signal.connect(self.device_signal__handler)
        self.device_monitor.moveToThread(self.thread)
        self.thread.started.connect(self.device_monitor.monitor_devices)
        self.thread.start()
    
    @Slot(object)
    def device_signal__handler(self, device):
        action = device.action
        logging.debug(' '.join(['handling device event:', str(action), str(device)]))
        device_path = device.sys_path
        if not device_path.startswith('/sys/devices/'):
            return
        elif action == 'add':
            item = add_device(device.sys_path)
            #set_current_device(device_path)
            set_current_item(item)
        elif action == 'remove':
            current_device_path = get_current_device()
            parent_item = remove_device(device.sys_path)
            if current_device_path.startswith(device_path):
                set_current_index(parent_item.index())
    
    def reload(self):
        selected_indexes = devices_view.selectionModel().selectedIndexes()
        current_device_path = devices_model.itemFromIndex(selected_indexes[-1]).data() if selected_indexes else None
        self.model.reload()
        if current_device_path is not None:
            set_current_device(current_device_path)


#devices_view = QTreeView()
devices_view = DevicesView()
#devices_view.setModel(devices_model)
devices_model = devices_view.model

def get_parent_item(device_path):
    device_path_parts = device_path.split('/')
    for i in reversed(range(len(device_path_parts))):
        #print('trying parent', '/'.join(device_path_parts[:i]))
        device_parent = items_dict.get('/'.join(device_path_parts[:i]))
        if device_parent is not None:
            return device_parent
    return devices_model.invisibleRootItem()

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

#def get_device_item_position(item, parent_item):
def get_device_item_position(device_path, parent_item):
    i = 0
    while i < parent_item.rowCount():
        #if parent_item.child(i).text() > item.text():
        if '/sys'+get_upper_path(parent_item.child(i).data()[len('/sys'):], device_path[len('/sys'):]) == device_path:
            break
        i += 1
    return i

def add_device(device_path, parent_item=None):
    logger.debug(' '.join(['adding device', str(device_path), str(parent_item.data() if parent_item else None)]))
    if device_path in devices_dict:
        raise(BaseException('Double adding device!'))
    device_dict = {}
    update_device_dict(device_path, device_dict)
    devices_dict[device_path] = device_dict
    icon = icons[device_dict['subsystem']] if 'subsystem' in device_dict and device_dict['subsystem'] in icons else icons['device']
    item = QStandardItem(icon, device_dict['name'])
    item.setData(device_path) # to be able to get device path for selected item
    if parent_item is None:
        parent_item = get_parent_item(device_path)
    pos = get_device_item_position(device_path, parent_item)
    parent_item.insertRow(pos, item)
    items_dict[device_path] = item
    global last_added_device
    last_added_device = device_path
    return item

def remove_device(device_path):
    print('removing device', device_path)
    if device_path in devices_dict:
        del devices_dict[device_path]
    if device_path in items_dict:
        item = items_dict[device_path]
        parent_item = item.parent()
        if parent_item is None:
            parent_item = devices_model.invisibleRootItem()
        parent_item.removeRow(item.row())
        del items_dict[device_path]
        return parent_item

# simplification: there should always be prev_item
# initial value is model's invisible_root_node
def add_devices():
    selected_indexes = devices_view.selectionModel().selectedIndexes()
    current_device_path = devices_model.itemFromIndex(selected_indexes[-1]).data() if selected_indexes else None
    devices_model.clear()
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
    if current_device_path is not None:
        set_current_device(current_device_path)


clipboard = QApplication.clipboard()

def get_current_device():
    return devices_model.itemFromIndex(devices_view.selectionModel().selectedIndexes()[-1]).data()
    
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
        target_device_path = os.path.abspath(os.path.join(device_path, os.readlink(os.path.join(device_path, 'firmware_node'))))
        set_current_device(target_device_path)
    elif 'physical_node' in device_listdir and chosen_action is action_to_physical:
        target_device_path = os.path.abspath(os.path.join(device_path, os.readlink(os.path.join(device_path, 'physical_node'))))
        set_current_device(target_device_path)

#treeWidget.currentItemChanged.connect(tree_item_clicked)
#treeWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
#treeWidget.customContextMenuRequested.connect(context_menu_handler)

devices_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
devices_view.customContextMenuRequested.connect(context_menu_handler)

def devices_view_item_selected(current, previous):
    current_indexes = current.indexes()
    print('selection changed', current_indexes)
    if current_indexes:
        device_path = devices_model.itemFromIndex(current.indexes()[-1]).data()
        logging.debug('device selected: '+device_path)
        device_props_tree_widget.clear()
        device_props_tree_widget.addTopLevelItems([item for item in iter_device_props_tree_items(device_path, devices_dict[device_path])])
        device_props_tree_widget.expandAll()

devices_view.selectionModel().selectionChanged.connect(devices_view_item_selected)

# load icons
icons = {}
for item_name in os.listdir('icons'):
    if item_name.endswith('.png'):
        icons[item_name[:-len('.png')]] = QIcon('icons/'+item_name)

def set_current_index(index):
    # "selected" and "current" are different things
    #devices_view.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)
    devices_view.setCurrentIndex(index)
    devices_view.scrollTo(index)

# scrollTo() doesn't expand everything (bug?), thus have to expand() every ancestor explicitly
# TODO: scrollTo() also causes unwanted scrolling, have to scroll explicitly
def set_current_item(item):
    parent = item.parent()
    while parent is not None:
        devices_view.expand(parent.index())
        parent = parent.parent()
    index = item.index()
    set_current_index(index)

def set_current_device(device_path):
    item = items_dict[device_path]
    set_current_item(item)

# populate ui_devices_view
add_devices()
