import os
import sys
from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QTabWidget, QVBoxLayout, QComboBox, QLabel, QStatusBar
from PySide2.QtCore import QItemSelectionModel
from PySide2.QtGui import QIcon
from store_tree import StoreTreeView
from derivation_tree import DerivationView
from contents_tree import ContentsView


app = QApplication(sys.argv)
app.setWindowIcon(QIcon.fromTheme('nix-snowflake'))
app.setApplicationName('Nix Explorer')
status_bar = QStatusBar()

store_view = StoreTreeView(status_bar=status_bar)
store_model = store_view.model

derivation_view = DerivationView()
store_view.derivation_view = derivation_view

contents_view = ContentsView()
store_view.contents_view = contents_view
contents_view.model().store_view = store_view
contents_view.status_bar = status_bar

profile_dropdown = QComboBox()
profile_generation_dropdown = QComboBox()
for name in os.listdir('/nix/var/nix/profiles'):
    if name.startswith('system'):
        if len(name) == len('system'):
            pass
        else:
            #system_profile_number = name[len('system')+1:]
            system_profile_path = os.path.realpath('/nix/var/nix/profiles/'+name)
            profile_dropdown.addItem('/nix/var/nix/profiles/'+name) #+(' (current)' if os.path.realpath('/run/current-system') else ''))
for username in os.listdir('/nix/var/nix/profiles/per-user'):
    for name in os.listdir('/nix/var/nix/profiles/per-user/'+username):
        if name.startswith('profile'):
            if len(name) == len('profile'):
                pass
            else:
                #system_profile_number = name[len('profile')+1:]
                system_profile_path = os.path.realpath('/nix/var/nix/profiles/per-user/'+username+'/'+name)
                profile_dropdown.addItem('/nix/var/nix/profiles/per-user/'+username+'/'+name)


def profile_dropdown__activated(index):
    system_profile_path = os.path.realpath(profile_dropdown.currentText())
    store_model.removeRows(0, 1)
    print('adding root path', system_profile_path)
    item = store_view.add_store_path(os.path.realpath(system_profile_path))
    store_view.selectionModel().select(item.index(), QItemSelectionModel.ClearAndSelect)
profile_dropdown.activated.connect(profile_dropdown__activated)


store_view.add_store_path(os.path.realpath('/nix/var/nix/profiles/system'))

layout_base = QVBoxLayout()
layout_selectors = QHBoxLayout()
layout_selectors.addWidget(QLabel('Profile: '))
layout_selectors.addWidget(profile_dropdown)
layout = QHBoxLayout()
layout_base.addLayout(layout_selectors)
layout_base.addLayout(layout)
layout_base.addWidget(status_bar)
layout.addWidget(store_view)
right_tabbed = QTabWidget()
right_tabbed.addTab(derivation_view, 'Derivation')
right_tabbed.addTab(contents_view, 'Contents')
layout.addWidget(right_tabbed)
window = QWidget()
window.setLayout(layout_base)
window.show()
app.exec_()
