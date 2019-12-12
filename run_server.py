from lib.CommonConstants import BUFFER_SIZE
import socket
from lib import PacketProcessor
from threading import Thread, Lock
from lib.ForumClasses import Topic, Message
import re


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
    send_packet = PacketProcessor.get_disc_packet()
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
            else:
                print("--------------\nMSG from %s: %s" % (client.name, data["data"]))

                send_packet = PacketProcessor.get_msg_packet(client_name=client.name, text=data["data"])

                mutex.acquire()
                for other_client in client_list:
                    if other_client != client:
                        print("RESENDING TO %s" % other_client.name)
                        other_client.conn.send(send_packet)
                mutex.release()
        elif opcode == PacketProcessor.OP_NEW_TOPIC:
            title = data["data"]
            print("%s WANT TO CREATE NEW TOPIC %s" % (client.name, title))
            topic = Topic(title)
            if not topic_list.__contains__(topic):
                print("NEW TOPIC %s ADDED" % title)
                topic_list.append(topic)
                send_packet = PacketProcessor.get_msg_packet(client_name="SERVER", text="topic %s created" % title)
                client.conn.send(send_packet)

            else:
                print("CAN'T CREATE TOPIC %s, ALREADY EXIST" % title)
                send_packet = PacketProcessor.get_msg_packet(client_name="SERVER", text="topic already exist")
                client.conn.send(send_packet)

        elif opcode == PacketProcessor.OP_GET_TOPIC_LIST:
            print("%s WANT TO GET TOPIC LIST" % (client.name))
            send_packet = PacketProcessor.get_topic_list_packet(topic_list)
            client.conn.send(send_packet)

        elif opcode == PacketProcessor.OP_SWITCH_TOPIC:
            topic_i = data["data"]
            print("%s WANT TO SWITCH TOPIC TO %d" % (client.name, topic_i))
            if topic_i < len(topic_list):
                send_packet = PacketProcessor.get_msg_packet(client_name="SERVER", text="your topic switched")
                client.current_topic = topic_list[topic_i]
            else:
                send_packet = PacketProcessor.get_msg_packet(client_name="SERVER",
                                                             text="topic_i must be < len(topic_list), but have %d" % topic_i)

            client.conn.send(send_packet)

        elif opcode == PacketProcessor.OP_DISC:
            remove_client("DISCONNECTION OPCODE == %d" % opcode, client, client_list)

        else:
            raise Exception("Undefined opcode = %d" % opcode)

    print("DISCONNECTED:Client = %s" % client.name)


def cmd_processing(client_list, topic_list):
    while True:
        command = re.sub(" +", " ", input())
        print("-------------------------")
        if command == "list client":
            for i, client in enumerate(client_list):
                print("%d:%s" % (i, client.name))
        elif command == "list topic":
            for i, topic in enumerate(topic_list):
                print("%d:%s" % (i, topic.title))

        print("-------------------------")


def main():
    client_list = []
    topic_list = []

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
            name = data["client_name"]
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


if __name__ == '__main__':
    main()
