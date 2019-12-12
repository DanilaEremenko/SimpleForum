from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor
import socket
from threading import Thread
import re
import os


def debug_print(text):
    print("DEBUG:%s" % text)


# ----------------------------------------------------------------
def write_loop(s, connected, name):
    while connected:
        text = input("Your message: ")
        splited_text = re.sub(" +", " ", text).split(" ")

        if text == "":  # don't send empty message
            continue

        elif len(splited_text) >= 2 and splited_text[0] == 'command':  # check commands
            if splited_text[1] == 'put_topic' and len(splited_text) == 3:
                send_packet = PacketProcessor.get_new_topic_packet(splited_text[2])
                debug_print("NEW TOPIC PACKET SENDING")

            elif splited_text[1] == "get_topic_list":
                send_packet = PacketProcessor.get_topic_list_request_packet()
                debug_print("GET TOPIC LIST PACKET SENDING (OP = %d)" %
                            PacketProcessor.parse_packet(send_packet)[0])

            elif splited_text[1] == "switch_topic" and len(splited_text) == 3:
                topic_num = int(splited_text[2])
                send_packet = PacketProcessor.get_switch_topic_packet(topic_num=topic_num)
                debug_print("TRYING TO SWITCH TOPIC TO %d (OP = %d)" %
                            (topic_num, PacketProcessor.parse_packet(send_packet)[0]))

            elif splited_text[1] == 'exit':
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
    print("\rDISCONNECTION IN WRITE LOOP")
    os._exit(0)


# ----------------------------------------------------------------
def read_loop(s, connected):
    while connected:
        rec_packet = s.recv(BUFFER_SIZE)
        opcode, data = PacketProcessor.parse_packet(rec_packet)

        if opcode == PacketProcessor.OP_MSG:
            print("\r%s: %s" % (data["data"]["client_name"], data["data"]["text"]), flush=True)

        elif opcode == PacketProcessor.OP_SERVER_MSG:
            print("\rSERVER: %s" % (data["data"]), flush=True)

        elif opcode == PacketProcessor.OP_MSG_LIST:
            for date, client, text in zip(data["data"]["date"], data["data"]["client"], data["data"]["text"]):
                print("\r[%s]:%s:%s" % (date, client, text), flush=True)

        elif opcode == PacketProcessor.OP_GET_TOPIC_LIST:
            print("\r-------- TOPIC LIST FROM SERVER---------")
            if data["data"] != "NULL":
                for i, topic_name in enumerate(data["data"]):
                    print("%d:%s" % (i, topic_name))
            print("------------------------------------------")

        elif opcode == PacketProcessor.OP_DISC:
            print("RECEIVED OP_DISC FROM SERVER(%s)") % data["data"]
            connected = False

        else:
            raise Exception("Undefined opcode = %d" % opcode)

        print("Your message: ", end="", flush=True)
    print("\rDISCONNECTION IN READ LOOP")
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
