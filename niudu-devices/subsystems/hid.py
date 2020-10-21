def update_dict(device_path, device_dict):
    device_dict['name'] = 'HID device "'+device_path.split('/')[-1] + '"'
