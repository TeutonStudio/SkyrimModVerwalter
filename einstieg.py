import sys

from PyQt6.QtWidgets import QApplication

from kern.umgebung_verwalter import Umgebung
from schnittstelle.verwalter_widget import VerwalterFenster


def main() -> int:
    app = QApplication(sys.argv)
    fenster = VerwalterFenster(Umgebung())
    fenster.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
