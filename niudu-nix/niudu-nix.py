import os
import sys
from PySide2 import QtGui, QtWidgets
from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QTabWidget, QVBoxLayout, QComboBox, QLabel, QStatusBar
from PySide2.QtCore import QItemSelectionModel
from PySide2.QtGui import QIcon
from store_tree import StoreTreeView
from derivation_tree import DerivationView
from contents_tree import ContentsView
from summary import SummaryView


app = QApplication(sys.argv)
app.setWindowIcon(QIcon.fromTheme('nix-snowflake'))
app.setApplicationName('Nix Explorer')
status_bar = QStatusBar()

store_view = StoreTreeView(status_bar=status_bar)
store_model = store_view.model()

summary_view = SummaryView()
store_view.summary_view = summary_view

derivation_view = DerivationView()
store_view.derivation_view = derivation_view

contents_view = ContentsView()
store_view.contents_view = contents_view
contents_view.model().store_view = store_view
contents_view.status_bar = status_bar
contents_view.clipboard = app.clipboard()

store_view.add_store_path(os.path.realpath('/nix/var/nix/profiles/system'))

layout_base = QVBoxLayout()
layout = QHBoxLayout()
layout_base.addLayout(layout)
layout_base.addWidget(status_bar)
layout.addWidget(store_view)
right_tabbed = QTabWidget()
right_tabbed.addTab(summary_view, 'Summary')
right_tabbed.addTab(derivation_view, 'Derivation')
right_tabbed.addTab(contents_view, 'Contents')
layout.addWidget(right_tabbed)

profiles = []


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        menu_bar = self.menuBar()
        store_menu = QtWidgets.QMenu('Store', self)
        menu_bar.addMenu(store_menu)
        store_root_menu = store_menu.addMenu('Set root')
        store_root_profiles_action_group = QtWidgets.QActionGroup(store_root_menu, exclusive=True)
        for name in os.listdir('/nix/var/nix/profiles'):
            if name.startswith('system'):
                if len(name) == len('system'):
                    pass
                else:
                    #system_profile_number = name[len('system')+1:]
                    system_profile_path = os.path.realpath('/nix/var/nix/profiles/'+name)
                    action = QtWidgets.QAction('/nix/var/nix/profiles/'+name, store_root_menu, checkable=True) #+(' (current)' if os.path.realpath('/run/current-system') else ''))
                    profiles.append(system_profile_path)
                    store_root_menu.addAction(action)
                    store_root_profiles_action_group.addAction(action)
        for username in os.listdir('/nix/var/nix/profiles/per-user'):
            for name in os.listdir('/nix/var/nix/profiles/per-user/'+username):
                if name.startswith('profile'):
                    if len(name) == len('profile'):
                        pass
                    else:
                        #system_profile_number = name[len('profile')+1:]
                        system_profile_path = os.path.realpath('/nix/var/nix/profiles/per-user/'+username+'/'+name)
                        profiles.append(system_profile_path)
                        action = QtWidgets.QAction('/nix/var/nix/profiles/per-user/'+username+'/'+name, store_root_menu, checkable=True)
                        store_root_menu.addAction(action)
                        store_root_profiles_action_group.addAction(action)
        summary_view.profiles = profiles
        store_root_profiles_action_group.triggered.connect(self.store_root_profiles_action__handler)
        store_root_path_action = store_root_menu.addAction('Store path...')
        store_root_path_action.triggered.connect(self.store_root_path_action__handler)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout_base)
        self.setCentralWidget(central_widget)

    def store_root_profiles_action__handler(self, action):
        system_profile_path = os.path.realpath(action.text())
        store_model.removeRows(0, 1)
        item = store_view.add_store_path(os.path.realpath(system_profile_path))
        store_view.selectionModel().select(item.index(), QItemSelectionModel.ClearAndSelect)

    def store_root_path_action__handler(self, action):
        path, ok = QtWidgets.QInputDialog.getText(self, 'Set store view root', 'Enter store path:')
        if not ok:
            return
        store_model.removeRows(0, 1)
        path = os.path.realpath(path)
        path = '/'.join(path.split('/')[:4])
        if not path.startswith('/nix/store/'):
            return
        item = store_view.add_store_path(path)
        store_view.selectionModel().select(item.index(), QItemSelectionModel.ClearAndSelect)        


window = MainWindow()
window.show()
app.exec_()
