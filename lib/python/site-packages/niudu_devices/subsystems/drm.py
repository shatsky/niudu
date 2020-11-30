def update_dict(device_path, device_dict):
        device_dict['name'] = 'DRM'
        device_name = device_path.split('/')[-1]
        if device_name.startswith('card'):
            if device_name[4:].isdigit():
                device_dict['name'] += ' graphics card ' + device_name[4:] + ' primary node'
            else:
                parts = device_name.split('-')
                if parts[1] == 'DP':
                    parts[1] = 'DisplayPort'
                device_dict['name'] += ' ' + '-'.join(parts[1:-1]) + ' connector ' + parts[-1]
        elif device_name.startswith('renderD'):
            device_dict['name'] += ' graphics card ' + str(int(device_name[7:])-128) + ' render node'
        else:
            device_dict['name'] += ' device "' + device_name + '"'
