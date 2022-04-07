import os
import hashlib
import binascii
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    qApp,
    QTableView,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QTimer


class MainWindow(QMainWindow):
    """Класс - основное окно сервера."""

    def __init__(self, database, server, config):
        super().__init__()
        self.database = database
        self.server_thread = server
        self.config = config

        self.exitAction = QAction("Exit", self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.triggered.connect(qApp.quit)

        self.refresh_button = QAction("Refresh list", self)
        self.config_btn = QAction("Config server", self)
        self.register_btn = QAction("User registration", self)
        self.remove_btn = QAction("User delete", self)
        self.show_history_button = QAction("Users history", self)

        self.statusBar()
        self.statusBar().showMessage("Server Working")

        self.toolbar = self.addToolBar("MainBar")
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)
        self.toolbar.addAction(self.register_btn)
        self.toolbar.addAction(self.remove_btn)

        self.setFixedSize(800, 600)
        self.setWindowTitle("Messenger test release")

        self.label = QLabel("Active users list:", self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 25)

        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 45)
        self.active_clients_table.setFixedSize(780, 400)

        self.timer = QTimer()
        self.timer.timeout.connect(self.create_users_model)
        self.timer.start(1000)

        self.refresh_button.triggered.connect(self.create_users_model)
        self.show_history_button.triggered.connect(self.show_statistics)
        self.config_btn.triggered.connect(self.server_config)
        self.register_btn.triggered.connect(self.reg_user)
        self.remove_btn.triggered.connect(self.rem_user)

        self.show()

    def create_users_model(self):
        list_users = self.database.active_users_list()
        lst = QStandardItemModel()
        lst.setHorizontalHeaderLabels(
            ["Username", "IP address", "Port", "Connection time"]
        )
        for row in list_users:
            user, ip, port, time = row
            user = QStandardItem(user)
            user.setEditable(False)
            ip = QStandardItem(ip)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(str(time.replace(microsecond=0)))
            time.setEditable(False)
            lst.appendRow([user, ip, port, time])
        self.active_clients_table.setModel(lst)
        self.active_clients_table.resizeColumnsToContents()
        self.active_clients_table.resizeRowsToContents()

    def show_statistics(self):
        global stat_window
        stat_window = StatWindow(self.database)
        stat_window.show()

    def server_config(self):
        global config_window
        config_window = ConfigWindow(self.config)

    def reg_user(self):
        global reg_window
        reg_window = RegisterUser(self.database, self.server_thread)
        reg_window.show()

    def rem_user(self):
        global rem_window
        rem_window = DelUserDialog(self.database, self.server_thread)
        rem_window.show()


