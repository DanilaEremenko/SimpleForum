import argparse

import colorama
from datetime import datetime
import os
import re
import socket
from threading import Thread

from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor
from lib.ForumClasses import Topic, Message, DataContainer, Client

# ------------------------------ COLORS -----------------------------------
COLOR_DATE = colorama.Fore.YELLOW
COLOR_NAME = colorama.Fore.BLUE
COLOR_TEXT = colorama.Fore.WHITE
COLOR_DEBUG = colorama.Fore.RED
COLOR_SERVER_NAME = colorama.Fore.RED
COLOR_TOPIC_NAME = colorama.Fore.CYAN
COLOR_DIV_LINES = colorama.Fore.MAGENTA
COLOR_COMMAND = colorama.Fore.GREEN
COLOR_INDEX = colorama.Fore.WHITE

# ------------------------------ CAPACITY CONSTANTS ----------------------------
MAX_MSG_IN_TOPIC = 50
MSG_FROM_TOPIC_NUM = 10

# ---------------------------- CMD -----------------------------------
HELP_SERVER = "%s------------ AVAILABLE SERVER COMMANDS ----------\n" \
              "%slist client\n" \
              "list topic\n" \
              "listmsg topic_i:int\n" \
              "help\n" \
              "exit\n" \
              "%s-------------------------------------------------\n%s" % (
                  COLOR_DIV_LINES, COLOR_COMMAND, COLOR_DIV_LINES, colorama.Fore.RESET)


def debug_print(text):
    print("%sDEBUG:%s" % (colorama.Fore.RED, text))


# ---------------------------------- CMD INPUT  ----------------------------------------------
def cmd_processing(dc: DataContainer):
    while True:
        command = re.sub(" +", " ", input())
        command_splited = command.split()
        if command == "list client":
            for i, client in enumerate(dc.client_list):
                print("%s%d:%s%s%s" % (COLOR_INDEX, i, COLOR_NAME, client.name, colorama.Fore.RESET))

        elif command == "list topic":
            topic_dict = PacketProcessor.get_topic_dict(dc.topic_list)
            for topic_i, (topic_name, client_list) in \
                    enumerate(zip(topic_dict.keys(), topic_dict.values())):
                print("%s%d:%s%s" % (COLOR_INDEX, topic_i, COLOR_TOPIC_NAME, topic_name))
                for client_i, client in enumerate(client_list):
                    print("\t%s%d:%s%s" % (COLOR_INDEX, client_i, COLOR_NAME, client))

            print(colorama.Fore.RESET)


        elif len(command_splited) >= 2 and command_splited[0] == "listmsg":  # print last 10 message
            try:
                topic_i = int(command_splited[1])
            except:
                continue
            for message in dc.get_last_topic_msgs(topic_i, MSG_FROM_TOPIC_NUM):
                print("%s[%s]:%s%s:%s%s" %
                      (COLOR_DATE, message.date.strftime("%Y-%m-%d-%H.%M.%S"),
                       COLOR_NAME, message.client_name,
                       COLOR_TEXT, message.text))
            print(colorama.Fore.RESET)

        elif command == "help":
            print(HELP_SERVER)

        elif command == "exit":
            exit_server(dc)

        else:
            print("Undefined command = %s. Use help for information" % command)


