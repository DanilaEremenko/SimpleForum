from lib.CommonConstants import BUFFER_SIZE
from lib import PacketProcessor
import socket

TCP_IP = 'localhost'
TCP_PORT = 5005

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

while True:
    text = input("Message: ")

    send_packet = PacketProcessor.get_msg_packet(text)
    s.send(send_packet)

    rec_packet = s.recv(BUFFER_SIZE)
    opcode, data = PacketProcessor.parse_packet(rec_packet)
    print("opcode = %d, data = %s" % (opcode, data))

    if not data:
        continue
    if data == '':
        print("empty data")
        break

s.close()
