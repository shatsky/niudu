#import pyudev
import os
from PySide2.QtWidgets import QApplication, QMenu, QTreeView
from PySide2.QtCore import Qt, QThread, Signal, Slot, QObject, QAbstractProxyModel
from PySide2.QtGui import QStandardItem, QStandardItemModel, QIcon

from . import subsystems
from .device import iter_props_tree_items as iter_device_props_tree_items
from .device import update_dict as update_device_dict
from .ui_device_props_view import device_props_tree_widget
from . import plugins
from .plugins import attach_to_vm
import logging
import pyudev
udev_context = pyudev.Context()

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
    root_device_subtree_path = None
    generator = os.walk('/sys/devices')
    next(generator) # we don't want root node
    for path, subdirs, files in generator:
        # systemd/udev src/libsystemd/sd-device/sd-device.c: "all 'devices' require an 'uevent' file"
        # however, we also want parent nodes like /system, /virtual, etc.
        # is device path
        if 'uevent' in files:
            yield path
            if root_device_subtree_path is None or not path.startswith(root_device_subtree_path):
                root_device_subtree_path = path
        # is not device path, is not child of device path
        elif root_device_subtree_path is None:
            yield path
        elif not path.startswith(root_device_subtree_path):
            yield path
            root_device_subtree_path = None


class DevicesModel(QStandardItemModel):

    # if tree is partitioned into groups, this method should return id of group which device belongs to
    def get_group_id(self, device_path, device_dict):
        return None

    # this method should return root item of subtree in which parent item of item being inserted is to be seeked
    # if tree is partitioned into groups, this method should return root item of subtree of group which device belongs to
    # if it returns None, device item is not inserted
    def get_group_root_item(self, group_id):
        return self.invisibleRootItem()

    def insert(self, device_path, seq=False):
        logger.debug(' '.join(['adding device', str(device_path)]))
        #logger.debug(' '.join(['adding device', str(device_path), str(parent_item.data() if parent_item else None)]))
        if device_path in devices_dict:
            raise(BaseException('Double adding device!'))
        device_dict = {}
        update_device_dict(device_path, device_dict)
        
        # Find parent item
        # TODO: is this complexity worth? Is looking for a path through Qt items hierarchy faster than just looking for it in python dict?
        # Made quick measurment, no certain winner
        group_id = self.get_group_id(device_path, device_dict)
        parent_item = self.get_group_root_item(group_id)
        if parent_item is None:
            return
        if seq:
            # For sequentially added item, parent item is in last grown branch of its group subtree
            # which spans from root to previous added item in it
            #while True:
            #    candidate_parent_item = parent_item.child(parent_item.rowCount()-1)
            #    if candidate_parent_item is not None and device_path.startswith(candidate_parent_item.data()+'/'):
            #        parent_item = candidate_parent_item
            #        continue
            #    break
            # Item is not always appended as last row of its parent, so we have to keep record of last added item for each group
            candidate_parent_item = self.group_last_added_items_dict.get(group_id)
            while candidate_parent_item is not None:
                if candidate_parent_item is parent_item or device_path.startswith(candidate_parent_item.data()+'/'):
                    parent_item = candidate_parent_item
                    break
                candidate_parent_item = candidate_parent_item.parent()
        else:
            while True:
                # For randomly added item
                # Same as code for sequentially added item, this assumes that all ancestors are already in the model
                saved_parent_item = parent_item
                for child_i in range(parent_item.rowCount()):
                    candidate_parent_item = parent_item.child(child_i)
                    if device_path.startswith(candidate_parent_item.data()+'/'):
                        parent_item = candidate_parent_item
                        break
                if parent_item is saved_parent_item:
                    break

        icon = icons[device_dict['subsystem']] if 'subsystem' in device_dict and device_dict['subsystem'] in icons else icons['device']
        item = QStandardItem(icon, device_dict.get('label', '"'+device_dict['node_name']+'"'))
        item.setData(device_path) # to be able to get device path for selected item
        pos = get_device_item_position(device_path, parent_item)
        #print('inserting item as child of parent item "'+parent_item.text()+'"')
        parent_item.insertRow(pos, item)

        devices_dict[device_path] = device_dict
        items_dict[device_path] = item
        global last_added_device
        last_added_device = device_path
        if seq:
            self.group_last_added_items_dict[group_id] = item
        return item
    
    def remove(self, device_path):
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
    
    def reload(self):
        self.clear()
        devices_dict.clear()
        items_dict.clear()
        self.group_last_added_items_dict = {}
        for device_path in iter_devices():
            self.insert(device_path, seq=True)
        del self.group_last_added_items_dict


