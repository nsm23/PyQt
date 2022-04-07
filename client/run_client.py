import argparse
import sys
import os
from Crypto.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox
from configs.variables import *
from configs.errors import ServerError
from database import ClientDatabase
from transport import ClientTransport
from main_window import ClientMainWindow, UserNameDialog


def arg_parser():
    """
    Парсер аргументов командной строки.
    Выполняет проверку на корректность номера порта.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("addr", default=DEFAULT_IP_ADDRESS, nargs="?")
    parser.add_argument("port", default=DEFAULT_PORT, type=int, nargs="?")
    parser.add_argument("-n", "--name", default=None, nargs="?")
    parser.add_argument("-p", "--password", default="", nargs="?")
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    if not 1023 < server_port < 65536:
        sys.exit(1)
    return server_address, server_port, client_name, client_passwd


if __name__ == "__main__":
    server_address, server_port, client_name, client_passwd = arg_parser()

    client_app = QApplication(sys.argv)

    start_dialog = UserNameDialog()
    if not client_name or not client_passwd:
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
        else:
            sys.exit(0)

    dir_path = os.getcwd()
    key_file = os.path.join(dir_path, f"{client_name}.key")
    if not os.path.exists(key_file):
        keys = RSA.generate(1024, os.urandom)
        with open(key_file, "wb") as key:
            key.write(keys.export_key())
    else:
        with open(key_file, "rb") as key:
            keys = RSA.importKey(key.read())

    database = ClientDatabase(client_name)
    try:
        transport = ClientTransport(
            server_port, server_address, database, client_name, client_passwd, keys
        )
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, "Server error", error.text)
        sys.exit(1)
    transport.setDaemon(True)
    transport.start()

    del start_dialog

    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f"Messenger test release - {client_name}")
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
