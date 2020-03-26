def update_dict(device_path, device_dict):
    device_dict['name'] = 'PCI bus '+device_path[-2:]
