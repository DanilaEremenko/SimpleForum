from datetime import datetime
import re
import struct
import json

from lib import CommonConstants


# ----------------------------------------------------------------
def parse_packet(packet):
    opcode = -1
    try:
        opcode = struct.unpack("!H", packet[0:2])[0]
        data = json.loads(str(packet[4:].decode(CommonConstants.CODING)))

    except:
        print("PARSE_PACKET:BAD JSON(OPCODE = %d\nJSON = %s" % (opcode, str(packet[4:].decode(CommonConstants.CODING))))
        opcode = OP_DISC
        data = {"data": {"reason": "BAD PARSING"}}

    return opcode, data


# ----------------------------------------------------------------
OP_MSG = 0


def get_msg_packet(client_name, text):
    json_text = json.dumps(
        {"data": {"client_name": client_name, "text": text, "date": datetime.now().strftime("%Y-%m-%d-%H.%M.%S")}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_MSG,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_SERVER_MSG = 10


def get_server_message_packet(text):
    json_text = json.dumps({"data": {"text": text, "date": datetime.now().strftime("%Y-%m-%d-%H.%M.%S")}})
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
    data = {"client_name": [], "date": [], "text": []}
    for message in message_list:
        data["client_name"].append(message.client_name)
        data["date"].append(message.date.strftime("%Y-%m-%d-%H.%M.%S"))
        data["text"].append(message.text)

    json_text = json.dumps({"data": data})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_MSG_LIST,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_NEW_TOPIC = 2


def get_new_topic_packet(topic_name):
    json_text = json.dumps({"data": {"topic_name": topic_name}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_NEW_TOPIC,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_GET_TOPIC_LIST = 4


def get_topic_list_request_packet():
    json_text = json.dumps({"data": {"empty": "empty"}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_GET_TOPIC_LIST,
                       len(json_text),
                       json_text.encode())


def get_topic_dict(topic_list: list):
    topic_dict = {}
    if len(topic_list) != 0:
        for i, topic in enumerate(topic_list):
            client_list = []
            for j, client in enumerate(topic.client_list):
                client_list.append(client.name)
            topic_dict[topic.title] = client_list
    return topic_dict


def get_topic_list_packet(topic_list: list):
    topic_dict = get_topic_dict(topic_list)
    json_text = json.dumps({"data": {"topic_dict": topic_dict}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_GET_TOPIC_LIST,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_SWITCH_TOPIC = 3


def get_switch_topic_packet(topic_num):
    json_text = json.dumps({"data": {"topic_i": topic_num}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_SWITCH_TOPIC,
                       len(json_text),
                       json_text.encode())


# ----------------------------------------------------------------
OP_DISC = 5


def get_disc_packet(reason):
    json_text = json.dumps({"data": {"reason": reason}})
    send_format = "!2H%ds" % len(json_text)
    return struct.pack(send_format.encode(),
                       OP_DISC,
                       len(json_text),
                       json_text.encode())
