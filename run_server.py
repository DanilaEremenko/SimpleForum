from lib.CommonConstants import BUFFER_SIZE
import socket
from lib import PacketProcessor

TCP_IP = 'localhost'
TCP_PORT = 5005

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
conn, addr = s.accept()

print('Connection address:', addr)

while True:
    opcode, data = PacketProcessor.parse_packet(conn.recv(BUFFER_SIZE))

    print("opcode = %d, data = %s" % (opcode, data))
    if not data:
        continue
    if data == '':
        print("empty data")
        break
    send_packet = PacketProcessor.get_msg_packet("Welcome")
    conn.send(send_packet)

conn.close()
