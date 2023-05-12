from PyQt5.QtWidgets import QApplication

from DesktopClock import MainWindow

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    mWindow = MainWindow()
    mWindow.show()
    sys.exit(app.exec())