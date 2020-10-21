from ..util import get_label_suffix


def update_dict(device_path, device_dict):
    device_dict['label'] = 'HID raw interface'
    if device_dict['node_name'].startswith('hidraw'):
        device_dict['label'] += get_label_suffix(device_dict['node_name'][6:])
    else:
        device_dict['label'] += get_label_suffix(device_dict['node_name'])
