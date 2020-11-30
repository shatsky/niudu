def update_dict(device_path, device_dict):
    device_dict['label'] = 'ALSA sound card'
    if device_dict['node_name'].startswith('pcm'):
        device_dict['label'] += ' device ' + device_dict['node_name'][6]
        if device_dict['node_name'][7] == 'p':
            device_dict['label'] += ' playback node'
        elif device_dict['node_name'][7] == 'c':
            device_dict['label'] += ' capture node'
    elif device_dict['node_name'].startswith('hw'):
        device_dict['label'] += ' device ' + device_dict['node_name'][5] + ' codec node'
    elif device_dict['node_name'].startswith('control'):
        device_dict['label'] += ' control node'
    elif device_dict['node_name'] == 'dsp':
        device_dict['label'] += ' OSS compatibility playback&capture node'
    elif device_dict['node_name'] == 'adsp':
        device_dict['label'] += ' OSS compatibility secondary playback&capture node'
    elif device_dict['node_name'] == 'audio':
        device_dict['label'] += ' OSS compatibility playback&capture node, u-law encoding'
    elif device_dict['node_name'] == 'mixer':
        device_dict['label'] += ' OSS compatibility control node'
    else:
        device_dict['label'] += ' ' + device_dict['node_name'][4:]
