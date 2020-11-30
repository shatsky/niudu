import unittest

from PySide2 import QtWidgets, QtGui


class MyTestCase(unittest.TestCase):

    def test_iterating_devices_props(self):
        from ..ui_devices_view import iter_devices
        from ..device import iter_props_tree_items, update_dict
        for device_path in iter_devices():
            device_dict = {}
            update_dict(device_path, device_dict)
            try:
                for item in iter_props_tree_items(device_path, device_dict):
                    pass
            except:
                print('Exception at device', device_path)
                raise
        return True


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    suite = unittest.TestLoader().loadTestsFromTestCase(MyTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
