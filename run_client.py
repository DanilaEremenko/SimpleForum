from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor
import socket
from threading import Thread
import re
import os
import datetime
import colorama

# ---------------------------- COLORS -----------------------------------
COLOR_DATE = colorama.Fore.YELLOW
COLOR_NAME = colorama.Fore.BLUE
COLOR_TEXT = colorama.Fore.WHITE
COLOR_DEBUG = colorama.Fore.RED
COLOR_SERVER_NAME = colorama.Fore.RED

# ---------------------------- HELP -----------------------------------
HELP_CLIENT = "%s------- AVAILABLE CLIENT COMMANDS --------------\n" \
              "%s/put_topic name\n" \
              "/get_topic_list\n" \
              "/switch_topic num\n" \
              "/help\n" \
              "/exit\n" \
              "%s------------------------------------------------\n" % (
                  colorama.Fore.MAGENTA, colorama.Fore.GREEN, colorama.Fore.MAGENTA)


# ------------------------ PRINTS --------------------------
def debug_print(text):
    print("%sDEBUG:%s" % (COLOR_DEBUG, text))


def msg_print(date, name, text, end="\n"):
    print("\r%s[%s]:%s%s:%s%s " % (COLOR_DATE, date, COLOR_NAME, name, COLOR_TEXT, text), end=end)


def server_msg_print(date, text, end="\n"):
    print("\r%s[%s]:%sSERVER:%s%s " % (COLOR_DATE, date, COLOR_SERVER_NAME, COLOR_TEXT, text), end=end)


def topic_print_all(topic_dict):
    print("\r%s-------- TOPIC LIST FROM SERVER ---------" % colorama.Fore.MAGENTA)
    for topic_i, (topic_name, client_list) in enumerate(zip(topic_dict.keys(), topic_dict.values())):
        print("%s%d:%s%s" % (colorama.Fore.WHITE, topic_i, colorama.Fore.CYAN, topic_name))
        for client_i, client in enumerate(client_list):
            print("\t%s%d:%s%s" % (colorama.Fore.WHITE, client_i, colorama.Fore.CYAN, client))

    print("%s------------------------------------------" % colorama.Fore.MAGENTA)


def help_print():
    print(HELP_CLIENT)


# ------------------------ WRITE --------------------------------
def write_loop(s, connected, name):
    while connected:
        msg_print(date=datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S"), name="You", text="", end="")
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
        rec_packet = s.recv(BUFFER_SIZE)
        opcode, data = PacketProcessor.parse_packet(rec_packet)

        if opcode == PacketProcessor.OP_MSG:
            msg_print(date=data["data"]["date"], name=data["data"]["client_name"], text=data["data"]["text"])

        elif opcode == PacketProcessor.OP_SERVER_MSG:
            server_msg_print(date=data["data"]["date"], text=data["data"]["text"])

        elif opcode == PacketProcessor.OP_MSG_LIST:
            for date, client, text in zip(data["data"]["date"], data["data"]["client"], data["data"]["text"]):
                msg_print(date=date, name=client, text=text)

        elif opcode == PacketProcessor.OP_GET_TOPIC_LIST:
            topic_print_all(data["data"]["topic_dict"])

        elif opcode == PacketProcessor.OP_DISC:
            debug_print("RECEIVED OP_DISC FROM SERVER(%s)" % data["data"]["reason"])
            connected = False
            continue

        else:
            raise Exception("Undefined opcode = %d" % opcode)

        msg_print(date=datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S"), name="You", text="", end="")
    debug_print("\rDISCONNECTION IN READ LOOP")
    os._exit(0)


# ----------------------------------------------------------------
def main():
    TCP_IP = 'localhost'
    TCP_PORT = 5005

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
