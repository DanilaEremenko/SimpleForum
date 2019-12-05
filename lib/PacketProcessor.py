from lib import CommonConstants
from lib import Opcodes
import struct


def parse_packet(packet):
    opcode = struct.unpack("!H", packet[0:2])[0]
    data = str(packet[4:].decode(CommonConstants.CODING))
    return opcode, data


def get_msg_packet(text):
    """
    opcode |  msg.size | msg.buffer
    :param text:
    :return:
    """
    send_format = "!2H%ds" % len(text)
    return struct.pack(send_format.encode(),
                       Opcodes.OP_MSG,
                       len(text),
                       text.encode())
