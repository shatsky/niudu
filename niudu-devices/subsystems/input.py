import os

from util import get_file_contents


def update_dict(device_path, device_dict):
    device_name = device_path.split('/')[-1]
    device_dict['name'] = 'Input'
    if device_name.startswith('event'):
        device_dict['name'] += ' event interface node'
    elif device_name.startswith('mouse'):
        device_dict['name'] += ' mouse interface node'
    device_dict['name'] += ' ' + device_name[5:]
    if 'name' in os.listdir(device_path):
        input_name = get_file_contents(device_path, 'name')
        if input_name:
            device_dict['name'] += ': "' + input_name + '"'
