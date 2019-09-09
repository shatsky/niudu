#import pyudev
import os
import sys
from PySide2.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMenuBar, QMenu, QTreeView
from PySide2.QtCore import Qt
from PySide2.QtGui import QStandardItem, QStandardItemModel #, QTreeView

#udev_context = pyudev.Context()

def iterate_devices():
    for path, subdirs, files in os.walk('/sys/devices/'):
        if path == '/sys/devices/':
            pass
        if 'uevent' in files:
            yield path
        elif not device_parent(path):
            yield path

# return parent node that _is_ a device
# if current node is a device, otherwise return parent
def device_parent(path, root='/sys/devices'):
    #if path !=root and 'uevent' not in path:
    #    return '/'.join(path.split('/')[:-1])
    parent = path
    while parent != root:
        parent = '/'.join(parent.split('/')[:-1])
        if 'uevent' in os.listdir(parent):
            return parent
    parent = '/'.join(path.split('/')[:-1])
    if parent != root:
        return parent
    

def add_device(items_dict, device): #, props):
    # some devices are False
    if device in items_dict:
        return
    if device_parent(device) is not None and device_parent(device) not in items_dict:
        # find place between siblings
        # default: alphanumeric order
        # special cases:
        # -pci bus before devices
        # -usb endpoint first, then configs:interfaces of parent device, then child devices
        # -event sources always last
        # to do this we have to interate siblings with their paths
        add_device(items_dict, device_parent(device)) #, get_subsystem_specific_props(device.parent))
    item = QTreeWidgetItem(items_dict[device_parent(device)] if device_parent(device) is not None else None, [devices_dict.get(device, {}).get('name') or device.split('/')[-1]]) #[props.get('tree_name', device.sys_name)])
    item.setData(0, -1, device)  # to identify device in a clicked item
    #if device has access node:
    #    item_font = QtGui.QFont()
    #    item_font.setBold(True)
    #    item.setFont(item_font)
    #    #item.setFont(QtGui.QFont(weight=QtGui.QFont.Bold))
    items_dict[device] = item

app = QApplication(sys.argv)
device_props_tree_widget = QTreeWidget()
#device_props_tree_widget.setExpanded(True)
items_dict = {}
#for device in udev_context.list_devices():
#    add_device(device, items_dict)

pci_db = {}
pci_db_class = {}
with open('/nix/store/lj9647ggaf470xrvl8cr5lr8r2w2ji6i-pciutils-3.6.2/share/pci.ids') as f:
    scope_class = False
    for line in f:
        if line.startswith('#'): continue
        line_len_full = len(line)
        line = line.lstrip('\t')
        indent = line_len_full - len(line)
        if indent == 0:
            if line.startswith('C '):
                scope_class = True
                pci_class = (line[6:-1], {})
                pci_db_class[line[2:4]] = pci_class
            else:
                scope_class = False
                vendor = (line[6:-1], {})
                pci_db[line[:4]] = vendor
        elif indent == 1:
            if scope_class:
                subclass = (line[4:-1], {})
                pci_class[1][line[0:2]] = subclass
            else:
                device = (line[6:-1], {})
                vendor[1][line[:4]] = device
        elif indent == 2:
            if scope_class:
                # interface
                subclass[1][line[0:2]] = line[4:-1]
            else:
                # subsystem vendor&device
                device[1][line[:9]] = line[11:-1]

#print(pci_db_class); exit()

pnp_db = {}
with open('pnp.ids') as f:
    scope_class = False
    for line in f:
        if line.startswith('#'): continue
        line_len_full = len(line)
        line = line.lstrip('\t')
        indent = line_len_full - len(line)
        if indent == 0:
            vendor = (line[5:-1], {})
            pnp_db[line[:3]] = vendor
        elif indent == 1:
            vendor[1][line[:4]] = line[6:-1]
pnp_db['pnp'][1]['0a08'] = 'PCI Bus'

