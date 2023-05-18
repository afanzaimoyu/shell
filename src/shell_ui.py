#! /usr/bin/python3
# @File     :       shell_ui.py
#  -*-    coding: utf-8   -*-
# Author    :       摸鱼呀阿凡
# Contact   :       f2095522823@gmail.com
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QMenu, QFileDialog, QInputDialog
from src.shell import Ui_Form
from connection import ConnectionManager
from saved_info import SavedInfoManager
from logger import get


class WorkerSignals(QObject):
    finished = pyqtSignal(object)


class Worker(QRunnable):
    def __init__(self, command, connection_manager, *args):
        super().__init__()
        self.command = command
        self.connection_manager = connection_manager
        self.args = args
        self.signals = WorkerSignals()

    def run(self):
        result = None
        if self.command == 'shell':
            result = self.connection_manager.execute_remote_command(*self.args)
        elif self.command == 'save':
            # 保存文件内容到远程服务器
            result = self.connection_manager.save_file_content(*self.args)
        elif self.command == 'put':
            result = self.connection_manager.upload_file(*self.args)
        elif self.command == 'push':
            result = self.connection_manager.download_file(*self.args)
        self.signals.finished.emit(result)


class Mainwindow(Ui_Form, QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        """
        主窗口类，用于管理界面和操作逻辑。

        Args:
            parent: 父窗口对象
        """
        super(Mainwindow, self).__init__(parent)
        self.ui_start = Ui_Form()
        self.ui_start.setupUi(self)
        self.log = get()
        self.init_ui()

    def init_ui(self):
        """
        初始化界面，设置初始状态和绑定事件处理函数。
        """
        self.user_text = ""
        self.pwd_text = ""
        self.save_server_text = ""
        self.is_editing = False
        self.connected = False
        self.file_name = None

        self.ui_start.login_btn.clicked.connect(self.lianjie)
        self.ui_start.exit_btn.clicked.connect(self.tuichu)
        self.ui_start.listWidget.itemClicked.connect(self.show_info)
        self.ui_start.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui_start.listWidget.customContextMenuRequested.connect(self.show_context_menu)
        self.ui_start.command.returnPressed.connect(self.execute_command)
        self.ui_start.ok.accepted.connect(self.execute_command)
        self.ui_start.ok.rejected.connect(self.clear_command)

        self.connection_manager = ConnectionManager(self.log)
        self.saved_info_manager = SavedInfoManager(self.log)
        self.load_saved_info()  # 加载数据库中的连接信息

        # 绑定上传和下载按钮的点击事件
        self.ui_start.uploadButton.clicked.connect(self.upload_file)
        self.ui_start.downloadButton.clicked.connect(self.download_file)

        # 编辑和保存按钮
        self.ui_start.editButton.clicked.connect(self.show_file_content)
        self.ui_start.saveButton.clicked.connect(self.save_file_content)

        self.ui_start.textEdit.hide()  # 隐藏编辑器页面
        self.ui_start.saveButton.hide()  # 隐藏保存按钮

    def show_file_content(self):
        if not self.connected:
            QMessageBox.warning(self, "错误", "请先连接！", QMessageBox.Ok)
            return
        if not self.is_editing:
            self.to_edit()
        else:
            self.is_editing = False
            self.ui_start.textEdit.clear()
            self.ui_start.textEdit.hide()
            self.ui_start.editButton.setText("编辑")

    def to_edit(self):
        """
        编辑按钮点击事件，允许用户选择远程服务器上的文件并显示文件内容。
        """
        current_remote_path = self.connection_manager.current_directory  # 获取当前远程路径

        # 显示当前路径的文件供选择
        files_in_path = self.connection_manager.list_files(current_remote_path)
        file, ok = QtWidgets.QInputDialog.getItem(self, "选择文件", "选择要编辑的文件", files_in_path,
                                                  editable=False)
        if file and ok:
            self.file_name = file
            content = self.connection_manager.get_file_content(file)
            if content:
                self.is_editing = True
                self.ui_start.textEdit.show()
                self.ui_start.textEdit.setText(content)
                self.ui_start.saveButton.show()
                self.ui_start.editButton.setText("取消")
            else:
                try:
                    reply = QMessageBox.question(
                        self, "错误",
                        f"无法获取文件内容，是否强制打开",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.ui_start.editButton.setText("取消")
                        self.is_editing = True
                        self.ui_start.textEdit.show()
                        self.ui_start.textEdit.setText(content)
                        self.ui_start.saveButton.show()
                    else:
                        QMessageBox.warning(self, "错误", "无法强制打开文件！", QMessageBox.Ok)
                except Exception as e:
                    self.log.error(f"打开文件出现错误: {e}")

    def save_file_content(self):
        """
        保存按钮点击事件，将编辑后的文件内容保存到远程服务器上。
        """

        file_content = self.ui_start.textEdit.toPlainText()

        def save_the_pop_up(result):
            if result:
                QMessageBox.information(self, "成功!", "文件保存成功", QMessageBox.Ok)
            else:
                QMessageBox.warning(self, "错误", "文件保存失败！", QMessageBox.Ok)
            self.ui_start.textEdit.clear()
            self.ui_start.editButton.setText("编辑")
            self.is_editing = False
            self.ui_start.textEdit.hide()
            self.ui_start.saveButton.hide()

        task = Worker("save", self.connection_manager, file_content, self.file_name)
        task.signals.finished.connect(save_the_pop_up)  # 连接信号和槽函数
        QThreadPool.globalInstance().start(task)

    def upload_file(self):
        """
        上传文件到远程服务器
        """
        if not self.connected:
            QMessageBox.warning(self, "错误", "请先连接！", QMessageBox.Ok)
            return

        local_file, _ = QFileDialog.getOpenFileName(self, "选择要上传的文件")
        if local_file:
            current_remote_path = self.connection_manager.current_directory  # 获取当前远程路径
            remote_file, _ = QInputDialog.getText(self, "远程文件路径", "请输入远程服务器上保存文件的路径",
                                                  text=current_remote_path)
            if remote_file:
                def upload_back(result):
                    if result:
                        QMessageBox.information(self, "成功!", "文件保存成功", QMessageBox.Ok)
                    else:
                        QMessageBox.warning(self, "错误", "文件保存失败！", QMessageBox.Ok)

                task = Worker("put", self.connection_manager, local_file, remote_file)
                task.signals.finished.connect(upload_back)  # 连接信号和槽函数
                QThreadPool.globalInstance().start(task)

    def download_file(self):
        """
        从远程服务器下载文件
        """
        if not self.connected:
            QMessageBox.warning(self, "错误", "请先连接！", QMessageBox.Ok)
            return

        current_remote_path = self.connection_manager.current_directory  # 获取当前远程路径

        # 显示当前路径的文件供选择
        files_in_path = self.connection_manager.list_files(current_remote_path)
        remote_file, ok = QtWidgets.QInputDialog.getItem(self, "选择文件", "选择要下载的文件", files_in_path,
                                                         editable=False)
        if remote_file and ok:
            local_file, _ = QFileDialog.getSaveFileName(self, "保存文件", remote_file)
            if local_file:
                def download_back(result):
                    if result:
                        QMessageBox.information(self, "成功!", "文件下载成功", QMessageBox.Ok)
                    else:
                        QMessageBox.warning(self, "错误", "文件下载失败！", QMessageBox.Ok)

                task = Worker("push", self.connection_manager, remote_file, local_file)
                task.signals.finished.connect(download_back)  # 连接信号和槽函数
                QThreadPool.globalInstance().start(task)

    def execute_command(self):
        """
         执行命令，将命令发送到远程服务器执行，并显示执行结果。
        """
        command = self.ui_start.command.text()
        self.ui_start.command.clear()

        # result = self.connection_manager.execute_remote_command(command)
        def update_result(result):
            if result:
                if result == 'clear':
                    self.ui_start.show.clear()
                    result = ''
                self.ui_start.show.append(result)

        task = Worker("shell", self.connection_manager, command)
        task.signals.finished.connect(update_result)
        QThreadPool.globalInstance().start(task)

    def clear_command(self):
        """
        清空命令输入框。
        """
        self.ui_start.command.clear()

    def lianjie(self):
        """
        连接按钮点击事件，尝试连接到远程服务器。
        """
        ip = self.ui_start.ip_edit.text()
        username = self.ui_start.username_edit.text()
        password = self.ui_start.password_edit.text()

        try:
            if self.connection_manager.connect(ip, username, password):
                success_message = "连接成功!"
                QMessageBox.information(self, "成功!", success_message, QMessageBox.Ok)
                if self.ui_start.checkBox.isChecked():
                    self.ui_start.listWidget.addItem(f"{ip} {username} {password}")
                    self.save_info(load_info=False)  # 只在勾选保存时保存连接信息
                self.setup_after_connection()
            else:
                QMessageBox.warning(self, "错误", "连接失败！", QMessageBox.Ok)
        except Exception as e:
            self.log.error(e)
            QMessageBox.warning(self, "错误", f"连接失败！请检查参数是否正确+{e}", QMessageBox.Ok)

    def tuichu(self):
        """
        退出按钮点击事件，断开与远程服务器的连接。
        """
        if not self.connected:
            QMessageBox.warning(self, "错误", "请先连接！", QMessageBox.Ok)
            return

        self.connection_manager.disconnect()
        self.setup_before_connection()

        QMessageBox.information(self, "成功!", "成功退出连接！", QMessageBox.Ok)
        self.connected = False

    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem)
    def show_info(self, item):
        """
        展示已保存的服务器信息，并自动填充到对应的输入框中。
        """
        selected_text = item.text()
        parts = selected_text.split()
        if len(parts) >= 3:
            ip = parts[0]
            username = parts[1]
            password = parts[2]
            self.ui_start.ip_edit.setText(ip)
            self.ui_start.username_edit.setText(username)
            self.ui_start.password_edit.setText(password)

    def save_info(self, load_info=True):
        """
        保存连接信息到数据库中，并更新界面上的连接信息列表。
        """
        ip = self.ui_start.ip_edit.text()
        username = self.ui_start.username_edit.text()
        password = self.ui_start.password_edit.text()

        saved_info = self.saved_info_manager.get_saved_info()
        if (ip, username, password) in saved_info:
            QMessageBox.warning(self, "警告", "该连接信息已存在！", QMessageBox.Ok)
            return

        self.saved_info_manager.add_saved_info(ip, username, password)
        if load_info:
            self.load_saved_info()

    def load_saved_info(self):
        """
        加载保存的连接信息，并更新界面上的连接信息列表。
        """
        try:
            self.ui_start.listWidget.clear()

            saved_info = self.saved_info_manager.get_saved_info()
            for ip, username, password in saved_info:
                info = f"{ip} {username} {password}"
                self.ui_start.listWidget.addItem(info)
        except FileNotFoundError:
            self.log.error(f"没有找到saved_info.db文件，造成无法读取文件")

    @QtCore.pyqtSlot(QtCore.QPoint)
    def show_context_menu(self, pos):
        """
        右键菜单事件，显示右键菜单，并处理相应的操作。
        """
        menu = QMenu(self)
        delete_action = menu.addAction("删除")
        action = menu.exec_(self.ui_start.listWidget.mapToGlobal(pos))
        if action == delete_action:
            self.delete_item()

    def delete_item(self):
        """
        删除选择的项目，并从数据库中删除对应的连接信息。
        """
        selected_items = self.ui_start.listWidget.selectedItems()
        try:
            if selected_items:
                reply = QMessageBox.question(
                    self, "删除选择的项目",
                    f"确认要删除选择的项目吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    for item in selected_items:
                        info = item.text().split()
                        if len(info) >= 3:
                            ip = info[0]
                            username = info[1]
                            password = info[2]
                            self.saved_info_manager.remove_saved_info(ip, username, password)
                            self.log.info(f"删除选择的项目：{item.text()}")
                        else:
                            self.log.warning(f"无法删除项目：{item.text()}，部分信息缺失")
            self.load_saved_info()
        except Exception as e:
            self.log.error(f"删除报错: {e}")

    def setup_after_connection(self):
        """
        连接成功后的界面设置，禁用一些输入框和按钮，并记录原始的文本框内容。
        """
        self.connected = True
        self.ui_start.login_btn.setEnabled(False)
        self.ui_start.ip_edit.setDisabled(True)
        self.ui_start.username_edit.hide()
        self.ui_start.password_edit.hide()
        self.ui_start.checkBox.hide()
        self.ui_start.listWidget.hide()

        self.user_text = self.ui_start.user.text()
        self.pwd_text = self.ui_start.pwd.text()
        self.save_server_text = self.ui_start.save_server.text()
        self.ui_start.user.clear()
        self.ui_start.pwd.clear()
        self.ui_start.save_server.clear()

    def setup_before_connection(self):
        """
        连接断开后的界面设置，恢复输入框和按钮的状态，并还原文本框内容。
        """
        self.connected = False
        self.ui_start.login_btn.setEnabled(True)
        self.ui_start.ip_edit.setDisabled(False)
        self.ui_start.ip_edit.clear()
        self.ui_start.username_edit.show()
        self.ui_start.username_edit.clear()
        self.ui_start.password_edit.show()
        self.ui_start.password_edit.clear()
        self.ui_start.checkBox.show()
        self.ui_start.listWidget.show()
        self.ui_start.show.clear()

        self.ui_start.user.setText(self.user_text)  # 还原用户文本框的内容
        self.ui_start.pwd.setText(self.pwd_text)  # 还原密码文本框的内容
        self.ui_start.save_server.setText(self.save_server_text)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = Mainwindow()
    window.show()
    sys.exit(app.exec_())
