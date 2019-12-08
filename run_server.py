from lib.CommonConstants import BUFFER_SIZE
import socket
from lib import PacketProcessor
from lib import Opcodes
from threading import Thread, Lock


class Client():
    def __init__(self, conn, addr, name, thread):
        self.conn = conn
        self.addr = addr
        self.name = name
        self.is_connected = False
        self.thread = thread


def remove_client(client, client_list: list):
    print("DISCONNECTING:Client = %s" % client.name)
    send_packet = PacketProcessor.get_msg_disc()
    client.conn.send(send_packet)
    client.is_connected = False
    client_list.remove(client)
    client.conn.close()


def client_processing(client: Client, client_list, mutex):
    client.is_connected = True
    print("New client = %s(%d) accepted" % (client.name, client.conn.fileno()))
    while client.is_connected:
        opcode, data = PacketProcessor.parse_packet(client.conn.recv(BUFFER_SIZE))

        if opcode == Opcodes.OP_MSG:

            if not data or data == '':
                remove_client(client, client_list)
            else:
                print("--------------\nMSG from %s: %s" % (client.name, data["text"]))

                send_packet = PacketProcessor.get_msg_packet(client_name=client.name, text=data["text"])

                mutex.acquire()
                for other_client in client_list:
                    if other_client != client:
                        print("RESENDING TO %s" % other_client.name)
                        other_client.conn.send(send_packet)
                mutex.release()

        elif opcode == Opcodes.OP_DISC:
            remove_client(client, client_list)

        else:
            raise Exception("Undefined opcode = %d" % opcode)

    print("DISCONNECTED:Client = %s" % client.name)


def cmd_processing(client_list):
    while True:
        command = input()
        print("-------------------------")
        if command == "list":
            for i, client in enumerate(client_list):
                print("%d:%s" % (i, client.name))

        print("-------------------------")


def main():
    client_list = []

    TCP_IP = 'localhost'
    TCP_PORT = 5005

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    mutex = Lock()

    # running cmd thread
    cmd_thread = Thread(target=cmd_processing, args=(client_list,), daemon=True)
    cmd_thread.start()

    while True:
        # new clients accepting
        conn, addr = s.accept()
        opcode, data = PacketProcessor.parse_packet(conn.recv(BUFFER_SIZE))
        if opcode == Opcodes.OP_MSG:
            name = data["client_name"]
            new_client = Client(conn=conn, addr=addr, name=name, thread=None)
            new_client.thread = Thread(target=client_processing, args=(new_client, client_list, mutex), daemon=True)

            mutex.acquire()
            client_list.append(new_client)
            mutex.release()

            new_client.thread.start()

        else:
            print("opcode = %d (%d awaiting)" % (opcode, Opcodes.OP_MSG))


if __name__ == '__main__':
    main()
