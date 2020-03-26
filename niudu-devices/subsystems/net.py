def update_dict(device_path, device_dict):
    device_dict['name'] = 'Network interface '+device_path.split('/')[-1]
