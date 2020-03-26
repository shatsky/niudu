import os


pnp_db = {}
with open(os.path.dirname(os.path.abspath(__file__))+'/pnp.ids') as f:
    scope_class = False
    for line in f:
        if line.startswith('#'): continue
        line_len_full = len(line)
        line = line.lstrip('\t')
        indent = line_len_full - len(line)
        if indent == 0:
            vendor = (line[5:-1], {})
            pnp_db[line[:3]] = vendor
        elif indent == 1:
            vendor[1][line[:4]] = line[6:-1]
pnp_db['pnp'][1]['0a08'] = 'PCI Bus'


def update_dict(device_path, device_dict):
    # PnP device: pnpPP:DD, PP=protocol number, DD=device number
    # drivers/pnp/core.c:
    # 	dev_set_name(&dev->dev, "%02x:%02x", dev->protocol->number, dev->number);
    # PnP root: pnpP, P=protocol number (first available one taken during protocol init)
    # drivers/pnp/core.c:
    # 	dev_set_name(&protocol->dev, "pnp%d", nodenum);
    # Seems there's no easy way to map protocol number to protocol name
    # PnP ACPI: if any child device has firmware_node pointing to acpi subsystem device, it's ACPI protocol
    device_dict['name'] = 'PnP'
    device_name = device_path.split('/')[-1]
    pnp_protocol, pnp_number = device_name.split(':')
    #device_dict['name'] += ' protocol ' + pnp_protocol + ' device ' + pnp_number
    device_dict['name'] += ' device ' + pnp_number
