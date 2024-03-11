import json
import socket


def read_json_file(file_path: str) -> dict:
    """ Function to read a json file
        :param file_path: str -> data json file path

        :return json file output
    """
    with open(file_path, "r", encoding="utf-8") as f:
        file = json.load(f)
    return file


def write_json_file(to_write: dict):
    """ Function to read a json file
        :param to_write: str -> data json file path
    """
    with open("datas.json", "w") as f:
        json.dump(to_write, f, indent=4)


def get_self_ip() -> str:
    """ Function to get the IP of the current computer
        :return: str -> IP wanted
    """
    return socket.gethostbyname(socket.gethostname())
