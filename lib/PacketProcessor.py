from lib import CommonConstants
from lib import Opcodes
import struct
import json


# TODO replace name with id in signatures

def parse_packet(packet):
    try:
        opcode = struct.unpack("!H", packet[0:2])[0]
        data = json.loads(str(packet[4:].decode(CommonConstants.CODING)))

    except:
        print("BAD JSON OR OPCODE")
        opcode = Opcodes.OP_DISC
        data = "DISC"

    return opcode, data


def get_msg_packet(client_name, text):
    """
    opcode |  msg.size | msg.buffer
    :param text:
    :return:
    """
    json_text = "{\"client_name\":\"%s\",\"text\":\"%s\"}" % (client_name, text)
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       Opcodes.OP_MSG,
                       len(json_text),
                       json_text.encode())


def get_new_topic_packet(topic_name):
    json_text = "{\"text\":\"%s\"}" % topic_name
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       Opcodes.OP_NEW_TOPIC,
                       len(json_text),
                       json_text.encode())


def get_topic_list_packet():
    json_text = "{\"text\":\"empty text\"}"
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       Opcodes.OP_GET_TOPIC_LIST,
                       len(json_text),
                       json_text.encode())


def get_disc_packet():
    json_text = "{\"text\":\"empty text\"}"
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       Opcodes.OP_DISC,
                       len(json_text),
                       json_text.encode())
