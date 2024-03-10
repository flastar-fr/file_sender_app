import json
import socket


def read_json_file(file_path: str) -> {}:
    """ Function to read a json file
        :param file_path: str -> data json file path

        :return json file output
    """
    with open(file_path, "r", encoding="utf-8") as file_reader:
        file = json.load(file_reader)
    return file


def get_self_ip() -> str:
    return socket.gethostbyname(socket.gethostname())
