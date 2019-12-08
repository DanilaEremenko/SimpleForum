from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor
import socket
from threading import Thread
from lib import Opcodes


def write_loop(s, connected, name):
    while connected:
        text = input("Your message: ")
        if text == 'exit':
            send_packet = PacketProcessor.get_msg_disc()
            connected = False
        elif text == "":
            continue
        else:
            send_packet = PacketProcessor.get_msg_packet(client_name=name, text=text)
        s.send(send_packet)
    print("\rDISCONNECTION IN WRITE LOOP")
    exit(0)


def read_loop(s, connected):
    while connected:
        rec_packet = s.recv(BUFFER_SIZE)
        opcode, data = PacketProcessor.parse_packet(rec_packet)

        if opcode == Opcodes.OP_MSG:
            print("\r%s: %s\nYour message: " % (data["client_name"], data["text"]), flush=True, end="")

        elif opcode == Opcodes.OP_DISC:
            connected = False

    print("\rDISCONNECTION IN READ LOOP")
    exit(0)


if __name__ == '__main__':
    TCP_IP = 'localhost'
    TCP_PORT = 5005

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))

    # Authorization
    name = input("Print your name: ")
    send_packet = PacketProcessor.get_msg_packet(client_name=name, text="text")
    s.send(send_packet)

    connected = True
    # using threads
    read_thread = Thread(target=read_loop, args=(s, connected), daemon=True)
    write_thread = Thread(target=write_loop, args=(s, connected, name), daemon=True)

    read_thread.start()
    write_thread.start()

    read_thread.join()
    write_thread.join()
