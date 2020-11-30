from ..util import get_file_contents

def update_dict(device_path, device_dict):
    device_dict['name'] = 'I2C adapter ' + '-'.join(device_path.split('/')[-1].split('-', 1)[1:]) + ': "' + get_file_contents(device_path, 'name') + '"'
