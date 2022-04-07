import json
import base64
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow,
    qApp,
    QMessageBox,
    QDialog,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, Qt
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from configs.errors import ServerError
from configs.variables import *


class Ui_MainClientWindow(object):
    def setupUi(self, MainClientWindow):
        MainClientWindow.setObjectName("MainClientWindow")
        MainClientWindow.resize(756, 534)
        MainClientWindow.setMinimumSize(QtCore.QSize(756, 534))
        self.centralwidget = QtWidgets.QWidget(MainClientWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label_contacts = QtWidgets.QLabel(self.centralwidget)
        self.label_contacts.setGeometry(QtCore.QRect(10, 0, 101, 16))
        self.label_contacts.setObjectName("label_contacts")
        self.btn_add_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add_contact.setGeometry(QtCore.QRect(10, 450, 121, 31))
        self.btn_add_contact.setObjectName("btn_add_contact")
        self.btn_remove_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_remove_contact.setGeometry(QtCore.QRect(140, 450, 121, 31))
        self.btn_remove_contact.setObjectName("btn_remove_contact")
        self.label_history = QtWidgets.QLabel(self.centralwidget)
        self.label_history.setGeometry(QtCore.QRect(300, 0, 391, 21))
        self.label_history.setObjectName("label_history")
        self.text_message = QtWidgets.QTextEdit(self.centralwidget)
        self.text_message.setGeometry(QtCore.QRect(300, 360, 441, 71))
        self.text_message.setObjectName("text_message")
        self.label_new_message = QtWidgets.QLabel(self.centralwidget)
        self.label_new_message.setGeometry(
            QtCore.QRect(300, 330, 450, 16)
        )  # Правка тут
        self.label_new_message.setObjectName("label_new_message")
        self.list_contacts = QtWidgets.QListView(self.centralwidget)
        self.list_contacts.setGeometry(QtCore.QRect(10, 20, 251, 411))
        self.list_contacts.setObjectName("list_contacts")
        self.list_messages = QtWidgets.QListView(self.centralwidget)
        self.list_messages.setGeometry(QtCore.QRect(300, 20, 441, 301))
        self.list_messages.setObjectName("list_messages")
        self.btn_send = QtWidgets.QPushButton(self.centralwidget)
        self.btn_send.setGeometry(QtCore.QRect(610, 450, 131, 31))
        self.btn_send.setObjectName("btn_send")
        self.btn_clear = QtWidgets.QPushButton(self.centralwidget)
        self.btn_clear.setGeometry(QtCore.QRect(460, 450, 131, 31))
        self.btn_clear.setObjectName("btn_clear")
        MainClientWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainClientWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 756, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")
        MainClientWindow.setMenuBar(self.menubar)
        self.statusBar = QtWidgets.QStatusBar(MainClientWindow)
        self.statusBar.setObjectName("statusBar")
        MainClientWindow.setStatusBar(self.statusBar)
        self.menu_exit = QtWidgets.QAction(MainClientWindow)
        self.menu_exit.setObjectName("menu_exit")
        self.menu_add_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_add_contact.setObjectName("menu_add_contact")
        self.menu_del_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_del_contact.setObjectName("menu_del_contact")
        self.menu.addAction(self.menu_exit)
        self.menu_2.addAction(self.menu_add_contact)
        self.menu_2.addAction(self.menu_del_contact)
        self.menu_2.addSeparator()
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.retranslateUi(MainClientWindow)
        self.btn_clear.clicked.connect(self.text_message.clear)
        QtCore.QMetaObject.connectSlotsByName(MainClientWindow)

    def retranslateUi(self, MainClientWindow):
        _translate = QtCore.QCoreApplication.translate
        MainClientWindow.setWindowTitle(
            _translate("MainClientWindow", "Messenger test release")
        )
        self.label_contacts.setText(_translate("MainClientWindow", "Contact list:"))
        self.btn_add_contact.setText(_translate("MainClientWindow", "Add contact"))
        self.btn_remove_contact.setText(_translate("MainClientWindow", "Del contact"))
        self.label_history.setText(_translate("MainClientWindow", "History message:"))
        self.label_new_message.setText(
            _translate("MainClientWindow", "Input new message:")
        )
        self.btn_send.setText(_translate("MainClientWindow", "Send message"))
        self.btn_clear.setText(_translate("MainClientWindow", "Clear text"))
        self.menu.setTitle(_translate("MainClientWindow", "Fail"))
        self.menu_2.setTitle(_translate("MainClientWindow", "Contacts"))
        self.menu_exit.setText(_translate("MainClientWindow", "Exit"))
        self.menu_add_contact.setText(_translate("MainClientWindow", "Add contact"))
        self.menu_del_contact.setText(_translate("MainClientWindow", "Del contact"))


class ClientMainWindow(QMainWindow):
    """Основное окно пользователя."""

    def __init__(self, database, transport, keys):
        super().__init__()
        self.database = database
        self.transport = transport
        self.decrypter = PKCS1_OAEP.new(keys)

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)
        self.ui.menu_exit.triggered.connect(qApp.exit)
        self.ui.btn_send.clicked.connect(self.send_message)
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)
        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def set_disabled_input(self):
        """Метод делает поля ввода неактивными"""
        self.ui.label_new_message.setText("double click for select user")
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

        self.encryptor = None
        self.current_chat = None
        self.current_chat_key = None

    def history_list_update(self):
        """Историей переписки с текущим собеседником."""
        lst = sorted(
            self.database.get_history(self.current_chat), key=lambda item: item[3]
        )
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        self.history_model.clear()
        length = len(lst)
        start_index = 0
        if length > 20:
            start_index = length - 20
        for i in range(start_index, length):
            item = lst[i]
            if item[1] == "in":
                mess = QStandardItem(
                    f"Incoming message {item[3].replace(microsecond=0)}:\n {item[2]}"
                )
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(
                    f"Outgoing message {item[3].replace(microsecond=0)}:\n {item[2]}"
                )
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    def select_active_user(self):
        """Обработчик события списка контактов."""
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        """Активация чата с собеседником."""
        try:
            self.current_chat_key = self.transport.key_request(self.current_chat)
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
        if not self.current_chat_key:
            self.messages.warning(self, "Error", "No encryption key for the user .")
            return

        self.ui.label_new_message.setText(f"Input text {self.current_chat}:")
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        self.history_list_update()

    def clients_list_update(self):
        """Обновление списка контактов."""
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_window(self):
        """Окно добавления контакта"""
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(
            lambda: self.add_contact_action(select_dialog)
        )
        select_dialog.show()

    def add_contact_action(self, item):
        """Обработчик  кнопки 'Добавить'"""
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        """Метод добавляющий контакт в серверную и клиентсткую BD."""
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, "Server error", err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, "Error", "Connection lost!")
                self.close()
            self.messages.critical(self, "Error", "Timeout!")
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            self.messages.information(self, "Well done", "Contact added.")

    def delete_contact_window(self):
        """Удаление контакта."""
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        """Метод удаляющий контакт из серверной и клиентсткой BD."""
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, "Server error", err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, "Error", "Connection lost!")
                self.close()
            self.messages.critical(self, "Error", "Timeout!")
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            self.messages.information(self, "Well done!", "Contact deleted")
            item.close()
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    def send_message(self):
        """Отправки и шифрование сообщения текущему собеседнику."""
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        message_text_encrypted = self.encryptor.encrypt(message_text.encode("utf8"))
        message_text_encrypted_base64 = base64.b64encode(message_text_encrypted)
        try:
            self.transport.send_message(
                self.current_chat, message_text_encrypted_base64.decode("ascii")
            )
            pass
        except ServerError as err:
            self.messages.critical(self, "Error", err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, "Error", "Connection lost!")
                self.close()
            self.messages.critical(self, "Error", "Timeout!")
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, "Error", "Connection lost!")
            self.close()
        else:
            self.database.save_message(self.current_chat, "out", message_text)
            self.history_list_update()

    @pyqtSlot(dict)
    def message(self, message):
        """
        Обработчик сообщений, выполняет дешифровку и сохранение в истории.
        Если пришло сообщение не от текущего собеседника.
        При необходимости меняет собеседника.
        """
        encrypted_message = base64.b64decode(message[MESSAGE_TEXT])
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError):
            self.messages.warning(self, "Error", "no decode message")
            return
        self.database.save_message(
            self.current_chat, "in", decrypted_message.decode("utf8")
        )

        sender = message[SENDER]
        if sender == self.current_chat:
            self.history_list_update()
        else:
            if self.database.check_contact(sender):
                if (
                    self.messages.question(
                        self,
                        "new message",
                        f"Incoming message {sender}, open chat?",
                        QMessageBox.Yes,
                        QMessageBox.No,
                    )
                    == QMessageBox.Yes
                ):
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print("NO")
                if (
                    self.messages.question(
                        self,
                        "New message",
                        f"Incoming message from {sender}.\n"
                        f"the user is not contact list.\n"
                        f"Add this user in contact list?",
                        QMessageBox.Yes,
                        QMessageBox.No,
                    )
                    == QMessageBox.Yes
                ):
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.database.save_message(
                        self.current_chat, "in", decrypted_message.decode("utf8")
                    )
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        """Слот обработчик потери соеднинения с сервером."""
        self.messages.warning(self, "Sorry", "Connection failure")
        self.close()

    @pyqtSlot()
    def sig_205(self):
        """Обновление баз данных."""
        if self.current_chat and not self.database.check_user(self.current_chat):
            self.messages.warning(self, "Sorry", "User was deleted")
            self.set_disabled_input()
            self.current_chat = None
        self.clients_list_update()

    def make_connection(self, trans_obj):
        """Соединение сигналов и слотов."""
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
        trans_obj.message_205.connect(self.sig_205)


