class Message():
    def __init__(self, text, date, client_name):
        self.text = text
        self.date = date
        self.client_info = client_name


class Topic():
    def __init__(self, title):
        self.title = title
        self.client_list = []
        self.message_story = []

    def __eq__(self, other):
        if self.title == other.title:
            return True
        else:
            return False
