import dis


class ServerVerifier(type):
    """
    Метакласс. Проверяет, что в  классе нет клиентских
    вызовов таких как: connect. Также проверяет, что
    сокет является TCP и работает по IPv4 протоколу.
    """

    def __init__(cls, clsname, bases, clsdict):
        attrs = []
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == "LOAD_GLOBAL":
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == "LOAD_ATTR":
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        if "connect" in methods:
            raise TypeError('The method "connect" is invalid in the class')
        if not ("SOCK_STREAM" in attrs and "AF_INET" in attrs):
            raise TypeError("Invalid socket.")
        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    """
    Метакласс. Проверяет что в классе нет серверных
    вызовов таких как: accept, listen. Также проверяет, что сокет не
    создаётся внутри конструктора класса.
    """

    def __init__(cls, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == "LOAD_GLOBAL":
                        if i.argval not in methods:
                            methods.append(i.argval)
        for command in ("accept", "listen", "socket"):
            if command in methods:
                raise TypeError("Forbidden method")
        if "get_message" in methods or "send_message" in methods:
            pass
        else:
            raise TypeError("There is no function call that works with sockets")
        super().__init__(clsname, bases, clsdict)
