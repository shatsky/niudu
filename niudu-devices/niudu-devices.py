import sys
from PySide2 import QtWidgets

# "Must construct a QApplication before a QWidget"
# i. e. before importing stuff that instantiates QWidget
app = QtWidgets.QApplication(sys.argv)

from ui_devices_view import DevicesView
from ui_device_props_view import device_props_tree_widget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        
        menu_bar = self.menuBar()
        tree_menu = QtWidgets.QMenu('Tree', self)
        action = tree_menu.addAction('Reload')
        action.triggered.connect(self.reload__handler)
        action = tree_menu.addAction('Go to last added device')
        action.triggered.connect(self.last_added_device__handler)
        menu_bar.addMenu(tree_menu)

        devices_view = DevicesView()

        layout_base = QtWidgets.QHBoxLayout()
        layout_base.addWidget(devices_view)
        layout_base.addWidget(device_props_tree_widget)        
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout_base)
        self.setCentralWidget(central_widget)
        
        self.showMaximized()
    
    def reload__handler(self, action):
        devices_view.model.reload()
    
    def last_added_device__handler(self, action):
        from ui_devices_view import last_added_device, set_current_device
        set_current_device(last_added_device)
        


window = MainWindow()
app.exec_()
