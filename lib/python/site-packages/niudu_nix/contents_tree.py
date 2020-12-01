import os
from PySide2.QtWidgets import QTreeView, QFileSystemModel, QMenu
from PySide2.QtCore import Qt, QItemSelectionModel
from PySide2.QtGui import QBrush
import dbus


class ContentsModel(QFileSystemModel):

    def data(self, index, role):
        if index.isValid():
            if role == Qt.ForegroundRole:
                # Gray text color for symlinks pointing to out-of-current-store-path locations and files accessible via them
                current_store_path = self.store_view.model().itemFromIndex(self.store_view.selectionModel().selectedIndexes()[-1]).data()
                current_path = self.filePath(index)
                if not os.path.realpath(current_path).startswith(current_store_path):
                    return QBrush(Qt.gray)
        return super().data(index, role)


class ContentsView(QTreeView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model = ContentsModel()
        self.setModel(model)
        self.setMouseTracking(True)
        self.entered.connect(lambda index: self.status_bar.showMessage(self.model().filePath(index)))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.custom_contents_menu_requested__handler)

    def update(self, store_path):
        self.model().setRootPath(store_path)
        self.setRootIndex(self.model().index(store_path))

    def custom_contents_menu_requested__handler(self, point):
        contents_view = self
        contents_model = self.model()
        store_view = contents_model.store_view
        store_model = store_view.model()
        current_store_path = store_model.itemFromIndex(store_view.selectionModel().selectedIndexes()[-1]).data()
        current_path = contents_model.filePath(contents_view.selectionModel().selectedIndexes()[-1])
        context_menu = QMenu()
        action_open_in_file_manager = context_menu.addAction('Reveal in file manager')
        action_copy_full_path = context_menu.addAction('Copy full path')
        action_to_origin = None
        if not os.path.realpath(current_path).startswith(current_store_path) and os.path.realpath(current_path).startswith('/nix/store/'):
            action_to_origin = context_menu.addAction('Go to origin store path')
        chosen_action = context_menu.exec_(contents_view.mapToGlobal(point))
        if chosen_action == action_open_in_file_manager:
            bus = dbus.SessionBus()
            proxy_obj = bus.get_object("org.freedesktop.FileManager1", "/org/freedesktop/FileManager1")
            iface = dbus.Interface(proxy_obj, "org.freedesktop.FileManager1")
            iface.ShowItems([contents_model.filePath(contents_view.selectionModel().selectedIndexes()[-1])], "")
        elif chosen_action == action_copy_full_path:
            self.clipboard.setText(contents_model.filePath(contents_view.selectionModel().selectedIndexes()[-1]))
        elif chosen_action == action_to_origin:
            self.get_borrowed_file_store_path_item(contents_model.filePath(contents_view.selectionModel().selectedIndexes()[-1]))

    def get_borrowed_file_store_path_item(self, path):
        contents_view = self
        contents_model = self.model()
        store_view = contents_model.store_view
        store_model = store_view.model()
        # Files are borrowed via symlinks; packages owning destination objects are deps of ones containing symlinks
        # Follow chain of borrowing and select appropriate target store path item
        # Problem: it may not be loaded yet; solution: expand
        current_store_path_item = store_model.itemFromIndex(store_view.selectionModel().selectedIndexes()[-1])
        current_store_path = current_store_path_item.data()
        path_components = path[len(current_store_path)+1:].split('/')
        path_tmp = path[:len(current_store_path)]
        store_path_item_tmp = current_store_path_item
        for path_component in path_components:
            store_view.expand(store_path_item_tmp.index())
            path_tmp = path_tmp + '/' + path_component
            real_path_tmp = os.path.realpath(path_tmp)
            store_path_tmp = '/'.join(real_path_tmp.split('/')[:4])
            print(path_tmp, real_path_tmp, store_path_tmp)
            for i in range(store_path_item_tmp.rowCount()):
                print(i)
                if store_path_item_tmp.child(i) and store_path_item_tmp.child(i).data() == store_path_tmp:
                    store_path_item_tmp = store_path_item_tmp.child(i)
                    print(store_path_item_tmp.data())
                    break
        if not os.path.realpath(path).startswith(store_path_item_tmp.data()):
            raise
        # let currentChanged handler do the selection
        store_view.selectionModel().setCurrentIndex(store_path_item_tmp.index(), QItemSelectionModel.NoUpdate)
        store_view.scrollTo(store_path_item_tmp.index())
        #contents_view.expand(contents_model.index(os.path.realpath(path)))
        contents_view.selectionModel().select(contents_model.index(os.path.realpath(path)), QItemSelectionModel.ClearAndSelect)
        contents_view.scrollTo(contents_model.index(os.path.realpath(path)))

