import socket
import time
import threading
import hashlib
import hmac
import binascii
from PyQt5.QtCore import pyqtSignal, QObject
from configs.utils import *
from configs.variables import *
from configs.errors import ServerError

socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    """
    Класс. Отвечает за взаимодействие с сервером.
    """

    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.password = passwd
        self.transport = None
        self.keys = keys
        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                raise ServerError("Connection lost!")
        self.running = True

    def connection_init(self, port, ip):
        """Устанновка соединения с сервером."""
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)
        connected = False
        for i in range(5):
            print(f"Connection №{i + 1}")
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            raise ServerError("No connection to the server")

        passwd_bytes = self.password.encode("UTF-8")
        salt = self.username.lower().encode("UTF-8")
        passwd_hash = hashlib.pbkdf2_hmac("sha512", passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)
        pubkey = self.keys.publickey().export_key().decode("ascii")

        with socket_lock:
            presense = {
                ACTION: PRESENCE,
                TIME: time.time(),
                USER: {ACCOUNT_NAME: self.username, PUBLIC_KEY: pubkey},
            }
            print(f"Presense message = {presense}")
            try:
                send_message(self.transport, presense)
                ans = get_message(self.transport)
                if RESPONSE in ans:
                    if ans[RESPONSE] == 400:
                        raise ServerError(ans[ERROR])
                    elif ans[RESPONSE] == 511:
                        ans_data = ans[DATA]
                        hash = hmac.new(
                            passwd_hash_string, ans_data.encode("UTF-8"), "MD5"
                        )
                        digest = hash.digest()
                        my_ans = RESPONSE_511
                        my_ans[DATA] = binascii.b2a_base64(digest).decode("ascii")
                        send_message(self.transport, my_ans)
                        self.process_server_ans(get_message(self.transport))
            except (OSError, json.JSONDecodeError) as err:
                raise ServerError("Authorization rror.")

    def process_server_ans(self, message):
        """Обработчик поступающих сообщений с сервера."""
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f"{message[ERROR]}")
            elif message[RESPONSE] == 205:
                self.user_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                print(f"Unknown error code {message[RESPONSE]}")
        elif (
            ACTION in message
            and message[ACTION] == MESSAGE
            and SENDER in message
            and DESTINATION in message
            and MESSAGE_TEXT in message
            and message[DESTINATION] == self.username
        ):
            self.new_message.emit(message)

    def contacts_list_update(self):
        """Обновление списка контактов."""
        self.database.contacts_clear()
        req = {ACTION: GET_CONTACTS, TIME: time.time(), USER: self.username}
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            print("Filed to update contact list")

    def user_list_update(self):
        """Обновление списка пользователей."""
        req = {ACTION: USERS_REQUEST, TIME: time.time(), ACCOUNT_NAME: self.username}
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            print("Filed to update users list")

    def key_request(self, user):
        """Запрос публичный ключ пользователя."""
        req = {ACTION: PUBLIC_KEY_REQUEST, TIME: time.time(), ACCOUNT_NAME: user}
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 511:
            return ans[DATA]
        else:
            print(f"Could not get the key {user}.")

    def add_contact(self, contact):
        """Добавление контакта."""
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact,
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def remove_contact(self, contact):
        """Удаление контакта."""
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact,
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def transport_shutdown(self):
        """Завершение работы клиента."""
        self.running = False
        message = {ACTION: EXIT, TIME: time.time(), ACCOUNT_NAME: self.username}
        with socket_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        time.sleep(0.5)

    def send_message(self, to, message):
        """Метод. Отправляет на сервер сообщения для пользователя."""
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message,
        }
        with socket_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))

    def run(self):
        """Основной цикл работы потока."""
        while self.running:
            time.sleep(1)
            message = None
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        self.running = False
                        self.connection_lost.emit()
                except (
                    ConnectionError,
                    ConnectionAbortedError,
                    ConnectionResetError,
                    json.JSONDecodeError,
                    TypeError,
                ):
                    self.running = False
                    self.connection_lost.emit()
                finally:
                    self.transport.settimeout(5)
            if message:
                self.process_server_ans(message)
