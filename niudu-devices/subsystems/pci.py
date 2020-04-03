import os
from PySide2.QtWidgets import QTreeWidgetItem

from util import get_file_contents


db = {}
db_class = {}
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
                db_class[line[2:4]] = pci_class
            else:
                scope_class = False
                vendor = (line[6:-1], {})
                db[line[:4]] = vendor
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


def update_dict(device_path, device_dict):
        device_dict['name'] = 'PCI'
        device_dict['pci_device'] = device_path[-4:-2]
        device_dict['pci_function'] = device_path[-1]
        device_dict['pci_class'] = get_file_contents(device_path, 'class')
        device_dict['pci_class_base'] = '0x' + device_dict['pci_class'][2:4]
        device_dict['pci_class_subclass'] = '0x' + device_dict['pci_class'][4:6]
        device_dict['pci_class_interface'] = '0x' + device_dict['pci_class'][6:]
        db_base_class = db_class.get(device_dict['pci_class_base'][2:])
        if db_base_class:
            device_dict['pci_class_base_name'] = db_base_class[0]
            db_subclass = db_base_class[1].get(device_dict['pci_class_subclass'][2:])
            if db_subclass:
                device_dict['pci_class_subclass_name'] = db_subclass[0]
                db_interface = db_subclass[1].get(device_dict['pci_class_interface'][2:])
                if db_interface:
                    device_dict['pci_class_interface_name'] = db_interface
            else:
                device_dict['pci_class_subclass_name'] = None
        else:
            device_dict['pci_class_base_name'] = None
        device_dict['name'] += ' device ' + device_dict['pci_device']
        if device_dict['pci_function'] != '0':
            device_dict['name'] += ' function ' + device_dict['pci_function']
        if device_dict['pci_class_subclass_name'] is not None:
            device_dict['name'] += ': ' + device_dict['pci_class_subclass_name']
        elif device_dict['pci_class_base_name'] is not None:
            device_dict['name'] += ': ' + device_dict['pci_class_base_name']
        if device_dict['pci_class_base'] == '0x06' and device_dict['pci_class_subclass'] == '0x04':
            device_dict['name'] += ' (to bus ' + os.listdir(device_path+'/pci_bus')[0][-2:] + ')'


def iter_props_tree_items(device_path, device_dict):
    parent_item = None

    subsystem_item = QTreeWidgetItem(parent_item, ['Subsystem: PCI'])
    
    addr_item = QTreeWidgetItem(subsystem_item, ['Address: '+device_path[-12:]])
    QTreeWidgetItem(addr_item, ['Domain: '+device_path[-12:-8]])
    QTreeWidgetItem(addr_item, ['Bus: '+device_path[-7:-5]])
    QTreeWidgetItem(addr_item, ['Device: '+device_path[-4:-2]])
    QTreeWidgetItem(addr_item, ['Function: '+device_path[-1]])
    
    class_item = QTreeWidgetItem(subsystem_item, ['Class: '+device_dict['pci_class']])
    QTreeWidgetItem(class_item, ['Base: '+device_dict['pci_class_base']+(' ('+device_dict['pci_class_base_name']+')' if 'pci_class_base_name' in device_dict else '')])
    QTreeWidgetItem(class_item, ['Subclass: '+device_dict['pci_class_subclass']+(' ('+device_dict['pci_class_subclass_name']+')' if 'pci_class_subclass_name' in device_dict else '')])
    QTreeWidgetItem(class_item, ['Interface: '+device_dict['pci_class_interface']+(' ('+device_dict['pci_class_interface_name']+')' if 'pci_class_interface_name' in device_dict else '')])
    
    ids_item = QTreeWidgetItem(subsystem_item, ['IDs'])
    vendor = get_file_contents(device_path, 'vendor')
    device__pci_id = get_file_contents(device_path, 'device')
    subvendor = get_file_contents(device_path, 'subsystem_vendor')
    subdevice = get_file_contents(device_path, 'subsystem_device')
    vendor_db_entry = db.get(vendor[2:])
    if vendor_db_entry:
        vendor += ' (' + vendor_db_entry[0] + ')'
        device_db_entry = vendor_db_entry[1].get(device__pci_id[2:])
        if device_db_entry:
            device__pci_id += ' (' + device_db_entry[0] + ')'
            subdevice_db_entry = device_db_entry[1].get(subvendor[2:]+' '+subdevice[2:])
            if subdevice_db_entry:
                subdevice += ' (' + subdevice_db_entry + ')'
    subvendor_db_entry = db.get(subvendor[2:])
    if subvendor_db_entry:
        subvendor += ' (' + subvendor_db_entry[0] + ')'
    base_ids_item = QTreeWidgetItem(ids_item, ['Base'])
    QTreeWidgetItem(base_ids_item, ['Vendor: '+vendor])
    QTreeWidgetItem(base_ids_item, ['Device: '+device__pci_id])
    revision = get_file_contents(device_path, 'revision')
    QTreeWidgetItem(base_ids_item, ['Revision: '+revision])
    subsystem_ids_item = QTreeWidgetItem(ids_item, ['Subsystem'])
    QTreeWidgetItem(subsystem_ids_item, ['Vendor: '+subvendor])
    QTreeWidgetItem(subsystem_ids_item, ['Device: '+subdevice])
    
    resources_item = QTreeWidgetItem(subsystem_item, ['Resources'])
    resource_records = []
    with open(device_path+'/resource') as f:
        for line in f:
            resource_records.append(line[:-1].split(' '))
    for i in range(6):
        QTreeWidgetItem(resources_item, ['BAR '+str(i)+': '+str(resource_records[i])])
    
    yield subsystem_item
