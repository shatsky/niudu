import os
from PySide2.QtWidgets import QTreeWidgetItem

from ..util import get_file_contents
from ..static import data_path


# http://www.linux-usb.org/usb.ids
usb_db = {}
usb_db_class = {}
with open(os.path.join(data_path, 'hwdata', 'usb.ids'), errors='replace') as f:
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


def update_dict(device_path, device_dict):
    # http://www.linux-usb.org/FAQ.html
    device_dict['name'] = 'USB'
    addr = device_path.split('/')[-1]
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
                # TODO ADB
                # adb/transport_usb.c:is_adb_interface()
                # adb/usb_vendors.c
                # if parent device has relevant vendor id
                #  and interface class is 0xff
                #  and interface subclass is 0x42
                #  and interface protocol is 0x01
                ## MTP
                # https://github.com/libmtp/libmtp/blob/master/util/mtp-probe.c
            else:
                device_dict['usb_iface'] = None
        else:
            device_dict['name'] += ' device on port ' + device_dict['usb_port'].split('.')[-1]
            device_dict['usb_class'] = get_file_contents(device_path, 'bDeviceClass')
            device_dict['usb_iface'] = None
            device_dict['usb_kernel_seq_devnum'] = get_file_contents(device_path, 'devnum')
            device_dict['icon'] = 'usb_device'
    else:
        device_dict['name'] += ' bus'
        if device_dict['usb_bus'].startswith('usb'):
            device_dict['name'] += ' ' + device_dict['usb_bus'][3:]
        else:
            device_dict['name'] += ' ' + device_dict['usb_bus']
        device_dict['usb_iface'] = None

    if device_dict['usb_iface'] is None:
        device_dict['usb_class'] = get_file_contents(device_path, 'bDeviceClass')
        device_dict['usb_subclass'] = get_file_contents(device_path, 'bDeviceSubClass')
        device_dict['usb_protocol'] = get_file_contents(device_path, 'bDeviceProtocol')
    else:
        device_dict['usb_class'] = get_file_contents(device_path, 'bInterfaceClass')
        device_dict['usb_subclass'] = get_file_contents(device_path, 'bInterfaceSubClass')
        device_dict['usb_protocol'] = get_file_contents(device_path, 'bInterfaceProtocol')

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


def iter_props_tree_items(device_path, device_dict):
    subsystem_item = QTreeWidgetItem(None, ['Subsystem: USB'])
    
    addr_item = QTreeWidgetItem(subsystem_item, ['Address: '+device_path.split('/')[-1]])
    QTreeWidgetItem(addr_item, ['Bus: '+device_dict['usb_bus']])
    if 'usb_port' in device_dict:
        QTreeWidgetItem(addr_item, ['Port path: '+device_dict['usb_port']])
        if 'usb_config' in device_dict:
            QTreeWidgetItem(addr_item, ['Config: '+device_dict['usb_config']])
            if 'usb_iface' in device_dict:
                QTreeWidgetItem(addr_item, ['Interface: '+device_dict['usb_iface']])

    if 'usb_kernel_seq_devnum' in device_dict:
        QTreeWidgetItem(subsystem_item, ['Sequential number: '+device_dict['usb_kernel_seq_devnum']])

    class_item = QTreeWidgetItem(subsystem_item, ['Class'])
    QTreeWidgetItem(class_item, ['Base: '+device_dict['usb_class']+(' ('+device_dict['usb_class_name']+')' if 'usb_class_name' in device_dict else '')])
    QTreeWidgetItem(class_item, ['Subclass: '+device_dict['usb_subclass']+(' ('+device_dict['usb_subclass_name']+')' if 'usb_subclass_name' in device_dict else '')])
    QTreeWidgetItem(class_item, ['Protocol: '+device_dict['usb_protocol']+(' ('+device_dict['usb_protocol_name']+')' if 'usb_protocol_name' in device_dict else '')])

    if not device_dict.get('usb_iface'):
        ids_item = QTreeWidgetItem(subsystem_item, ['IDs'])
        vendor = get_file_contents(device_path, 'idVendor')
        device__id = get_file_contents(device_path, 'idProduct')
        db_vendor = usb_db.get(vendor)
        db_device = db_vendor[1].get(device__id) if db_vendor else None
        QTreeWidgetItem(ids_item, ['Vendor: '+vendor+(' ('+db_vendor[0]+')' if db_vendor else '')])
        QTreeWidgetItem(ids_item, ['Device: '+device__id+(' ('+db_device[0]+')' if db_device else '')])
    
    yield subsystem_item
