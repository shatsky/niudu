import subprocess
from PySide2.QtWidgets import QErrorMessage
import libvirt


def attach_to_vm(device, vm):
    if 'subsystem' in device and device['subsystem'] == 'usb' and 'usb_kernel_seq_devnum' in device:
        xml = '''<hostdev mode='subsystem' type='usb' managed='yes'>
  <source>
    <address bus=\''''+device['usb_bus']+'''\' device=\''''+device['usb_kernel_seq_devnum']+'''\'/>
  </source>
</hostdev>'''
        try:
            libvirt_conn = libvirt.open('qemu:///system')
            domain = libvirt_conn.lookupByName(vm)
            domain.attachDevice(xml)
        except libvirt.libvirtError as e:
            error_message = QErrorMessage()
            error_message.showMessage(str(e))
            error_message.exec()
        
def add_device_actions(device, menu, tuples):
    if 'subsystem' in device and device['subsystem'] == 'usb' and 'usb_kernel_seq_devnum' in device:
        try:
            libvirt_conn = libvirt.open('qemu:///system')
        except libvirt.libvirtError:
            # TODO log
            return
        vm_submenu = menu.addMenu('Attach to VM')
        # This function, having hotplug semantics, is only allowed on an active domain
        # https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainState
        running_vms = [ domain.name() for domain in libvirt_conn.listAllDomains() if domain.state()[0] == libvirt.VIR_DOMAIN_RUNNING ]
        if not running_vms:
            action = vm_submenu.addAction('No running VMs')
            action.setEnabled(False)
            return
        for vm in running_vms:
            action = vm_submenu.addAction(vm)
            tuples.append((action, attach_to_vm, [vm], {}))