class ConfigWindow(QDialog):
    """Класс окно настроек."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.initUI()

    def initUI(self):
        self.setFixedSize(365, 260)
        self.setWindowTitle("Config server")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.db_path_label = QLabel("Browse: ", self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        self.db_path_select = QPushButton("Browse...", self)
        self.db_path_select.move(275, 28)

        self.db_file_label = QLabel("database name: ", self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        self.port_label = QLabel("Port:", self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        self.ip_label = QLabel("IP address:", self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        self.ip_label_note = QLabel("if empty,\n connection from any adr.", self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        self.save_btn = QPushButton("Save", self)
        self.save_btn.move(190, 220)

        self.close_button = QPushButton("Close", self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.db_path_select.clicked.connect(self.open_file_dialog)

        self.show()

        self.db_path.insert(self.config["SETTINGS"]["Database_path"])
        self.db_file.insert(self.config["SETTINGS"]["Database_file"])
        self.port.insert(self.config["SETTINGS"]["Default_port"])
        self.ip.insert(self.config["SETTINGS"]["Listen_Address"])
        self.save_btn.clicked.connect(self.save_server_config)

    def open_file_dialog(self):
        global dialog
        dialog = QFileDialog(self)
        path = dialog.getExistingDirectory()
        path = path.replace("/", "\\")
        self.db_path.clear()
        self.db_path.insert(path)

    def save_server_config(self):
        global config_window
        message = QMessageBox()
        self.config["SETTINGS"]["Database_path"] = self.db_path.text()
        self.config["SETTINGS"]["Database_file"] = self.db_file.text()
        try:
            port = int(self.port.text())
        except ValueError:
            message.warning(self, "Error", "Port must be a number")
        else:
            self.config["SETTINGS"]["Listen_Address"] = self.ip.text()
            if 1023 < port < 65536:
                self.config["SETTINGS"]["Default_port"] = str(port)
                dir_path = os.getcwd()
                dir_path = os.path.join(dir_path, "..")
                with open(f"{dir_path}/{'server.ini'}", "w") as conf:
                    self.config.write(conf)
                    message.information(self, "OK", "Settings saved")
            else:
                message.warning(self, "Error", "Port must be a number")


class StatWindow(QDialog):
    """Класс - статистики пользователей"""

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Users statistics")
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.close_button = QPushButton("Close", self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        self.stat_table = QTableView(self)
        self.stat_table.move(10, 10)
        self.stat_table.setFixedSize(580, 620)

        self.create_stat_model()

    def create_stat_model(self):
        stat_list = self.database.message_history()

        lst = QStandardItemModel()
        lst.setHorizontalHeaderLabels(
            [
                "Username",
                "Last login",
                "Messages sent",
                "Messages received",
            ]
        )
        for row in stat_list:
            user, last_seen, sent, recvd = row
            user = QStandardItem(user)
            user.setEditable(False)
            last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
            last_seen.setEditable(False)
            sent = QStandardItem(str(sent))
            sent.setEditable(False)
            recvd = QStandardItem(str(recvd))
            recvd.setEditable(False)
            lst.appendRow([user, last_seen, sent, recvd])
        self.stat_table.setModel(lst)
        self.stat_table.resizeColumnsToContents()
        self.stat_table.resizeRowsToContents()


class RegisterUser(QDialog):
    """Класс - регистрации пользователя на сервере."""

    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        self.setWindowTitle("Registration")
        self.setFixedSize(175, 183)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.label_username = QLabel("Enter username:", self)
        self.label_username.move(10, 10)
        self.label_username.setFixedSize(150, 15)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.label_passwd = QLabel("Enter pass:", self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)
        self.label_conf = QLabel("Enter the pass again:", self)
        self.label_conf.move(10, 100)
        self.label_conf.setFixedSize(150, 15)

        self.client_conf = QLineEdit(self)
        self.client_conf.setFixedSize(154, 20)
        self.client_conf.move(10, 120)
        self.client_conf.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton("Save", self)
        self.btn_ok.move(10, 150)
        self.btn_ok.clicked.connect(self.save_data)

        self.btn_cancel = QPushButton("Exit", self)
        self.btn_cancel.move(90, 150)
        self.btn_cancel.clicked.connect(self.close)

        self.messages = QMessageBox()

        self.show()

    def save_data(self):
        if not self.client_name.text():
            self.messages.critical(self, "Error", "Input username.")
            return
        elif self.client_passwd.text() != self.client_conf.text():
            self.messages.critical(self, "Error", "Passwords don`t match.")
            return
        elif self.database.check_user(self.client_name.text()):
            self.messages.critical(self, "Error", "User already exist.")
            return
        else:
            passwd_bytes = self.client_passwd.text().encode("UTF-8")
            salt = self.client_name.text().lower().encode("UTF-8")
            passwd_hash = hashlib.pbkdf2_hmac("sha512", passwd_bytes, salt, 10000)
            self.database.add_user(
                self.client_name.text(), binascii.hexlify(passwd_hash)
            )
            self.messages.information(self, "Well done", "The user is registered")
            self.server.service_update_lists()
            self.close()


class DelUserDialog(QDialog):
    """Класс - удаления контакта."""

    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        self.setFixedSize(350, 120)
        self.setWindowTitle("Delete user")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel("Select the user to delete:", self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton("Delete", self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)
        self.btn_ok.clicked.connect(self.remove_user)

        self.btn_cancel = QPushButton("Esc", self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.all_users_fill()

    def all_users_fill(self):
        self.selector.addItems([item[0] for item in self.database.users_list()])

    def remove_user(self):
        self.database.remove_user(self.selector.currentText())
        if self.selector.currentText() in self.server.names:
            sock = self.server.names[self.selector.currentText()]
            del self.server.names[self.selector.currentText()]
            self.server.remove_client(sock)
        self.server.service_update_lists()
        self.close()