class DevicesBySubsystemModel(DevicesModel):

    def get_group_id(self, device_path, device_dict):
        return device_dict.get('subsystem')

    def get_group_root_item(self, group_id):
        if group_id is None:
            return
        root_item = self.invisibleRootItem()
        for child_i in range(root_item.rowCount()):
            group_root_item = root_item.child(child_i)
            if group_root_item.data() == group_id:
                return group_root_item
        group_root_item = QStandardItem('"'+group_id+'"')
        group_root_item.setData(group_id)
        root_item.appendRow(group_root_item)
        return group_root_item


class DevicesBySeatModel(DevicesModel):

    def get_group_id(self, device_path, device_dict):
        if 'uevent' not in device_dict['listdir']:
            return
        device_udev_obj = pyudev.Devices.from_sys_path(udev_context, device_path)
        device_dict['udev_properties'] = dict(device_udev_obj.properties)
        device_dict['udev_tags'] = list(device_udev_obj.tags)
        if 'seat' not in device_dict['udev_tags']:
            return
        return device_dict['udev_properties'].get('ID_SEAT', 'seat0')

    def get_group_root_item(self, group_id):
        if group_id is None:
            return
        root_item = self.invisibleRootItem()
        for child_i in range(root_item.rowCount()):
            group_root_item = root_item.child(child_i)
            if group_root_item.data() == group_id:
                return group_root_item
        group_root_item = QStandardItem(icons['seat'], 'Seat "{0}"'.format(group_id))
        group_root_item.setData(group_id)
        root_item.appendRow(group_root_item)
        return group_root_item


class DevicesByIOMMUGroupModel(DevicesModel):

    def get_group_id(self, device_path, device_dict):
        if device_dict.get('subsystem') != 'pci':
            return
        return os.path.realpath(device_path+'/iommu_group').split('/')[-1]

    def get_group_root_item(self, group_id):
        if group_id is None:
            return
        root_item = self.invisibleRootItem()
        for child_i in range(root_item.rowCount()):
            group_root_item = root_item.child(child_i)
            if group_root_item.data() == '/sys/kernel/iommu_groups/'+group_id:
                return group_root_item
        group_root_item = QStandardItem('IOMMU group {0}'.format(group_id))
        group_root_item.setData('/sys/kernel/iommu_groups/'+group_id)
        root_item.appendRow(group_root_item)
        return group_root_item


import subprocess
import xml.etree.ElementTree as ET


class HwLocModel(QStandardItemModel):
    
    def get_sysfs_device_path(self, element):
        object_type = element.attrib.get('type')
        if object_type == 'Bridge':
            if element.attrib.get('bridge_type') == '1-1':
                return os.path.realpath('/sys/bus/pci/devices/'+element.attrib['pci_busid'])
            elif element.attrib.get('bridge_type') == '0-1':
                pci_domain = element.attrib.get('bridge_pci', '')[0:4]
                pci_bus = element.attrib.get('bridge_pci', '')[6:8]
                return os.path.realpath('/sys/devices/pci'+pci_domain+':'+pci_bus)
        elif object_type == 'PCIDev':
            return os.path.realpath('/sys/bus/pci/devices/'+element.attrib['pci_busid'])
        elif object_type == 'OSDev':
            if element.attrib['osdev_type'] == '0':
                return os.path.realpath('/sys/class/block/'+element.attrib['name'])
            elif element.attrib['osdev_type'] == '2':
                return os.path.realpath('/sys/class/net/'+element.attrib['name'])
    
    def get_item_label(self, element):
        object_type = element.attrib.get('type')
        if object_type == 'NUMANode':
            return 'NUMA node'
        elif object_type == 'L3Cache':
            return 'L3 cache'
        elif object_type == 'L2Cache':
            return 'L2 cache'
        elif object_type == 'L1Cache':
            return 'L1 cache'
        elif object_type == 'L1iCache':
            return 'L1i cache'
        elif object_type == 'Bridge':
            pci_bus = element.attrib.get('bridge_pci', '')[6:8]
            if element.attrib.get('bridge_type') == '1-1':
                pci_busid = element.attrib.get('pci_busid', '')
                pci_device = pci_busid[8:10]
                pci_function = pci_busid[11]
                if pci_function != '00':
                    return 'Bridge to PCI bus {0} (PCI device {1} function {2})'.format(pci_bus, pci_device, pci_function)
                return 'Bridge to PCI bus {0} (PCI device {1})'.format(pci_bus, pci_device)
            elif element.attrib.get('bridge_type') == '0-1':
                return 'Bridge to PCI bus {0}'.format(pci_bus)
        elif object_type == 'PU':
            return 'Processing unit'
        elif object_type == 'PCIDev':
            pci_busid = element.attrib.get('pci_busid', '')
            pci_device = pci_busid[8:10]
            pci_function = pci_busid[11]
            if pci_function != '00':
                return 'PCI device {0} function {1}'.format(pci_device, pci_function)
            return 'PCI device {0}'.format(pci_device)
        elif object_type == 'OSDev':
            if element.attrib['osdev_type'] == '0':
                return 'OS device "{0}" (block storage)'.format(element.attrib['name'])
            elif element.attrib['osdev_type'] == '2':
                return 'OS device "{0}" (network interface)'.format(element.attrib['name'])
            return 'OS device "{0}"'.format(name)
        return object_type
            
    def reload(self):
        topo_xml_text = subprocess.run(['lstopo', '--output-format', 'xml'], stdout=subprocess.PIPE).stdout
        topo_xml_tree = ET.fromstring(topo_xml_text)
        prev_element = topo_xml_tree.find('./object')
        prev_item = QStandardItem(self.get_item_label(prev_element))
        self.invisibleRootItem().appendRow(prev_item)
        stack_elements = []
        stack_items = []
        generator = prev_element.iter()
        next(generator)
        for element in generator:
            if element.tag != 'object':
                continue
            #if prev_element is element.parent():
            if element in prev_element:
                stack_elements.append(prev_element)
                stack_items.append(prev_item)
                parent_element = prev_element
                parent_item = prev_item
            else:
                for i in reversed(range(len(stack_elements))):
                    #if stack_elements[i] is element.parent():
                    if element in stack_elements[i]:
                        parent_element = stack_elements[i]
                        parent_item = stack_items[i]
                        stack_elements[i+1:] = []
                        stack_items[i+1:] = []
                        break
            prev_element = element
            prev_item = QStandardItem(self.get_item_label(element))
            prev_item.setData(self.get_sysfs_device_path(element))
            parent_item.appendRow(prev_item)


