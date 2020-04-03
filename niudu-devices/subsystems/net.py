from PySide2.QtWidgets import QTreeWidgetItem

from util import get_file_contents


def update_dict(device_path, device_dict):
    device_dict['name'] = 'Network interface "' + device_path.split('/')[-1] + '"'

def iter_props_tree_items(device_path, device_dict):
    parent_item = None

    subsystem_item = QTreeWidgetItem(parent_item, ['Subsystem: Network'])
    
    QTreeWidgetItem(subsystem_item, ['Address: '+get_file_contents(device_path, 'address')])
    QTreeWidgetItem(subsystem_item, ['Carrier: '+get_file_contents(device_path, 'carrier')])
    QTreeWidgetItem(subsystem_item, ['Speed: '+get_file_contents(device_path, 'speed')])
    
    yield subsystem_item
