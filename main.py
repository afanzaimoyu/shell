#! /usr/bin/python3
#  -*-    coding: utf-8   -*-
# Author    :       摸鱼呀阿凡
# Contact   :       f2095522823@gmail.com

from PyQt5 import QtWidgets
from src.shell_ui import Mainwindow

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = Mainwindow()
    window.show()
    sys.exit(app.exec_())
