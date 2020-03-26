def update_dict(device_path, device_dict):
        device_dict['name'] = 'DRM'
        device_name = device_path.split('/')[-1]
        if device_name.startswith('card'):
            if device_name[4:].isdigit():
                device_dict['name'] += ' graphics card ' + device_name[4:] + ' driver primary node'
            else:
                device_dict['name'] += ' ' + device_name
        elif device_name.startswith('renderD'):
            device_dict['name'] += ' graphics card ' + str(int(device_name[7:])-128) + ' driver render node'
        else:
            device_dict['name'] += ' ' + device_name
