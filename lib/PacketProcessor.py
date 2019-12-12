from lib import CommonConstants
import struct
import json
import re


# ----------------------------------------------------------------
def parse_packet(packet):
    try:
        opcode = struct.unpack("!H", packet[0:2])[0]
        data = json.loads(str(packet[4:].decode(CommonConstants.CODING)))

    except:
        print("PARSE_PACKET:BAD JSON OR OPCODE")
        opcode = OP_DISC
        data = "DISC"

    return opcode, data


# ----------------------------------------------------------------
OP_MSG = 0


def get_msg_packet(client_name, text):
    json_text = "{\"data\":{\"client_name\":\"%s\",\"text\":\"%s\"}}" % (client_name, text)
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_MSG,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_SERVER_MSG = 10


def get_server_message_packet(text):
    json_text = "{\"data\":\"%s\"}" % (text)
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_SERVER_MSG,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_MSG_LIST = 1  # TODO unused


def get_msg_list_packet(message_list):
    """
    opcode |  msg.size | msg.buffer
    :param text:
    :return:
    """
    data = {"client": [], "date": [], "text": []}
    for message in message_list:
        data["client"].append(message.client_name)
        data["date"].append(message.date.strftime("%Y-%m-%d-%H.%M.%S"))
        data["text"].append(message.text)

    json_text = "{\"data\" : %s}" % re.sub("\'", "\"", (data).__str__())
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_MSG_LIST,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_NEW_TOPIC = 2


def get_new_topic_packet(topic_name):
    json_text = "{\"data\":\"%s\"}" % topic_name
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_NEW_TOPIC,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_GET_TOPIC_LIST = 4


def get_topic_list_request_packet():
    json_text = "{\"data\":\"empty text\"}"
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_GET_TOPIC_LIST,
                       len(json_text),
                       json_text.encode())


def get_topic_list_packet(topic_list: list):
    if len(topic_list) != 0:
        topic_str = "["
        for i, topic in enumerate(topic_list):
            topic_str += "\"%s\"" % topic.title
            if i != len(topic_list) - 1:
                topic_str += ","
        topic_str += "]"
    else:
        topic_str = "NULL"

    json_text = "{\"data\":%s}" % topic_str
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_GET_TOPIC_LIST,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_SWITCH_TOPIC = 3


def get_switch_topic_packet(topic_num):
    json_text = "{\"data\":%d}" % topic_num
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_SWITCH_TOPIC,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_DISC = 5


def get_disc_packet(reason):
    json_text = "{\"data\":\"%s\"}" % reason
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_DISC,
                       len(json_text),
                       json_text.encode())
