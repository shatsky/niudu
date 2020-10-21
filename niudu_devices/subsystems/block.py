import os
from PySide2.QtWidgets import QTreeWidgetItem

from ..util import get_file_contents


def get_mounts():
    mounts = []
    with open('/proc/mounts') as mounts_file:
        for line in mounts_file:
            mounts.append(line.split(' '))
    return mounts


def parse_mountinfo():
    mounts = []
    with open('/proc/self/mountinfo') as mountinfo_file:
        for line in mounts_file:
            mounts.append(line.split(' '))
    return mounts

def iter_props_tree_items(device_path, device_dict):
    subsystem_item = QTreeWidgetItem(None, ['Subsystem: block'])
    
    mount_points_item = QTreeWidgetItem(subsystem_item, ['Mount points'])
    major_minor = get_file_contents(device_path, 'dev')
    with open('/proc/self/mountinfo') as mountinfo_file:
        for mountinfo_line in mountinfo_file:
            mount_id, mount_parent_id, mount_major_minor, mount_root, mount_point, _ = mountinfo_line.split(' ', 5)
            if mount_major_minor == major_minor:
                QTreeWidgetItem(mount_points_item, [mount_point])
    
    major = int(major_minor.split(':')[0])
    if major == 1: # ramdisk
        type_item = QTreeWidgetItem(subsystem_item, ['Type: RAM disk'])
    if major == 7: # loop
        type_item = QTreeWidgetItem(subsystem_item, ['Type: loop'])
        QTreeWidgetItem(type_item, ['Backing file: '+get_file_contents(device_path, 'loop/backing_file')])
    elif major == 8: # sd
        type_item = QTreeWidgetItem(subsystem_item, ['Type: SCSI disk'])
    elif major == 9: # md
        type_item = QTreeWidgetItem(subsystem_item, ['Type: multiple device (software RAID)'])
        for item in []:
            QTreeWidgetItem(subsystem_item, ['Device:'])
    elif major == 252:
        type_item = QTreeWidgetItem(subsystem_item, ['Type: zRAM (compressed RAM disk)'])
    elif major == 254:
        type_item = QTreeWidgetItem(subsystem_item, ['Type: device mapper'])
    
    yield subsystem_item
