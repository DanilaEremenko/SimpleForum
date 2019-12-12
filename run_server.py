from lib.CommonConstants import BUFFER_SIZE
import socket
from lib import PacketProcessor
from threading import Thread, Lock
from lib.ForumClasses import Topic, Message
import re
import datetime


class Client():
    def __init__(self, conn, addr, name, thread):
        self.conn = conn
        self.addr = addr
        self.name = name
        self.is_connected = False
        self.thread = thread
        self.current_topic = None


def debug_print(text):
    print("DEBUG:%s" % text)


def remove_client(reason, client, client_list: list):
    print("DISCONNECTING:Client = %s (%s)" % (client.name, reason))
    send_packet = PacketProcessor.get_disc_packet(reason)
    client.conn.send(send_packet)
    client.is_connected = False
    client_list.remove(client)
    client.conn.close()


def client_processing(client: Client, client_list: list, topic_list: list, mutex):
    client.is_connected = True
    print("New client = %s(%d) accepted" % (client.name, client.conn.fileno()))
    while client.is_connected:
        opcode, data = PacketProcessor.parse_packet(client.conn.recv(BUFFER_SIZE))

        if opcode == PacketProcessor.OP_MSG:

            if not data or data == '':
                remove_client("BAD MESSAGE", client, client_list)
                break

            else:
                print("--------------\nMSG from %s: %s" % (client.name, data["data"]["text"]))

                if client.current_topic is None:
                    send_packet = PacketProcessor.get_server_message_packet(text="NO ONE TOPIC CHOOSED")
                else:
                    send_packet = PacketProcessor.get_msg_packet(client_name=client.name, text=data["data"]["text"])
                    mutex.acquire()
                    for other_client in client.current_topic.client_list:
                        print("RESENDING TO CLIENTS IN %s TOPIC" % client.current_topic.title)
                        if other_client != client:
                            print("RESENDING TO %s" % other_client.name)
                            other_client.conn.send(send_packet)
                            client.current_topic.message_story.append(
                                Message(text=data["data"], date=datetime.datetime.now(), client_name=client.name))
                    mutex.release()

        elif opcode == PacketProcessor.OP_NEW_TOPIC:
            title = data["data"]
            print("%s WANT TO CREATE NEW TOPIC %s" % (client.name, title))
            topic = Topic(title)

            if not topic_list.__contains__(topic):
                print("NEW TOPIC %s ADDED" % title)
                topic_list.append(topic)
                send_packet = PacketProcessor.get_server_message_packet(text="topic %s created" % title)

            else:
                print("CAN'T CREATE TOPIC %s, ALREADY EXIST" % title)
                send_packet = PacketProcessor.get_server_message_packet(text="topic already exist")

        elif opcode == PacketProcessor.OP_GET_TOPIC_LIST:
            print("%s WANT TO GET TOPIC LIST" % (client.name))
            send_packet = PacketProcessor.get_topic_list_packet(topic_list)

        elif opcode == PacketProcessor.OP_SWITCH_TOPIC:
            topic_i = data["data"]
            print("%s WANT TO SWITCH TOPIC TO %d" % (client.name, topic_i))
            if topic_i < len(topic_list):

                if not topic_list[topic_i].client_list.__contains__(client):
                    print("CONNECTING AND SENDING LATS 10 CLIENTS")
                    send_packet = PacketProcessor.get_msg_list_packet(
                        message_list=get_last_from_topic_as_str(topic_list, topic_i))
                    client.current_topic = topic_list[topic_i]
                    topic_list[topic_i].client_list.append(client)
                else:
                    print("SENDING SORRY MESSAGE")
                    send_packet = PacketProcessor.get_server_message_packet(
                        text="You're trying to connect to your current topic ")

            else:
                send_packet = PacketProcessor.get_server_message_packet(
                    text="topic_i must be < len(topic_list), but have %d" % topic_i)


        elif opcode == PacketProcessor.OP_DISC:
            remove_client("DISCONNECTION OPCODE == %d" % opcode, client, client_list)
            break

        else:
            raise Exception("Undefined opcode = %d" % opcode)

        client.conn.send(send_packet)

    print("DISCONNECTED:Client = %s" % client.name)


def get_last_from_topic_as_str(topic_list, topic_i):
    result = []
    if topic_i < len(topic_list):
        for message in topic_list[topic_i].message_story[-10:]:
            result.append(message)

    return result


def cmd_processing(client_list, topic_list):
    while True:
        command = re.sub(" +", " ", input())
        command_splited = command.split()
        print("-------------------------")
        if command == "list client":
            for i, client in enumerate(client_list):
                print("%d:%s" % (i, client.name))
        elif command == "list topic":
            for i, topic in enumerate(topic_list):
                print("%d:%s" % (i, topic.title))
        elif len(command_splited) >= 2 and command_splited[0] == "get_topic_messages":  # print last 10 message
            topic_i = int(command_splited[1])
            for message in get_last_from_topic_as_str(topic_list, topic_i):
                print("[%s]:%s:%s\n" % (message.date.strftime("%Y-%m-%d-%H.%M.%S"), message.client_name, message.text))

        print("-------------------------")


def mock_topics(topic_list):
    for i in range(10):
        topic_list.append(Topic(title="topic_%d" % i))
        for mi in range(10):
            topic_list[i].message_story.append(
                Message(text="message_%d" % mi, date=datetime.datetime.now(), client_name="client_%d" % mi))


def main():
    client_list = []
    topic_list = []
    mock_topics(topic_list)

    TCP_IP = 'localhost'
    TCP_PORT = 5005

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    mutex = Lock()

    # running cmd thread
    cmd_thread = Thread(target=cmd_processing, args=(client_list, topic_list), daemon=True)
    cmd_thread.start()

    while True:
        # new clients accepting
        conn, addr = s.accept()
        opcode, data = PacketProcessor.parse_packet(conn.recv(BUFFER_SIZE))
        if opcode == PacketProcessor.OP_MSG:
            name = data["data"]["client_name"]
            new_client = Client(conn=conn, addr=addr, name=name, thread=None)
            new_client.thread = Thread(target=client_processing,
                                       args=(new_client, client_list, topic_list, mutex),
                                       daemon=True)

            mutex.acquire()
            client_list.append(new_client)
            mutex.release()

            new_client.thread.start()

        else:
            print("opcode = %d (%d awaiting)" % (opcode, PacketProcessor.OP_MSG))
            send_message = PacketProcessor.get_disc_packet("NO NAME MESSAGE SENDED")
            conn.send(send_message)


if __name__ == '__main__':
    main()
