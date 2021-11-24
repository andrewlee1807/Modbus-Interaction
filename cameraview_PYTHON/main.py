from mainwindow_ui import MainWindowClass
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
mainwindow = MainWindowClass()
mainwindow.show()
sys.exit(app.exec_())