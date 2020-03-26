def update_dict(device_path, device_dict):
    device_name = device_path.split('/')[-1]
    if device_name.startswith('host'):
        device_dict['name'] = 'SCSI host '+device_name[4:]
    elif device_name.startswith('target'):
        device_dict['name'] = 'SCSI bus ' + device_name[8] + ' target ' + device_name[10]
    else:
        device_dict['name'] = 'SCSI LUN ' + device_name[6]