acpi_names_dict = {
    'LNXSYSTM': 'root',
    '_HID': 'device',
    'LNXCPU': 'processor',
    'LNXTHERM': 'thermal zone',
    'LNXPOWER': 'porwer resource',
    'device': 'device',
    'LNXPWRBN': 'power button',
    'LNXSLPBN': 'sleep button',
    'LNXVIDEO': 'video extension',
    'LNXIOBAY': 'ATA controller',
    'LNXDOCK': 'docking station',
    'LNXSYBUS': 'system bus',
    #'INT33A0': 'Intel Smart Connect',
    #'PNP0A03': 'PCI host bridge',
    #'PNP0A08': 'PCI host bridge',
    #'PNP0C01': 'memory controller',
    #'PNP0C0C': 'power button',
    #'PNP0C0D': 'power lid',
    #'PNP0C0F': 'PCI interrupt link',
    #'INTC0102': 'TPM',
    #'PNP0C02': 'resource reservation',
}

# http://www.linux-usb.org/usb.ids
usb_db = {}
usb_db_class = {}
with open('usb.ids', errors='replace') as f:
    scope = None
    for line in f:
        line = str(line)
        if line.startswith('#'): continue
        line_len_full = len(line)
        line = line.lstrip('\t')
        indent = line_len_full - len(line)
        if indent == 0:
            if line[0].isdigit() or 'a' <= line[0] <= 'f':
                scope = 'device'
                vendor = (line[6:-1], {})
                usb_db[line[:4]] = vendor
            elif line[0] == 'C':
                scope = 'class'
                usb_class = (line[6:-1], {})
                usb_db_class[line[2:4]] = usb_class
            else:
                scope = None
        elif indent == 1:
            if scope == 'class':
                subclass = (line[4:-1], {})
                usb_class[1][line[0:2]] = subclass
            elif scope == 'device':
                device = (line[6:-1], {})
                vendor[1][line[:4]] = device
        elif indent == 2:
            if scope == 'class':
                # interface
                subclass[1][line[0:2]] = line[4:-1]
            elif scope == 'device':
                # protocol
                device[1][line[:9]] = line[11:-1]

def read(device, key, props):
    with open(os.path.join(device.sys_path, key), 'r') as f:
        props[key] = f.read().strip()

