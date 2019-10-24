import os
import sys
from PySide2 import QtGui, QtWidgets
import subprocess
import json


app = QtWidgets.QApplication(sys.argv)


class ScopeView(QtWidgets.QTreeView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = QtGui.QStandardItemModel()
        self.setModel(self.model)
        self.setHeaderHidden(True)
        self.expanded.connect(self.expanded__handler)
        self.add_items('(import <nixpkgs> {})', self.model.invisibleRootItem())

    def expanded__handler(self, index):
        parent_item = self.model.itemFromIndex(index)
        parent_item.removeRows(0, parent_item.rowCount())
        attr_path = ''
        parent_item_tmp = parent_item
        while parent_item_tmp is not None and parent_item_tmp is not self.model.invisibleRootItem():
            attr_path = '.' + parent_item_tmp.text() + attr_path
            parent_item_tmp = parent_item_tmp.parent()
        self.add_items('(import <nixpkgs> {})'+attr_path, parent_item)

    def add_items(self, set_expr, parent_item):
        #command = "nix-instantiate --strict --eval -E 'with rec {set_is_pkg = set: builtins.isAttrs set && builtins.hasAttr "type" set && builtins.getAttr "type" set == "derivation"; filter_pkgs = attr_set: builtins.filter (attr_name: (builtins.tryEval (set_is_pkg (builtins.getAttr attr_name attr_set))).value) (builtins.attrNames attr_set); }; filter_pkgs " + set_expr + "' --json"
        process = subprocess.Popen(["nix-instantiate", "--strict", "--eval", "-E", "with rec {set_is_pkg = set: builtins.isAttrs set && builtins.hasAttr \"type\" set && builtins.getAttr \"type\" set == \"derivation\"; filter_pkgs = attr_set: builtins.filter (attr_name: (builtins.tryEval (set_is_pkg (builtins.getAttr attr_name attr_set))).value) (builtins.attrNames attr_set); }; filter_pkgs "+set_expr, "--json"], stdout=subprocess.PIPE)
        (output, _) = process.communicate()
        _ = process.wait()
        for attr in json.loads(output):
            child_item = QtGui.QStandardItem(attr)
            parent_item.appendRow(child_item)
            child_item.appendRow(QtGui.QStandardItem(''))


scope_view = ScopeView()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        central_widget = scope_view
        self.setCentralWidget(central_widget)


window = MainWindow()
window.show()
app.exec_()
