import argparse
import colorama
from datetime import datetime
import os
import re
import socket
from threading import Thread

from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor

# ---------------------------- COLORS -----------------------------------
COLOR_DATE = colorama.Fore.YELLOW
COLOR_NAME = colorama.Fore.BLUE
COLOR_TEXT = colorama.Fore.WHITE
COLOR_DEBUG = colorama.Fore.RED
COLOR_SERVER_NAME = colorama.Fore.RED
COLOR_TOPIC_NAME = colorama.Fore.CYAN
COLOR_DIV_LINES = colorama.Fore.MAGENTA
COLOR_COMMAND = colorama.Fore.GREEN
COLOR_INDEX = colorama.Fore.WHITE

# ---------------------------- HELP -----------------------------------
HELP_CLIENT = "%s------- AVAILABLE CLIENT COMMANDS --------------\n" \
              "%s/put_topic name\n" \
              "/get_topic_list\n" \
              "/switch_topic num\n" \
              "/help\n" \
              "/exit\n" \
              "%s------------------------------------------------\n%s" % \
              (COLOR_DIV_LINES, COLOR_COMMAND, COLOR_DIV_LINES, colorama.Fore.RESET)


# ------------------------ PRINTS --------------------------
def debug_print(text):
    print("%sDEBUG:%s" % (COLOR_DEBUG, text))


def msg_print(date, name, text, end="\n"):
    print("\r%s[%s]:%s%s:%s%s " % (COLOR_DATE, date, COLOR_NAME, name, COLOR_TEXT, text), end=end)


def server_msg_print(date, text, end="\n"):
    print("\r%s[%s]:%sSERVER:%s%s " % (COLOR_DATE, date, COLOR_SERVER_NAME, COLOR_TEXT, text), end=end)


def topic_print_all(topic_dict):
    print("\r%s-------- TOPIC LIST FROM SERVER ---------" % COLOR_DIV_LINES)
    for topic_i, (topic_name, client_list) in enumerate(zip(topic_dict.keys(), topic_dict.values())):
        print("%s%d:%s%s" % (COLOR_INDEX, topic_i, COLOR_TOPIC_NAME, topic_name))
        for client_i, client_name in enumerate(client_list):
            print("\t%s%d:%s%s" % (COLOR_INDEX, client_i, COLOR_NAME, client_name))

    print("%s------------------------------------------" % COLOR_DIV_LINES)


def help_print():
    print(HELP_CLIENT)


# ------------------------ WRITE --------------------------------
def write_loop(s, connected, name):
    while connected:
        msg_print(date=datetime.now().strftime("%Y-%m-%d-%H.%M.%S"), name="You", text="", end="")
        text = input()

        splited_text = re.sub(" +", " ", text).split(" ")

        if text == "":  # don't send empty message
            continue

        elif text[0] == "/":  # check commands
            if splited_text[0] == '/put_topic' and len(splited_text) == 2:
                send_packet = PacketProcessor.get_new_topic_packet(splited_text[1])
                debug_print("NEW TOPIC PACKET SENDING")

            elif splited_text[0] == "/get_topic_list":
                send_packet = PacketProcessor.get_topic_list_request_packet()
                debug_print("GET TOPIC LIST PACKET SENDING (OP = %d)" %
                            PacketProcessor.parse_packet(send_packet)[0])

            elif splited_text[0] == "/switch_topic" and len(splited_text) == 2:
                topic_num = int(splited_text[1])
                send_packet = PacketProcessor.get_switch_topic_packet(topic_num=topic_num)
                debug_print("TRYING TO SWITCH TOPIC TO %d (OP = %d)" %
                            (topic_num, PacketProcessor.parse_packet(send_packet)[0]))
            elif splited_text[0] == "/help":
                help_print()
                continue

            elif splited_text[0] == '/exit':
                send_packet = PacketProcessor.get_disc_packet("EXIT COMMAND GOT")
                connected = False
                debug_print("EXIT PACKET SENDING (OP = %d)" %
                            PacketProcessor.parse_packet(send_packet)[0])

            else:
                debug_print("BAD COMMAND, NO PACKET SENDING")
                continue

        else:  # just send text message
            send_packet = PacketProcessor.get_msg_packet(client_name=name, text=text)

        s.send(send_packet)
    debug_print("\rDISCONNECTION IN WRITE LOOP")
    os._exit(0)


# ------------------------- READ -------------------------------
def read_loop(s, connected):
    while connected:
        opcode, data = PacketProcessor.parse_packet(s.recv(BUFFER_SIZE))

        if opcode == PacketProcessor.OP_MSG:
            msg_print(date=data["data"]["date"], name=data["data"]["client_name"], text=data["data"]["text"])

        elif opcode == PacketProcessor.OP_SERVER_MSG:
            server_msg_print(date=data["data"]["date"], text=data["data"]["text"])

        elif opcode == PacketProcessor.OP_MSG_LIST:
            for date, client_name, text in zip(data["data"]["date"], data["data"]["client_name"], data["data"]["text"]):
                msg_print(date=date, name=client_name, text=text)

        elif opcode == PacketProcessor.OP_GET_TOPIC_LIST:
            topic_print_all(data["data"]["topic_dict"])

        elif opcode == PacketProcessor.OP_DISC:
            debug_print("RECEIVED OP_DISC FROM SERVER(%s)" % data["data"]["reason"])
            connected = False
            continue

        else:
            raise Exception("Undefined opcode = %d" % opcode)

        msg_print(date=datetime.now().strftime("%Y-%m-%d-%H.%M.%S"), name="You", text="", end="")
    debug_print("\rDISCONNECTION IN READ LOOP")
    os._exit(0)


# ----------------------------------------------------------------
def main():
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
    s.connect((TCP_IP, TCP_PORT))

    # Authorization
    name = input("Print your name: ")
    send_packet = PacketProcessor.get_msg_packet(client_name=name, text=name)
    s.send(send_packet)

    help_print()

    connected = True
    # using threads
    read_thread = Thread(target=read_loop, args=(s, connected), daemon=True)
    write_thread = Thread(target=write_loop, args=(s, connected, name), daemon=True)

    read_thread.start()
    write_thread.start()

    read_thread.join()
    write_thread.join()


if __name__ == '__main__':
    main()
