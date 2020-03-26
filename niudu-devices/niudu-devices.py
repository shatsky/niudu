import sys
from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QMenuBar
from PySide2.QtCore import Qt

# Must construct a QApplication before a QWidget
app = QApplication(sys.argv)

from ui_devices_view import devices_view, add_devices
from ui_device_props_view import device_props_tree_widget


# populate ui_devices_view
add_devices()

#top_menu = QMenuBar()
#device_menu = top_menu.addMenu('Device')
window = QWidget()
layout = QHBoxLayout()
#layout.addWidget(top_menu)
#layout.addWidget(treeWidget)
layout.addWidget(devices_view)
#layout.addWidget(tableWidget)
layout.addWidget(device_props_tree_widget)
window.setLayout(layout)
window.show()
app.exec_()
