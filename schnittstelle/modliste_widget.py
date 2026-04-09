import PyQt6
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidget


class ModItem(PyQt6.QtWidgets.QListWidgetItem):
    def __init__(
        self,
        name: str,
        selektiert: bool,
        ist_ueberfluessig: bool = False,
    ):
        super().__init__(name)
        self.setFlags(
            self.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
        )
        self.setCheckState(
            Qt.CheckState.Checked if selektiert else Qt.CheckState.Unchecked
        )
        if ist_ueberfluessig:
            self.setToolTip(
                "Überflüssiger JSON-Eintrag: Ordner fehlt oder ist bereits vertreten."
            )

class ModListe(QListWidget):
    reihenfolge_geaendert = PyQt6.QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAlternatingRowColors(True)
        self.setDropIndicatorShown(True)

        model = self.model()
        if model is not None:
            model.rowsMoved.connect(self._emit_reihenfolge_geaendert)

    def _emit_reihenfolge_geaendert(self, *args):
        self.reihenfolge_geaendert.emit()

    def dragMoveEvent(self, event):
        # Direktes Droppen "auf" einen Eintrag verhindern.
        # Erlaubt bleiben nur Positionen oberhalb/unterhalb.
        index = self.indexAt(event.position().toPoint())
        if index.isValid():
            rect = self.visualRect(index)
            pos_y = event.position().toPoint().y()
            obere_zone = rect.top() + 6
            untere_zone = rect.bottom() - 6

            if obere_zone < pos_y < untere_zone:
                event.ignore()
                return

        super().dragMoveEvent(event)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.reihenfolge_geaendert.emit()

    def ausgewaehlte_mods_in_reihenfolge(self) -> list[str]:
        mods = []
        for index in range(self.count()):
            item = self.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                mods.append(item.text())
        return mods

    def alle_mods_in_reihenfolge(self) -> list[tuple[str, bool]]:
        mods = []
        for index in range(self.count()):
            item = self.item(index)
            aktiviert = item.checkState() == Qt.CheckState.Checked
            mods.append((item.text(), aktiviert))
        return mods
