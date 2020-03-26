import os
import stat
from PySide2.QtWidgets import QTreeWidgetItem

import subsystems
from util import get_symlink_path, get_file_contents


# special device files min&maj numbers dicts
db_numbers = {'char': {}, 'block': {}}
with open('/proc/devices') as f:
    for line in f:
        line = line[:-1]
        if line == 'Character devices:':
            scope = 'char'
        elif line == 'Block devices:':
            scope = 'block'
        else:
            number = line[:3].strip()
            if number.isdigit():
                db_numbers[scope][int(number)] = line[4:]


# get data for displaying device in devices tree widget and anything else that can be fetched together with it and can be needed later for displaying device details
def update_dict(device_path, device_dict):
    if 'subsystem' in os.listdir(device_path):
        subsystem_name = get_symlink_path(device_path, 'subsystem').split('/')[-1]
        device_dict['subsystem'] = subsystem_name
        if subsystem_name in dir(subsystems):
            subsystem_module = getattr(subsystems, subsystem_name)
            if hasattr(subsystem_module, 'update_dict'):
                device = getattr(subsystems, subsystem_name).update_dict(device_path, device_dict)
                return
        else:
            device_dict['subsystem'] = subsystem_name
    device_name = device_path.split('/')[-1]
    if device_name.startswith('ep_'):
        device_dict['name'] = 'USB endpoint '+device_name[3:]
    elif device_name.startswith('pci'):
        device_dict['name'] = 'PCI domain ' + device_name[3:7] + ' host bridge (to bus ' + device_name[8:10] + ') root'
    elif device_path.startswith('/sys/devices/pnp') and device_path[len('/sys/devices/pnp'):].isdigit():
        pnp_protocol = device_path[len('/sys/devices/pnp'):]
        if '00:00' in os.listdir(device_path) and 'firmware_node' in os.listdir(device_path+'/00:00') and get_symlink_path(device_path+'/00:00/firmware_node', 'subsystem').endswith('/acpi'):
            pnp_protocol = 'ACPI'
        device_dict['name'] = 'PnP'
        if pnp_protocol == 'ACPI':
            device_dict['name'] += ' root for ACPI (devices known exclusively from ACPI)'
        else:
            pass
    elif device_path.startswith('/sys/devices/platform'):
        if device_path == '/sys/devices/platform':
            device_dict['name'] = 'Platform root (devices known from this system\'s platform architecture)'
        else:
            device_dict['name'] = device_name
    elif device_path.startswith('/sys/devices/system'):
        if device_path == '/sys/devices/system':
            device_dict['name'] = 'System devices (devices and abstractions available on any supported platform)'
        elif device_path == '/sys/devices/system/node':
            device_dict['name'] = 'NUMA root'
        else:
            device_dict['name'] = device_name
    elif device_path.startswith('/sys/devices/virtual'):
        if device_path == '/sys/devices/virtual':
            device_dict['name'] = 'Virtual devices'
        else:
            device_dict['name'] = device_name
    elif device_name.startswith('ata') and 'ata_port' in os.listdir(device_path) and device_name in os.listdir(device_path+'/ata_port') and get_symlink_path(device_path+'/ata_port/'+device_name, 'subsystem').endswith('ata_port'):
        device_dict['name'] = 'ATA port ' + device_name[3:]
    elif device_name.startswith('link') and 'ata_link' in os.listdir(device_path) and device_name in os.listdir(device_path+'/ata_link') and get_symlink_path(device_path+'/ata_link/'+device_name, 'subsystem').endswith('ata_link'):
        device_dict['name'] = 'ATA link ' + device_name[4:]
    else:
        device_dict['name'] = device_name


# yield tree items for device properties tree widget
def iter_props_tree_items(device_path, device_dict):
    yield QTreeWidgetItem(None, ['Path: '+device_path])
    if device_dict.get('subsystem') is not None:
        if device_dict['subsystem'] in dir(subsystems):
            subsystem_module = getattr(subsystems, device_dict['subsystem'])
            if hasattr(subsystem_module, 'iter_props_tree_items'):
                for item in subsystem_module.iter_props_tree_items(device_path, device_dict):
                    yield item
            else:
                yield QTreeWidgetItem(None, ['Subsystem: '+device_dict['subsystem']])
        else:
            yield QTreeWidgetItem(None, ['Subsystem: '+device_dict['subsystem']])
    if 'dev' in os.listdir(device_path):
        files_item = QTreeWidgetItem(None, ['Special device files'])
        numbers = get_file_contents(device_path, 'dev')
        if numbers in os.listdir('/sys/dev/block') and get_symlink_path('/sys/dev/block', numbers) == device_path:
            files_type = 'block'
            QTreeWidgetItem(files_item, ['Type: block'])
        else:
            files_type = 'char'
            QTreeWidgetItem(files_item, ['Type: character'])
        numbers_item = QTreeWidgetItem(files_item, ['Numbers: '+numbers])
        major, minor = numbers.split(':')
        QTreeWidgetItem(numbers_item, ['Major: '+major+' ('+db_numbers[files_type][int(major)]+')'])
        QTreeWidgetItem(numbers_item, ['Minor: '+minor])
        for root, subdirs, files in os.walk('/dev'):
            for file in files:
                #st_rdev = os.lstat('/dev/'+file).st_rdev
                stat_res = os.lstat(root+'/'+file)
                if os.major(stat_res.st_rdev) == int(major) and os.minor(stat_res.st_rdev) == int(minor) and (((files_type == 'block') and stat.S_ISBLK(stat_res[stat.ST_MODE])) or ((files_type == 'char') and stat.S_ISCHR(stat_res[stat.ST_MODE]))):
                    QTreeWidgetItem(files_item, ['Path: '+root+'/'+file])
        yield files_item
    if 'modalias' in os.listdir(device_path):
        yield QTreeWidgetItem(None, ['Kernel module alias: '+get_file_contents(device_path, 'modalias')])
    if 'driver' in os.listdir(device_path):
        yield QTreeWidgetItem(None, ['Driver: '+get_symlink_path(device_path, 'driver').split('/')[-1]+((' (registered by module '+get_symlink_path(device_path, 'driver/module').split('/')[-1]+')') if 'module' in os.listdir(device_path+'/driver') else '')])
    if 'firmware_node' in os.listdir(device_path):
        yield QTreeWidgetItem(None, ['Related firmware node: '+get_symlink_path(device_path, 'firmware_node')])
    if 'physical_node' in os.listdir(device_path):
        yield QTreeWidgetItem(None, ['Related physical node: '+get_symlink_path(device_path, 'physical_node')])