def read_device_file(device, filename):
    try:
        with open(os.path.join(device.sys_path, filename), 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def get_symlink_path(device, symlink_name):
    return os.path.realpath(device+'/'+symlink_name)

def get_file_contents(device, filename):
    with open(os.path.join(device, filename), 'r') as f:
        return f.read()[:-1]

devices_dict = {}

# Update device dict functions fill dict with data nesessary for displaying device item in devices tree
# This dict can be reused by props tree functions to avoid duplicate file access and other operations

def update_device_dict(device):
    device_dict = devices_dict.get(device)
    if 'subsystem' in os.listdir(device):
        device_dict['subsystem'] = get_symlink_path(device, 'subsystem').split('/')[-1]
        if 'update_device_dict_subsystem_'+device_dict['subsystem'] in globals():
            globals()['update_device_dict_subsystem_'+device_dict['subsystem']](device)
    else:
        device_name = device.split('/')[-1]
        if device_name.startswith('ep_'):
            device_dict['name'] = 'USB endpoint '+device_name[3:]
        elif device_name.startswith('pci'):
            device_dict['name'] = 'PCI domain ' + device_name[3:7] + ' host bridge (to bus ' + device_name[8:10] + ') root'
        elif device.startswith('/sys/devices/pnp') and device[len('/sys/devices/pnp'):].isdigit():
            pnp_protocol = device[len('/sys/devices/pnp'):]
            if '00:00' in os.listdir(device) and 'firmware_node' in os.listdir(device+'/00:00') and get_symlink_path(device+'/00:00/firmware_node', 'subsystem').endswith('/acpi'):
                pnp_protocol = 'ACPI'
            device_dict['name'] = 'PnP'
            if pnp_protocol == 'ACPI':
                device_dict['name'] += ' root for ACPI (devices known exclusively from ACPI)'
            else:
                pass
        elif device.startswith('/sys/devices/platform'):
            if device == '/sys/devices/platform':
                device_dict['name'] = 'Platform root (devices known from this system\'s platform architecture)'
        elif device.startswith('/sys/devices/system'):
            if device == '/sys/devices/system':
                device_dict['name'] = 'System devices (devices and abstractions available on any supported platform)'
            if device == '/sys/devices/system/node':
                device_dict['name'] = 'NUMA root'
        elif device.startswith('/sys/devices/virtual'):
            if device == '/sys/devices/virtual':
                device_dict['name'] = 'Virtual devices'
        elif device_name.startswith('ata') and 'ata_port' in os.listdir(device) and device_name in os.listdir(device+'/ata_port') and get_symlink_path(device+'/ata_port/'+device_name, 'subsystem').endswith('ata_port'):
            device_dict['name'] = 'ATA port ' + device_name[3:]
        elif device_name.startswith('link') and 'ata_link' in os.listdir(device) and device_name in os.listdir(device+'/ata_link') and get_symlink_path(device+'/ata_link/'+device_name, 'subsystem').endswith('ata_link'):
            device_dict['name'] = 'ATA link ' + device_name[4:]

def update_device_dict_subsystem_pci(device):
    device_dict = devices_dict.get(device)
    device_dict['name'] = 'PCI'
    device_dict['pci_device'] = device[-4:-2]
    device_dict['pci_function'] = device[-1]
    device_dict['pci_class'] = get_file_contents(device, 'class')
    device_dict['pci_class_base'] = '0x' + device_dict['pci_class'][2:4]
    device_dict['pci_class_subclass'] = '0x' + device_dict['pci_class'][4:6]
    device_dict['pci_class_interface'] = '0x' + device_dict['pci_class'][6:]
    db_base_class = pci_db_class.get(device_dict['pci_class_base'][2:])
    if db_base_class:
        device_dict['pci_class_base_name'] = db_base_class[0]
        db_subclass = db_base_class[1].get(device_dict['pci_class_subclass'][2:])
        if db_subclass:
            device_dict['pci_class_subclass_name'] = db_subclass[0]
            db_interface = db_subclass[1].get(device_dict['pci_class_interface'][2:])
            if db_interface:
                device_dict['pci_class_interface_name'] = db_interface
    device_dict['name'] += ' device ' + device_dict['pci_device']
    if device_dict['pci_function'] != '0':
        device_dict['name'] += ' function ' + device_dict['pci_function']
    if 'pci_class_subclass_name' in device_dict:
        device_dict['name'] += ': ' + device_dict['pci_class_subclass_name']
    elif 'pci_class_base_name' in device_dict:
        device_dict['name'] += ': ' + device_dict['pci_class_base_name']
    if device_dict['pci_class_base'] == '0x06' and device_dict['pci_class_subclass'] == '0x04':
        device_dict['name'] += ' (to bus ' + os.listdir(device+'/pci_bus')[0][-2:] + ')'

def update_device_dict_subsystem_usb(device):
    # http://www.linux-usb.org/FAQ.html
    device_dict = devices_dict.get(device)
    device_dict['name'] = 'USB'
    addr = device.split('/')[-1]
    device_dict['usb_bus'], addr = (addr.split('-', 1) + [None])[:2]
    #device_dict['name'] += ' bus ' + device_dict['usb_bus']
    if addr:
        device_dict['usb_port'], addr = (addr.split(':', 1) + [None])[:2]
        #device_dict['name'] += ' port ' + device_dict['usb_port']
        if addr:
            device_dict['usb_config'], addr = (addr.split('.', 1) + [None])[:2]
            device_dict['name'] += ' config ' + device_dict['usb_config']
            if addr:
                device_dict['usb_iface'] = addr
                device_dict['name'] += ' interface ' + device_dict['usb_iface']
        else:
            device_dict['name'] += ' device on port ' + device_dict['usb_port']
            device_dict['usb_class'] = get_file_contents(device, 'bDeviceClass')
    else:
        device_dict['name'] += ' bus ' + device_dict['usb_bus']

    if 'usb_iface' not in device_dict:
        device_dict['usb_class'] = get_file_contents(device, 'bDeviceClass')
        device_dict['usb_subclass'] = get_file_contents(device, 'bDeviceSubClass')
        device_dict['usb_protocol'] = get_file_contents(device, 'bDeviceProtocol')
    else:
        device_dict['usb_class'] = get_file_contents(device, 'bInterfaceClass')
        device_dict['usb_subclass'] = get_file_contents(device, 'bInterfaceSubClass')
        device_dict['usb_protocol'] = get_file_contents(device, 'bInterfaceProtocol')

    if device_dict['usb_class'] == '00':
        device_dict['name'] += ': (class defined at interface level)'
    else:
        db_class = usb_db_class.get(device_dict['usb_class'])
        if db_class:
            device_dict['usb_class_name'] = db_class[0]
            device_dict['name'] += ': ' + db_class[0]
            db_subclass = db_class[1].get(device_dict['usb_subclass'])
            if db_subclass:
                device_dict['usb_subclass_name'] = db_subclass[0]
                db_protocol = db_subclass[1].get(device_dict['usb_protocol'])
                if device_dict['usb_class'] == '03' and device_dict['usb_protocol'] != '00':
                    device_dict['usb_protocol_name'] = db_protocol
                    device_dict['name'] += ' (' + db_protocol + ')'

def update_device_dict_subsystem_hid(device):
    device_dict = devices_dict.get(device)
    device_dict['name'] = 'HID device '+device.split('/')[-1]

def update_device_dict_subsystem_net(device):
    device_dict = devices_dict.get(device)
    device_dict['name'] = 'Network interface '+device.split('/')[-1]

def update_device_dict_subsystem_scsi(device):
    device_dict = devices_dict.get(device)
    device_name = device.split('/')[-1]
    if device_name.startswith('host'):
        device_dict['name'] = 'SCSI host '+device_name[4:]
    elif device_name.startswith('target'):
        device_dict['name'] = 'SCSI bus ' + device_name[8] + ' target ' + device_name[10]
    else:
        device_dict['name'] = 'SCSI LUN ' + device_name[6]

def update_device_dict_subsystem_ata_port(device):
    device_dict = devices_dict.get(device)
    device_name = device.split('/')[-1]
    #device_dict['name'] = 'ATA port ' + device_name[3:]
    device_dict['name'] = 'ATA port node'

def update_device_dict_subsystem_drm(device):
    device_dict = devices_dict.get(device)
    device_dict['name'] = 'DRM'
    device_name = device.split('/')[-1]
    if device_name.startswith('card'):
        if device_name[4:].isdigit():
            device_dict['name'] += ' graphics card ' + device_name[4:] + ' driver primary node'
        else:
            device_dict['name'] += ' ' + device_name
    elif device_name.startswith('renderD'):
        device_dict['name'] += ' graphics card ' + str(int(device_name[7:])-128) + ' driver render node'
    else:
        device_dict['name'] += ' ' + device_name

def update_device_dict_subsystem_sound(device):
    device_dict = devices_dict.get(device)
    device_dict['name'] = 'Sound card'
    device_name = device.split('/')[-1]
    if device_name.startswith('pcm'):
        device_dict['name'] += ' device ' + device_name[6]
        if device_name[7] == 'p':
            device_dict['name'] += ' playback node'
        elif device_name[7] == 'c':
            device_dict['name'] += ' capture node'
    elif device_name.startswith('hw'):
        device_dict['name'] += ' device ' + device_name[5] + ' codec node'
    elif device_name.startswith('control'):
        device_dict['name'] += ' control node'
    elif device_name == 'dsp':
        device_dict['name'] += ' OSS compatibility playback&capture node'
    elif device_name == 'adsp':
        device_dict['name'] += ' OSS compatibility secondary playback&capture node'
    elif device_name == 'audio':
        device_dict['name'] += ' OSS compatibility playback&capture node, u-law encoding'
    elif device_name == 'mixer':
        device_dict['name'] += ' OSS compatibility control node'
    else:
        device_dict['name'] += ' ' + device_name[5:]

def update_device_dict_subsystem_pci_bus(device):
    device_dict = devices_dict.get(device)
    device_dict['name'] = 'PCI bus '+device[-2:]

def update_device_dict_subsystem_acpi(device):
    device_dict = devices_dict.get(device)
    device_name = device.split('/')[-1]
    device_dict['name'] = 'ACPI'
    device_id, device_number = device_name.split(':', 1)
    if device_id:
        if device_id.startswith('LNX') and device_id in acpi_names_dict:
            if device_id == 'LNXSYSTM':
                device_dict['name'] += ' root ' + device_number + ' (firmware namespace hierarchy representation)'
            else:
                device_dict['name'] += ' ' + acpi_names_dict[device_id] + ' object ' + device_number
        elif device_id == 'device':
            device_dict['name'] += ' HID-less device object ' + device_number
        else:
            device_dict['name'] += ' "' + device_id + '" device object ' + device_number
            device_id_prefix = device_id[:-4]
            device_id_number = device_id[-4:]
            print(device_id_prefix, device_id_number)
            db_vendor = pnp_db.get(device_id_prefix.lower())
            if db_vendor:
                    print(db_vendor)
                    db_device = db_vendor[1].get(device_id_number.lower())
                    if db_device:
                        print(db_device)
                        if device_id_prefix == 'PNP':
                            device_dict['name'] += ': ' + db_device
                        else:
                            device_dict['name'] += ': "' + db_vendor[0] + ' ' + db_device + '"'
    else:
        device_dict['name'] += ' ' + device_name[:-3] + ' ' + device_name[-2:]

def update_device_dict_subsystem_input(device):
    device_dict = devices_dict.get(device)
    device_name = device.split('/')[-1]
    device_dict['name'] = 'Input'
    if device_name.startswith('event'):
        device_dict['name'] += ' event interface node'
    elif device_name.startswith('mouse'):
        device_dict['name'] += ' mouse interface node'
    device_dict['name'] += ' ' + device_name[5:]
    if 'name' in os.listdir(device):
        input_name = get_file_contents(device, 'name')
        if input_name:
            device_dict['name'] += ': "' + input_name + '"'

def update_device_dict_subsystem_pnp(device):
    # PnP device: pnpPP:DD, PP=protocol number, DD=device number
    # drivers/pnp/core.c:
    # 	dev_set_name(&dev->dev, "%02x:%02x", dev->protocol->number, dev->number);
    # PnP root: pnpP, P=protocol number (first available one taken during protocol init)
    # drivers/pnp/core.c:
    # 	dev_set_name(&protocol->dev, "pnp%d", nodenum);
    # Seems there's no easy way to map protocol number to protocol name
    # PnP ACPI: if any child device has firmware_node pointing to acpi subsystem device, it's ACPI protocol
    device_dict = devices_dict.get(device)
    device_dict['name'] = 'PnP'
    device_name = device.split('/')[-1]
    pnp_protocol, pnp_number = device_name.split(':')
    #device_dict['name'] += ' protocol ' + pnp_protocol + ' device ' + pnp_number
    device_dict['name'] += ' device ' + pnp_number

# Device props tree items iterate functions yield tree items for adding to device props tree

import stat

db_numbers = {'char': {}, 'block': {}}
with open('/proc/devices') as f:
    for line in f:
        line = line[:-1]
        if line == 'Character devices:':
            scope = 'char'
        elif line == 'Block devices:':
            scope = 'block'
        else:
            number = line[:3].strip()
            if number.isdigit():
                db_numbers[scope][int(number)] = line[4:]

def iter_device_props_tree_items(device):
    device_dict = devices_dict.get(device)
    yield QTreeWidgetItem(None, ['Path: '+device])
    if 'subsystem' in device_dict:
        if 'iter_device_props_tree_items_subsystem_'+device_dict['subsystem'] in globals():
            for item in globals()['iter_device_props_tree_items_subsystem_'+device_dict['subsystem']](device):
                yield item
        else:
            yield QTreeWidgetItem(None, ['Subsystem: '+device_dict['subsystem']])
    if 'dev' in os.listdir(device):
        files_item = QTreeWidgetItem(None, ['Special device files'])
        numbers = get_file_contents(device, 'dev')
        if numbers in os.listdir('/sys/dev/block') and get_symlink_path('/sys/dev/block', numbers) == device:
            files_type = 'block'
            QTreeWidgetItem(files_item, ['Type: block'])
        else:
            files_type = 'char'
            QTreeWidgetItem(files_item, ['Type: character'])
        numbers_item = QTreeWidgetItem(files_item, ['Numbers: '+numbers])
        major, minor = numbers.split(':')
        QTreeWidgetItem(numbers_item, ['Major: '+major+' ('+db_numbers[files_type][int(major)]+')'])
        QTreeWidgetItem(numbers_item, ['Minor: '+minor])
        for root, subdirs, files in os.walk('/dev'):
            for file in files:
                #st_rdev = os.lstat('/dev/'+file).st_rdev
                stat_res = os.lstat(root+'/'+file)
                if os.major(stat_res.st_rdev) == int(major) and os.minor(stat_res.st_rdev) == int(minor) and (((files_type == 'block') and stat.S_ISBLK(stat_res[stat.ST_MODE])) or ((files_type == 'char') and stat.S_ISCHR(stat_res[stat.ST_MODE]))):
                    QTreeWidgetItem(files_item, ['Path: '+root+'/'+file])
        yield files_item
    if 'modalias' in os.listdir(device):
        yield QTreeWidgetItem(None, ['Kernel module alias: '+get_file_contents(device, 'modalias')])
    if 'driver' in os.listdir(device):
        yield QTreeWidgetItem(None, ['Driver: '+get_symlink_path(device, 'driver').split('/')[-1]+((' (registered by module '+get_symlink_path(device, 'driver/module').split('/')[-1]+')') if 'module' in os.listdir(device+'/driver') else '')])
    if 'firmware_node' in os.listdir(device):
        yield QTreeWidgetItem(None, ['Related firmware node: '+get_symlink_path(device, 'firmware_node')])
    if 'physical_node' in os.listdir(device):
        yield QTreeWidgetItem(None, ['Related physical node: '+get_symlink_path(device, 'physical_node')])

def iter_device_props_tree_items_subsystem_pci(device):
    device_dict = devices_dict.get(device)
    parent_item = None

    subsystem_item = QTreeWidgetItem(parent_item, ['Subsystem: PCI'])
    
    addr_item = QTreeWidgetItem(subsystem_item, ['Address: '+device[-12:]])
    QTreeWidgetItem(addr_item, ['Domain: '+device[-12:-8]])
    QTreeWidgetItem(addr_item, ['Bus: '+device[-7:-5]])
    QTreeWidgetItem(addr_item, ['Device: '+device[-4:-2]])
    QTreeWidgetItem(addr_item, ['Function: '+device[-1]])
    
    class_item = QTreeWidgetItem(subsystem_item, ['Class: '+device_dict['pci_class']])
    QTreeWidgetItem(class_item, ['Base: '+device_dict['pci_class_base']+(' ('+device_dict['pci_class_base_name']+')' if 'pci_class_base_name' in device_dict else '')])
    QTreeWidgetItem(class_item, ['Subclass: '+device_dict['pci_class_subclass']+(' ('+device_dict['pci_class_subclass_name']+')' if 'pci_class_subclass_name' in device_dict else '')])
    QTreeWidgetItem(class_item, ['Interface: '+device_dict['pci_class_interface']+(' ('+device_dict['pci_class_interface_name']+')' if 'pci_class_interface_name' in device_dict else '')])
    
    ids_item = QTreeWidgetItem(subsystem_item, ['IDs'])
    vendor = get_file_contents(device, 'vendor')
    device__pci_id = get_file_contents(device, 'device')
    subvendor = get_file_contents(device, 'subsystem_vendor')
    subdevice = get_file_contents(device, 'subsystem_device')
    vendor_db_entry = pci_db.get(vendor[2:])
    if vendor_db_entry:
        vendor += ' (' + vendor_db_entry[0] + ')'
        device_db_entry = vendor_db_entry[1].get(device__pci_id[2:])
        if device_db_entry:
            device__pci_id += ' (' + device_db_entry[0] + ')'
            subdevice_db_entry = device_db_entry[1].get(subvendor[2:]+' '+subdevice[2:])
            if subdevice_db_entry:
                subdevice += ' (' + subdevice_db_entry + ')'
    subvendor_db_entry = pci_db.get(subvendor[2:])
    if subvendor_db_entry:
        subvendor += ' (' + subvendor_db_entry[0] + ')'
    base_ids_item = QTreeWidgetItem(ids_item, ['Base'])
    QTreeWidgetItem(base_ids_item, ['Vendor: '+vendor])
    QTreeWidgetItem(base_ids_item, ['Device: '+device__pci_id])
    revision = get_file_contents(device, 'revision')
    QTreeWidgetItem(base_ids_item, ['Revision: '+revision])
    subsystem_ids_item = QTreeWidgetItem(ids_item, ['Subsystem'])
    QTreeWidgetItem(subsystem_ids_item, ['Vendor: '+subvendor])
    QTreeWidgetItem(subsystem_ids_item, ['Device: '+subdevice])
    
    resources_item = QTreeWidgetItem(subsystem_item, ['Resources'])
    resource_records = []
    with open(device+'/resource') as f:
        for line in f:
            resource_records.append(line[:-1].split(' '))
    for i in range(6):
        QTreeWidgetItem(resources_item, ['BAR '+str(i)+': '+str(resource_records[i])])
            
    
    yield subsystem_item


def iter_device_props_tree_items_subsystem_usb(device):
    device_dict = devices_dict.get(device)
    subsystem_item = QTreeWidgetItem(None, ['Subsystem: USB'])
    
    addr_item = QTreeWidgetItem(subsystem_item, ['Address: '+device.split('/')[-1]])
    QTreeWidgetItem(addr_item, ['Bus: '+device_dict['usb_bus']])
    if 'usb_port' in device_dict:
        QTreeWidgetItem(addr_item, ['Port: '+device_dict['usb_port']])
        if 'usb_config' in device_dict:
            QTreeWidgetItem(addr_item, ['Config: '+device_dict['usb_config']])
            if 'usb_iface' in device_dict:
                QTreeWidgetItem(addr_item, ['Interface: '+device_dict['usb_iface']])

    class_item = QTreeWidgetItem(subsystem_item, ['Class'])
    QTreeWidgetItem(class_item, ['Base: '+device_dict['usb_class']+(' ('+device_dict['usb_class_name']+')' if 'usb_class_name' in device_dict else '')])
    QTreeWidgetItem(class_item, ['Subclass: '+device_dict['usb_subclass']+(' ('+device_dict['usb_subclass_name']+')' if 'usb_subclass_name' in device_dict else '')])
    QTreeWidgetItem(class_item, ['Protocol: '+device_dict['usb_protocol']+(' ('+device_dict['usb_protocol_name']+')' if 'usb_protocol_name' in device_dict else '')])

    if not 'usb_iface' in device_dict:
        ids_item = QTreeWidgetItem(subsystem_item, ['IDs'])
        vendor = get_file_contents(device, 'idVendor')
        device__id = get_file_contents(device, 'idProduct')
        db_vendor = usb_db.get(vendor)
        db_device = db_vendor[1].get(device__id) if db_vendor else None
        QTreeWidgetItem(ids_item, ['Vendor: '+vendor+(' ('+db_vendor[0]+')' if db_vendor else '')])
        QTreeWidgetItem(ids_item, ['Device: '+device__id+(' ('+db_device[0]+')' if db_device else '')])
    
    yield subsystem_item

def iter_device_props_tree_items_subsystem_acpi(device):
    device_dict = devices_dict.get(device)
    subsystem_item = QTreeWidgetItem(None, ['Subsystem: ACPI'])
    
    QTreeWidgetItem(subsystem_item, ['Path: '+get_file_contents(device, 'path')])
    if 'hid' in os.listdir(device):
        hid = get_file_contents(device, 'hid')
        hid_vendor = hid[:3]
        hid_device = hid[3:]
        ids_item = QTreeWidgetItem(subsystem_item, ['ID: '+hid])
        db_vendor = pnp_db.get(hid_vendor.lower())
        db_device = db_vendor[1].get(hid_device.lower()) if db_vendor else None
        QTreeWidgetItem(ids_item, ['Vendor: '+hid_vendor+(' ('+db_vendor[0]+')' if db_vendor else '')])
        QTreeWidgetItem(ids_item, ['Device: '+hid_device+(' ('+db_device+')' if db_device else '')])
    if 'adr' in os.listdir(device):
        adr = get_file_contents(device, 'adr')
        QTreeWidgetItem(subsystem_item, ['Address: '+adr])
    
    yield subsystem_item

# libudev enumeration looks like a dead end
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

positions = [
    None,
    '/sys/devices/system',
    '/sys/devices/platform',
    '/sys/devices/LNXSYSTM:00',
    '/sys/devices/pnp0',
]

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
    elif path1 == '/devices/virtual' and 'name' in devices_dict['/sys'+path2]:
        return path2
    elif path2 == '/devices/virtual' and 'name' in devices_dict['/sys'+path1]:
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
    devices_dict[device_path] = {}
    update_device_dict(device_path)
    #return {'device_path': device_path}
    if not device_parent:
        device_parent = devices_model.invisibleRootItem()
    item = QStandardItem(devices_dict[device_path].get('name', device_path.split('/')[-1]))
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
    device_props_tree_widget.addTopLevelItems([item for item in iter_device_props_tree_items(device_path)])
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
