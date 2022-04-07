import os
import threading
import select
import socket
import hmac
import binascii
from configs.descryptors import Port
from configs.utils import get_message, send_message
from configs.variables import *


class MessageProcessor(threading.Thread):
    """
    Основной класс сервера. Принимает содинения
    от клиентов, обрабатывает поступающие сообщения.
    """

    port = Port()

    def __init__(self, listen_address, listen_port, database):
        super().__init__()
        self.addr = listen_address
        self.port = listen_port
        self.database = database
        self.sock = None
        self.clients = []
        self.listen_sockets = None
        self.error_sockets = None
        self.running = True
        self.names = dict()

    def run(self):
        self.init_socket()
        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            try:
                if self.clients:
                    (
                        recv_data_lst,
                        self.listen_sockets,
                        self.error_sockets,
                    ) = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                print(f"Socket`s error: {err.errno}")
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(
                            get_message(client_with_message), client_with_message
                        )
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)
        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def process_message(self, message):
        if (
            message[DESTINATION] in self.names
            and self.names[message[DESTINATION]] in self.listen_sockets
        ):
            try:
                send_message(self.names[message[DESTINATION]], message)
            except OSError:
                self.remove_client(message[DESTINATION])
        elif (
            message[DESTINATION] in self.names
            and self.names[message[DESTINATION]] not in self.listen_sockets
        ):
            self.remove_client(self.names[message[DESTINATION]])
        else:
            print(f"User {message[DESTINATION]} not registered.")

    def process_client_message(self, message, client):
        if (
            ACTION in message
            and message[ACTION] == PRESENCE
            and TIME in message
            and USER in message
        ):
            self.autorize_user(message, client)
        elif (
            ACTION in message
            and message[ACTION] == MESSAGE
            and DESTINATION in message
            and TIME in message
            and SENDER in message
            and MESSAGE_TEXT in message
            and self.names[message[SENDER]] == client
        ):
            if message[DESTINATION] in self.names:
                self.database.process_message(message[SENDER], message[DESTINATION])
                self.process_message(message)
                try:
                    send_message(client, RESPONSE_200)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = "User not registered."
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return
        elif (
            ACTION in message
            and message[ACTION] == EXIT
            and ACCOUNT_NAME in message
            and self.names[message[ACCOUNT_NAME]] == client
        ):
            self.remove_client(client)
        elif (
            ACTION in message
            and message[ACTION] == GET_CONTACTS
            and USER in message
            and self.names[message[USER]] == client
        ):
            response = RESPONSE_202
            response[LIST_INFO] = self.database.get_contacts(message[USER])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)
        elif (
            ACTION in message
            and message[ACTION] == ADD_CONTACT
            and ACCOUNT_NAME in message
            and USER in message
            and self.names[message[USER]] == client
        ):
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)
        elif (
            ACTION in message
            and message[ACTION] == REMOVE_CONTACT
            and ACCOUNT_NAME in message
            and USER in message
            and self.names[message[USER]] == client
        ):
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            try:
                send_message(client, RESPONSE_200)
            except OSError:
                self.remove_client(client)
        elif (
            ACTION in message
            and message[ACTION] == USERS_REQUEST
            and ACCOUNT_NAME in message
            and self.names[message[ACCOUNT_NAME]] == client
        ):
            response = RESPONSE_202
            response[LIST_INFO] = [user[0] for user in self.database.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)
        elif (
            ACTION in message
            and message[ACTION] == PUBLIC_KEY_REQUEST
            and ACCOUNT_NAME in message
        ):
            response = RESPONSE_511
            response[DATA] = self.database.get_pubkey(message[ACCOUNT_NAME])
            if response[DATA]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = RESPONSE_400
                response[ERROR] = "Not public key for user"
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
        else:
            response = RESPONSE_400
            response[ERROR] = "Error"
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):
        if message[USER][ACCOUNT_NAME] in self.names.keys():
            response = RESPONSE_400
            response[ERROR] = "Имя пользователя уже занято."
            try:
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        elif not self.database.check_user(message[USER][ACCOUNT_NAME]):
            response = RESPONSE_400
            response[ERROR] = "User not registered."
            try:
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            message_auth = RESPONSE_511
            random_str = binascii.hexlify(os.urandom(64))
            message_auth[DATA] = random_str.decode("ascii")
            hash = hmac.new(
                self.database.get_hash(message[USER][ACCOUNT_NAME]), random_str, "MD5"
            )
            digest = hash.digest()
            try:
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[DATA])
            if (
                RESPONSE in ans
                and ans[RESPONSE] == 511
                and hmac.compare_digest(digest, client_digest)
            ):
                self.names[message[USER][ACCOUNT_NAME]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, RESPONSE_200)
                except OSError:
                    self.remove_client(message[USER][ACCOUNT_NAME])
                self.database.user_login(
                    message[USER][ACCOUNT_NAME],
                    client_ip,
                    client_port,
                    message[USER][PUBLIC_KEY],
                )
            else:
                response = RESPONSE_400
                response[ERROR] = "Wrong password"
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        for client in self.names:
            try:
                send_message(self.names[client], RESPONSE_205)
            except OSError:
                self.remove_client(self.names[client])
