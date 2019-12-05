class ClientInfo():
    def __init__(self, name, id):
        self.name = name
        self.id = id


class Message():
    def __init__(self, text, date, client):
        self.text = text
        self.date = date
        self.client = client


class Topic():
    def __init__(self, title):
        self.title = title
        self.message_story = []