# ---------------------------- client_processing -----------------------------------
def client_processing(client: Client, dc: DataContainer):
    # ---------------------- getting name --------------------------------------
    opcode, data = PacketProcessor.parse_packet(client.conn.recv(BUFFER_SIZE))
    if opcode == PacketProcessor.OP_MSG:
        client.name = data["data"]["client_name"]

    else:
        print("opcode = %d (%d awaiting)" % (opcode, PacketProcessor.OP_MSG))
        send_packet = PacketProcessor.get_disc_packet("NO NAME MESSAGE SENDED")
        client.conn.send(send_packet)
        dc.remove_client(reason="BAD OPCODE OF INIT MESSAGE", client=client)

    client.is_connected = True
    print("New client = %s(%d) accepted" % (client.name, client.conn.fileno()))

    # -------------------- process client loop -----------------------------------
    while client.is_connected:
        opcode, data = PacketProcessor.parse_packet(client.conn.recv(BUFFER_SIZE))

        if opcode == PacketProcessor.OP_MSG:

            if not data or data == '':
                dc.remove_client(reason="BAD MESSAGE", client=client)
                break

            else:
                print("--------------\nMSG from %s: %s" % (client.name, data["data"]["text"]))

                if client.current_topic is None:
                    send_packet = PacketProcessor.get_server_message_packet(text="NO ONE TOPIC CHOOSED")
                else:
                    send_packet = PacketProcessor.get_msg_packet(client_name=client.name, text=data["data"]["text"])
                    dc.mutex.acquire()

                    print("RESENDING TO CLIENTS IN %s TOPIC" % client.current_topic.title)
                    for other_client in client.current_topic.client_list:
                        if other_client != client:
                            print("RESENDING TO %s" % other_client.name)
                            other_client.conn.send(send_packet)

                    client.current_topic.message_story.append(
                        Message(text=data["data"]["text"],
                                date=datetime.now(),
                                client_name=client.name))
                    if len(client.current_topic.message_story) >= MAX_MSG_IN_TOPIC:
                        del client.current_topic.message_story[MAX_MSG_IN_TOPIC:]
                    dc.mutex.release()
                    continue

        elif opcode == PacketProcessor.OP_NEW_TOPIC:
            title = data["data"]["topic_name"]
            print("%s WANT TO CREATE NEW TOPIC %s" % (client.name, title))
            topic = Topic(title)

            if not topic in dc.topic_list:
                print("NEW TOPIC %s ADDED" % title)
                dc.topic_list.append(topic)
                send_packet = PacketProcessor.get_server_message_packet(text="topic %s created" % title)

            else:
                print("CAN'T CREATE TOPIC %s, ALREADY EXIST" % title)
                send_packet = PacketProcessor.get_server_message_packet(text="topic already exist")

        elif opcode == PacketProcessor.OP_GET_TOPIC_LIST:
            print("%s WANT TO GET TOPIC LIST" % (client.name))
            send_packet = PacketProcessor.get_topic_list_packet(dc.topic_list)

        elif opcode == PacketProcessor.OP_SWITCH_TOPIC:
            topic_i = data["data"]["topic_i"]
            print("%s WANT TO SWITCH TOPIC TO %d" % (client.name, topic_i))
            if topic_i < len(dc.topic_list):

                if not client in dc.topic_list[topic_i].client_list:
                    print("CONNECTING AND SENDING LATS 10 CLIENTS")
                    send_packet = PacketProcessor.get_msg_list_packet(
                        message_list=dc.get_last_topic_msgs(topic_i, MSG_FROM_TOPIC_NUM))

                    for topic in dc.topic_list:
                        if topic.client_list.__contains__(client):
                            topic.client_list.remove(client)

                    client.current_topic = dc.topic_list[topic_i]
                    dc.topic_list[topic_i].client_list.append(client)
                else:
                    print("SENDING SORRY MESSAGE")
                    send_packet = PacketProcessor.get_server_message_packet(
                        text="You're trying to connect to your current topic ")

            else:
                send_packet = PacketProcessor.get_server_message_packet(
                    text="topic_i must be < len(topic_list), but have %d" % topic_i)


        elif opcode == PacketProcessor.OP_DISC:
            dc.remove_client(reason="DISCONNECTION OPCODE == %d" % opcode, client=client)
            break

        else:
            raise Exception("Undefined opcode = %d" % opcode)

        client.conn.send(send_packet)

    print("DISCONNECTED:Client = %s" % client.name)


# ---------------------------------- EXIT----------------------------------
def exit_server(dc: DataContainer):
    dc.remove_all_clients()
    print("SERVER EXITING")
    os._exit(0)


# ---------------------------------- MAIN ----------------------------------
def main():
    dc = DataContainer()
    dc.mock_topics()
    # ---------------- parsing arguments --------------------------
    parser = argparse.ArgumentParser(description="Client for SimpleForum")

    parser.add_argument("-i", "--ip", type=str, action='store',
                        help="direcotry with data")

    parser.add_argument("-p", "--port", type=int, action='store',
                        help="port")

    args = parser.parse_args()

    TCP_IP = args.ip
    TCP_PORT = args.port

    if TCP_IP is None:
        raise Exception("-i ip of server was't passed")
    if TCP_PORT is None:
        raise Exception("-p port was't passed ")

    # ---------------- configuration --------------------------
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    # running cmd thread
    cmd_thread = Thread(target=cmd_processing, args=(dc,), daemon=True)
    cmd_thread.start()

    while True:
        # new clients accepting
        conn, addr = s.accept()
        new_client = Client(conn=conn, addr=addr, name="not initialized", thread=None)
        new_client.thread = Thread(target=client_processing,
                                   args=(new_client, dc),
                                   daemon=True)
        dc.mutex.acquire()
        dc.client_list.append(new_client)
        dc.mutex.release()
        new_client.thread.start()


if __name__ == '__main__':
    main()