class UserNameDialog(QDialog):
    """Класс запроса логина и пароля пользователя."""

    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle("Hello!")
        self.setFixedSize(175, 135)

        self.label = QLabel("Input username:", self)
        self.label.move(10, 10)
        self.label.setFixedSize(150, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.btn_ok = QPushButton("Run", self)
        self.btn_ok.move(10, 105)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton("Exit", self)
        self.btn_cancel.move(90, 105)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.label_passwd = QLabel("Enter password:", self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)

        self.show()

    def click(self):
        """Обрабтчик кнопки ОК."""
        if self.client_name.text() and self.client_passwd.text():
            self.ok_pressed = True
            qApp.exit()


class AddContactDialog(QDialog):
    """Добавление пользователя в список контактов."""

    def __init__(self, transport, database):
        super().__init__()
        self.transport = transport
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle("Select user to add:")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel("Select user to add:", self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_refresh = QPushButton("refresh list", self)
        self.btn_refresh.setFixedSize(100, 30)
        self.btn_refresh.move(60, 60)

        self.btn_ok = QPushButton("Add", self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton("Esc", self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.possible_contacts_update()
        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    def possible_contacts_update(self):
        """Отображение списка контактов."""
        self.selector.clear()
        contacts_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())
        users_list.remove(self.transport.username)
        self.selector.addItems(users_list - contacts_list)

    def update_possible_contacts(self):
        """Обновление списка контактов."""
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            self.possible_contacts_update()


class DelContactDialog(QDialog):
    """Удаление контакта."""

    def __init__(self, database):
        super().__init__()
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle("Select user for delete:")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel("Select user for delete:", self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton("Del", self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton("Esc", self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.selector.addItems(sorted(self.database.get_contacts()))
