from lib import CommonConstants
from lib import Opcodes
import struct
import json


def parse_packet(packet):
    try:
        opcode = struct.unpack("!H", packet[0:2])[0]
        data = json.loads(str(packet[4:].decode(CommonConstants.CODING)))

    except:
        opcode = Opcodes.OP_DISC
        data = "DISC"

    return opcode, data


def get_msg_packet(client_name, text):
    """
    opcode |  msg.size | msg.buffer
    :param text:
    :return:
    """
    json_text = "{\"client_name\": \"%s\", \"text\":\"%s\"}" % (client_name, text)
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       Opcodes.OP_MSG,
                       len(json_text),
                       json_text.encode())


def get_msg_disc():
    send_format = "!1H"
    return struct.pack(send_format.encode(), Opcodes.OP_DISC)