# In Qt app GUI entities can only be changed from the main thread,
# so for asynchronously adding/removing tree items we have to implement class with method which will run in background thread and emit signals
# telling handler in main thread to add/remove items
class DeviceMonitor(QObject):
    
    device_signal = Signal(object) # event
    
    @Slot() # handler
    def monitor_devices(self):
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        for device in iter(monitor.poll, None):
            logging.debug(' '.join(['emitting device event:', str(device.action), str(device)]))
            self.device_signal.emit(device) # fire "device_signal" event, passing device to handler


class DevicesView(QTreeView):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
        self.setModel(DevicesModel())
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu_handler)
        
        self.reload()
        
        self.device_monitor = DeviceMonitor()
        self.thread = QThread(self)
        self.device_monitor.device_signal.connect(self.device_signal__handler) # set handler for device_monitor "device_signal" event
        self.device_monitor.moveToThread(self.thread)
        self.thread.setObjectName('DeviceMonitorThread')
        self.thread.started.connect(self.device_monitor.monitor_devices) # set handler for thread "started" event
        self.thread.start()
    
    @Slot(object) # handler
    def device_signal__handler(self, device):
        action = device.action
        logging.debug(' '.join(['handling device event:', str(action), str(device)]))
        device_path = device.sys_path
        if not device_path.startswith('/sys/devices/'):
            return
        elif action == 'add':
            item = self.model().insert(device.sys_path)
            self.set_current_item(item)
        elif action == 'remove':
            current_device_path = self.get_current_device()
            parent_item = self.model().remove(device.sys_path)
            if current_device_path.startswith(device_path):
                self.set_current_index(parent_item.index())
    
    def reload(self):
        current_device_path = self.get_current_device()
        self.model().reload()
        if current_device_path is not None:
            self.set_current_device(current_device_path)

    def currentChanged(self, current, previous):
        QTreeView.currentChanged(self, current, previous)
        device_path = self.model().itemFromIndex(current).data()
        logging.debug('device selected: '+device_path)
        device_props_tree_widget.clear()
        device_props_tree_widget.addTopLevelItems([item for item in iter_device_props_tree_items(device_path, devices_dict[device_path])])
        device_props_tree_widget.expandAll()
        if self.history_push_flag:
            self.history_push(device_path)
        self.history_push_flag = True

    def get_current_device(self):
        current_index = self.currentIndex()
        if current_index is not None:
            current_item = self.model().itemFromIndex(current_index)
            if current_item is not None:
                return current_item.data()

    def set_current_index(self, index):
        self.setCurrentIndex(index)
        self.scrollTo(index)

    # scrollTo() doesn't expand everything (bug?), thus have to expand() every ancestor explicitly
    def set_current_item(self, item):
        parent = item.parent()
        while parent is not None:
            self.expand(parent.index())
            parent = parent.parent()
        index = item.index()
        self.set_current_index(index)

    def set_current_device(self, device_path):
        item = items_dict[device_path]
        self.set_current_item(item)
        
    def context_menu_handler(self, point):
        device_path = self.get_current_device()
        context_menu = QMenu()
        action_copy_path = context_menu.addAction('Copy path')
        device_listdir = os.listdir(device_path)
        if 'firmware_node' in device_listdir:
            action_to_firmware = context_menu.addAction('Go to firmware node')
        elif 'physical_node' in device_listdir:
            action_to_physical = context_menu.addAction('Go to physical node')
        # plugins which extend device actions menu must implement add_device_actions(device, menu, tuples) method
        #  it should add actions to the menu object
        #  and append (action, handler, handler_args, handler_kwargs) to the tuples list
        # tuples list is then used to check for chosen action and to call matching handler with args
        plugins_actions_tuples = []
        device = devices_dict[device_path]
        for plugin in [plugins.attach_to_vm]:
            if 'add_device_actions' in dir(plugin):
                plugin.add_device_actions(device, context_menu, plugins_actions_tuples)
        chosen_action = context_menu.exec_(self.mapToGlobal(point))
        if chosen_action == action_copy_path:
            clipboard.setText(device_path)
        elif 'firmware_node' in device_listdir and chosen_action is action_to_firmware:
            target_device_path = os.path.abspath(os.path.join(device_path, os.readlink(os.path.join(device_path, 'firmware_node'))))
            self.set_current_device(target_device_path)
        elif 'physical_node' in device_listdir and chosen_action is action_to_physical:
            target_device_path = os.path.abspath(os.path.join(device_path, os.readlink(os.path.join(device_path, 'physical_node'))))
            self.set_current_device(target_device_path)
        else:
            for action, handler, args, kwargs in plugins_actions_tuples:
                if chosen_action == action:
                    handler(device, *args, **kwargs)
                    break


    # QTreeView doesn't seem to have any navigation history logic, thus implement our own
    # Provides signal for external widgets like toolbar nav buttons to update state when history state changes
    history_list = []
    history_index = 0
    history_push_flag = True
    history_back_flag = False
    history_forward_flag = False
    history_signal = Signal(bool, bool)
    
    def history_push(self, device_path):
        self.history_list = self.history_list[self.history_index:self.history_index+16]
        self.history_list.insert(0, device_path)
        self.history_index = 0
        self.history_forward_flag = False
        if len(self.history_list)>1:
            self.history_back_flag = True
        self.history_signal.emit(self.history_back_flag, self.history_forward_flag)

    def history_back(self):
        # TODO: device can be already gone
        self.history_push_flag = False
        self.history_index += 1
        self.set_current_device(self.history_list[self.history_index])
        self.history_forward_flag = True
        if self.history_index == len(self.history_list)-1:
            self.history_back_flag = False
        self.history_signal.emit(self.history_back_flag, self.history_forward_flag)

    def history_forward(self):
        self.history_push_flag = False
        self.history_index -= 1
        self.set_current_device(self.history_list[self.history_index])
        self.history_back_flag = True
        if self.history_index == 0:
            self.history_forward_flag = False
        self.history_signal.emit(self.history_back_flag, self.history_forward_flag)


