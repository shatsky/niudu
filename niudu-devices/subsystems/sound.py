def update_dict(device_path, device_dict):
    device_dict['name'] = 'Sound card'
    device_name = device_path.split('/')[-1]
    if device_name.startswith('pcm'):
        device_dict['name'] += ' device ' + device_name[6]
        if device_name[7] == 'p':
            device_dict['name'] += ' playback node'
        elif device_name[7] == 'c':
            device_dict['name'] += ' capture node'
    elif device_name.startswith('hw'):
        device_dict['name'] += ' device ' + device_name[5] + ' codec node'
    elif device_name.startswith('control'):
        device_dict['name'] += ' control node'
    elif device_name == 'dsp':
        device_dict['name'] += ' OSS compatibility playback&capture node'
    elif device_name == 'adsp':
        device_dict['name'] += ' OSS compatibility secondary playback&capture node'
    elif device_name == 'audio':
        device_dict['name'] += ' OSS compatibility playback&capture node, u-law encoding'
    elif device_name == 'mixer':
        device_dict['name'] += ' OSS compatibility control node'
    else:
        device_dict['name'] += ' ' + device_name[5:]
