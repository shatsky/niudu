from util import get_file_contents, get_label_suffix


def update_dict(device_path, device_dict):
    device_dict['label'] = 'Input'
    if device_dict['node_name'].startswith('input'):
        device_dict['label'] += ' device'
        device_dict['label'] += get_label_suffix(device_dict['node_name'][5:])
    elif device_dict['node_name'].startswith('event'):
        device_dict['label'] += ' event interface'
        device_dict['label'] += get_label_suffix(device_dict['node_name'][5:])
    elif device_dict['node_name'].startswith('mouse'):
        device_dict['label'] += ' legacy mouse interface'
        device_dict['label'] += get_label_suffix(device_dict['node_name'][5:])
    elif device_dict['node_name'].startswith('js'):
        device_dict['label'] += ' legacy joystick interface'
        device_dict['label'] += get_label_suffix(device_dict['node_name'][2:])
    else:
        device_dict['label'] += ' interface'
        device_dict['label'] += get_label_suffix(device_dict['node_name'])
    if 'name' in device_dict['listdir']:
        input_name = get_file_contents(device_path, 'name')
        if input_name:
            device_dict['label'] += ': "' + input_name + '"'