# given 2 paths, function has to choose one which goes first
# this is expected to handle complex cases, e. g. to place sound card input nodes next to matching sound devices
def get_upper_path(path1, path2):
    if '/sys/devices/system' in (path1, path2):
        return '/sys/devices/system'
    elif '/sys/devices/platform' in (path1, path2):
        return '/sys/devices/platform'
    elif '/sys/devices/LNXSYSTM:00' in (path1, path2):
        return '/sys/devices/LNXSYSTM:00'
    elif '/sys/devices/pnp0' in (path1, path2):
        return '/sys/devices/pnp0'
    elif '/sys/devices/pci0000:00' in (path1, path2):
        return '/sys/devices/pci0000:00'
    elif path1 == '/sys/devices/virtual' and 'name' in dir(devices_dict[path2]):
        return path2
    elif path2 == '/sys/devices/virtual' and 'name' in dir(devices_dict[path1]):
        return path1
    else:
        if path1 is None or path2 is None:
            return path1
        return min(path1, path2)

#def get_device_item_position(item, parent_item):
def get_device_item_position(device_path, parent_item):
    i = 0
    while i < parent_item.rowCount():
        #if parent_item.child(i).text() > item.text():
        if get_upper_path(parent_item.child(i).data(), device_path) == device_path:
            break
        i += 1
    return i

clipboard = QApplication.clipboard()
   
# load icons
icons = {}
icons_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons')
for item_name in os.listdir(icons_dir):
    if item_name.endswith('.png'):
        icons[item_name[:-len('.png')]] = QIcon(os.path.join(icons_dir, item_name))
if 'scsi' in icons:
    for subsystem_name in ['bsg', 'scsi_device', 'scsi_disk', 'scsi_host']:
        icons[subsystem_name] = icons['scsi']
