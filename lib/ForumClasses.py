from datetime import datetime
from lib import PacketProcessor
from threading import Lock


# ---------------------------- MESSAGE CLASS -----------------------------------
class Message():
    def __init__(self, text, date, client_name):
        self.text = text
        self.date = date
        self.client_name = client_name


# ---------------------------- TOPIC CLASS -----------------------------------
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


# ---------------------------- CLIENT CLASS -----------------------------------
class Client():
    def __init__(self, conn, addr, name, thread):
        self.conn = conn
        self.addr = addr
        self.name = name
        self.is_connected = False
        self.thread = thread
        self.current_topic = None

    def __str__(self):
        return "%s" % self.name


# ---------------------------- DATA CONTAINER CLASS -----------------------------------
class DataContainer():
    def __init__(self):
        self.client_list = []
        self.topic_list = []
        self.mutex = Lock()

    def mock_topics(self):
        for i in range(10):
            self.topic_list.append(Topic(title="topic_%d" % i))
            for mi in range(10):
                self.topic_list[i].message_story.append(
                    Message(text="message_%d" % mi, date=datetime.now(), client_name="client_%d" % mi))

    def remove_client(self, reason, client):
        print("DISCONNECTING:Client = %s (%s)" % (client.name, reason))
        send_packet = PacketProcessor.get_disc_packet(reason)
        client.conn.send(send_packet)
        client.is_connected = False
        self.client_list.remove(client)

        if client.current_topic is not None \
                and client.current_topic.client_list is not None \
                and client.current_topic.client_list.__contains__(client):
            client.current_topic.client_list.remove(client)

        client.conn.close()

    def remove_all_clients(self):
        print("CLIENTS DELETING")
        for client in self.client_list:
            self.remove_client(reason="server closed", client=client)

    def get_last_topic_msgs(self, topic_i, num):
        result = []
        if topic_i < len(self.topic_list):
            for message in self.topic_list[topic_i].message_story[-num:]:
                result.append(message)

        return result
