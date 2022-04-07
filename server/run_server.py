import os
import sys
import argparse
import configparser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from core import MessageProcessor
from database import ServerStorage
from main_window import MainWindow
from configs.variables import *


def arg_parser(default_port, default_address):
    """Парсер аргументов коммандной строки."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", default=default_port, type=int, nargs="?")
    parser.add_argument("-a", default=default_address, nargs="?")
    parser.add_argument("--no_gui", action="store_true")
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    gui_flag = namespace.no_gui
    return listen_address, listen_port, gui_flag


def config_load():
    config = configparser.ConfigParser()
    dir_path = os.getcwd()
    config.read(f"{dir_path}/{'server.ini'}")
    if "SETTINGS" in config:
        return config
    else:
        config.add_section("SETTINGS")
        config.set("SETTINGS", "Default_port", str(DEFAULT_PORT))
        config.set("SETTINGS", "Listen_Address", "")
        config.set("SETTINGS", "Database_path", "")
        config.set("SETTINGS", "Database_file", "server_database.db3")
        return config


def main():
    config = config_load()
    listen_address, listen_port, gui_flag = arg_parser(
        config["SETTINGS"]["Default_port"], config["SETTINGS"]["Listen_Address"]
    )
    database = ServerStorage(
        os.path.join(
            config["SETTINGS"]["Database_path"], config["SETTINGS"]["Database_file"]
        )
    )

    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    if gui_flag:
        while True:
            command = input("Enter 'exit' for close server.")
            if command == "exit":
                server.running = False
                server.join()
                break
    else:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)

        server_app.exec_()

        server.running = False


if __name__ == "__main__":
    sys.exit(main())
