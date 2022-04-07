class ServerError(Exception):
    """Класс - исключение, для обработки ошибок сервера."""

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text
