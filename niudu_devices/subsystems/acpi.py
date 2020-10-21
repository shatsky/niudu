import os
from PySide2.QtWidgets import QTreeWidgetItem

from .pnp import pnp_db
from ..util import get_file_contents


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


def update_dict(device_path, device_dict):
    device_name = device_path.split('/')[-1]
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
            #print(device_id_prefix, device_id_number)
            db_vendor = pnp_db.get(device_id_prefix.lower())
            if db_vendor:
                #print(db_vendor)
                db_device = db_vendor[1].get(device_id_number.lower())
                if db_device:
                    #print(db_device)
                    if device_id_prefix == 'PNP':
                        device_dict['name'] += ': ' + db_device
                    else:
                        device_dict['name'] += ': "' + db_vendor[0] + ' ' + db_device + '"'
    else:
        device_dict['name'] += ' ' + device_name[:-3] + ' ' + device_name[-2:]


def iter_props_tree_items(device_path, device_dict):
    subsystem_item = QTreeWidgetItem(None, ['Subsystem: ACPI'])
    
    if 'path' in os.listdir(device_path):
        QTreeWidgetItem(subsystem_item, ['Path: '+get_file_contents(device_path, 'path')])
    if 'hid' in os.listdir(device_path):
        hid = get_file_contents(device_path, 'hid')
        hid_vendor = hid[:3]
        hid_device = hid[3:]
        ids_item = QTreeWidgetItem(subsystem_item, ['ID: '+hid])
        db_vendor = pnp_db.get(hid_vendor.lower())
        db_device = db_vendor[1].get(hid_device.lower()) if db_vendor else None
        QTreeWidgetItem(ids_item, ['Vendor: '+hid_vendor+(' ('+db_vendor[0]+')' if db_vendor else '')])
        QTreeWidgetItem(ids_item, ['Device: '+hid_device+(' ('+db_device+')' if db_device else '')])
    if 'adr' in os.listdir(device_path):
        adr = get_file_contents(device_path, 'adr')
        QTreeWidgetItem(subsystem_item, ['Address: '+adr])
    
    yield subsystem_item
