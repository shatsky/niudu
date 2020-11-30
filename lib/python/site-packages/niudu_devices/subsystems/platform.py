from .pnp import get_device_vendor_and_device_name
from ..util import get_label_suffix, get_symlink_path


def update_dict(device_path, device_dict):
    device_dict['label'] = 'Platform'
    if device_dict['node_name'] == 'alarmtimer':
        device_dict['label'] += ' alarm timer'
    elif device_dict['node_name'].startswith('coretemp.'):
        device_dict['label'] += ' digital temperature sensor of Intel CPU'
        device_dict['label'] += get_label_suffix(device_dict['node_name'][len('coretemp.'):])
    elif device_dict['node_name'].startswith('intel_rapl_msr.'):
        device_dict['label'] += ' RAPL MSR interface of Intel CPU'
        device_dict['label'] += get_label_suffix(device_dict['node_name'][len('intel_rapl_msr.'):])
    elif device_dict['node_name'] == 'microcode':
        device_dict['label'] += ' microcode access node'
    elif device_dict['node_name'] == 'pcspkr':
        device_dict['label'] += ' PC speaker'
    elif device_dict['node_name'].startswith('platform-framebuffer.'):
        device_dict['label'] += ' framebuffer'
        device_dict['label'] += get_label_suffix(device_dict['node_name'][len('platform-framebuffer.'):])
    elif device_dict['node_name'] == 'reg-dummy':
        device_dict['label'] += ' dummy regulators'
    elif device_dict['node_name'] == 'serial8250':
        device_dict['label'] += ' 8250/16550-type serial ports'
    else:
        device_dict['label'] += ' device'
        if 'firmware_node' in device_dict['listdir']:
            firmware_node_path = get_symlink_path(device_path, 'firmware_node')
            firmware_node_name = firmware_node_path.split('/')[-1]
            if device_dict['node_name'] == firmware_node_name and get_symlink_path(firmware_node_path, 'subsystem').split('/')[-1] == 'acpi':
                firmware_node_name_and_num = firmware_node_name.split(':', 1)
                if len(firmware_node_name_and_num) == 2:
                    device_dict['label'] += ' described by ACPI "' + firmware_node_name_and_num[0] + '" object' + get_label_suffix(firmware_node_name_and_num[1])
                    device_vendor, device_name = get_device_vendor_and_device_name(firmware_node_name_and_num[0])
                    if device_vendor == 'Generic' and device_name is not None:
                        device_dict['label'] += ': ' + device_name
                    return
        device_dict['label'] += get_label_suffix(device_dict['node_name'])
