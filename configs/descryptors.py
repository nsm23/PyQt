class Port:
    """Класс - дескриптор для номера порта."""
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            print(f". Error port. 1024 < {value} < 65535.")
            raise TypeError("Error port")
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
