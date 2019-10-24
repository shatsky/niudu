from PySide2.QtWidgets import QTreeView
from PySide2.QtGui import QStandardItem, QStandardItemModel, QFont
from store_tree import iter_command_output_lines


class SummaryView(QTreeView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = QStandardItemModel()
        self.setModel(self.model)
        self.setHeaderHidden(True)
        self.expanded.connect(self.expanded__handler)
        self.profiles = []

    def update(self, store_path):
        self.store_path = store_path
        self.model.removeRows(0, self.model.rowCount())
        self.model.invisibleRootItem().appendRow(QStandardItem('Store path: {0}'.format(store_path)))
        
        deps_item = QStandardItem('Dependencies')
        self.model.invisibleRootItem().appendRow(deps_item)
        
        direct_deps_item = QStandardItem('Direct')
        deps_item.appendRow(direct_deps_item)
        
        self.immediate_direct_deps_item = QStandardItem('Immediate')
        direct_deps_item.appendRow(self.immediate_direct_deps_item)
        dummy_item = QStandardItem('')
        self.immediate_direct_deps_item.appendRow(dummy_item)
        
        self.remote_direct_deps_item = QStandardItem('Remote')
        direct_deps_item.appendRow(self.remote_direct_deps_item)
        self.remote_direct_deps_item.appendRow(dummy_item)
        
        reverse_deps_item = QStandardItem('Reverse')
        deps_item.appendRow(reverse_deps_item)
        
        self.immediate_reverse_deps_item = QStandardItem('Immediate')
        reverse_deps_item.appendRow(self.immediate_reverse_deps_item)
        self.immediate_reverse_deps_item.appendRow(dummy_item)
        
        self.remote_reverse_deps_item = QStandardItem('Remote')
        reverse_deps_item.appendRow(self.remote_reverse_deps_item)
        self.remote_reverse_deps_item.appendRow(dummy_item)

    def expanded__handler(self, index):
        parent_item = self.model.itemFromIndex(index)
        if parent_item is self.immediate_direct_deps_item:
            parent_item.removeRows(0, parent_item.rowCount())
            self.immediate_direct_deps = []
            for dep in iter_command_output_lines('nix-store --query --references '+self.store_path):
                if dep == self.store_path:
                    continue
                self.immediate_direct_deps.append(dep)
                parent_item.appendRow(QStandardItem(dep))
        elif parent_item is self.immediate_reverse_deps_item:
            parent_item.removeRows(0, parent_item.rowCount())
            self.immediate_reverse_deps = []
            for dep in iter_command_output_lines('nix-store --query --referrers '+self.store_path):
                if dep == self.store_path:
                    continue
                self.immediate_reverse_deps.append(dep)
                item = QStandardItem(dep)
                if dep in self.profiles:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                parent_item.appendRow(item)
        elif parent_item is self.remote_direct_deps_item:
            parent_item.removeRows(0, parent_item.rowCount())
            for dep in iter_command_output_lines('nix-store --query --requisites '+self.store_path):
                if dep == self.store_path or dep in self.immediate_direct_deps:
                    continue
                self.immediate_direct_deps.append(dep)
                parent_item.appendRow(QStandardItem(dep))
        elif parent_item is self.remote_reverse_deps_item:
            parent_item.removeRows(0, parent_item.rowCount())
            for dep in iter_command_output_lines('nix-store --query --referrers-closure '+self.store_path):
                if dep == self.store_path or dep in self.immediate_reverse_deps:
                    continue
                self.immediate_reverse_deps.append(dep)
                item = QStandardItem(dep)
                if dep in self.profiles:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                parent_item.appendRow(item)
