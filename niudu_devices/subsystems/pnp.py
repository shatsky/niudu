import os

from ..util import get_label_suffix, get_symlink_path
from ..static import data_path


pnp_db = {}
with open(os.path.join(data_path, 'hwdata', 'pnp.ids')) as f:
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


def get_device_vendor_and_device_id(device_id):
    for i in range(len(device_id)):
        if device_id[i].isdigit():
            return device_id[:i], device_id[i:]
    return device_id, None


def get_device_vendor_and_device_name(device_id):
    device_id_prefix, device_id_number = get_device_vendor_and_device_id(device_id)
    db_vendor = pnp_db.get(device_id_prefix.lower())
    if db_vendor:
        db_device = db_vendor[1].get(device_id_number.lower())
        if db_device:
            return db_vendor[0], db_device
        return db_vendor[0], None
    return None, None


def update_dict(device_path, device_dict):
    # PnP device: pnpPP:DD, PP=protocol number, DD=device number
    # drivers/pnp/core.c:
    # 	dev_set_name(&dev->dev, "%02x:%02x", dev->protocol->number, dev->number);
    # PnP root: pnpP, P=protocol number (first available one taken during protocol init)
    # drivers/pnp/core.c:
    # 	dev_set_name(&protocol->dev, "pnp%d", nodenum);
    # Seems there's no easy way to map protocol number to protocol name
    # PnP ACPI: if any child device has firmware_node pointing to acpi subsystem device, it's ACPI protocol
    device_dict['label'] = 'PnP'
    pnp_protocol_and_num = device_dict['node_name'].split(':', 1)
    #device_dict['label'] += ' protocol ' + pnp_protocol + ' device ' + pnp_number
    if len(pnp_protocol_and_num) == 2 and pnp_protocol_and_num[0] == '00':
        device_dict['label'] += ' ACPI-discovered device' + get_label_suffix(pnp_protocol_and_num[1])
        if 'firmware_node' in device_dict['listdir']:
            firmware_node_path = get_symlink_path(device_path, 'firmware_node')
            firmware_node_name = firmware_node_path.split('/')[-1]
            firmware_node_hid_and_num = firmware_node_name.split(':', 1)
            device_vendor, device_name = get_device_vendor_and_device_name(firmware_node_hid_and_num[0])
            if device_vendor == 'Generic' and device_name is not None:
                device_dict['label'] += ': ' + device_name
        return
    device_dict['label'] += ' device' + get_label_suffix(device_dict['node_name'])
