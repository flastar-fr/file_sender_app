import math
import os
import socket
import re
import customtkinter
import threading
from uuid import getnode
from tkinter.filedialog import askopenfilename, askopenfilenames
from CTkMessagebox import CTkMessagebox
from datas_extraction import read_json_file, get_self_ip, write_json_file


customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")
BUFFER_SIZE = 4096
exit_event = threading.Event()


def start_thread(to_execute: ..., *args: ...):
    """ Function to execute a thread
        :param to_execute: ... -> object to execute in the new thread
        :param args: Any -> arguments to pass
    """
    thread = threading.Thread(target=to_execute, args=args)
    thread.daemon = True
    thread.start()


def try_to_connect(s: socket.socket, host: str, port: int) -> bool:
    """ Function to test to connect to another device
        :param s: socket -> socket to try connection
        :param host: str -> IP to connect
        :param port: int -> port to connect

        :return: bool -> True if the connection is working, otherwise False
    """
    try:
        s.connect((host, port))
        return True
    except ConnectionRefusedError:
        return False
    except TimeoutError:
        return False


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        os.chdir(dname)

        self.check_json_file()

        self.datas: dict[str: dict[str: str]] = read_json_file("datas.json")

        self.title("File Sender app")
        self.geometry(f"{450}x{290}")
        self.resizable(False, False)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        tabview = customtkinter.CTkTabview(self)
        tabview.add("Send")
        tabview.add("Receive")
        tabview.add("Add/Delete PC")
        tabview.add("+")
        tabview.pack(expand=True, fill="both", padx=10, pady=(0, 10))

        # send tab
        frame_send = customtkinter.CTkFrame(tabview.tab("Send"))
        frame_send.pack()
        label_ip = customtkinter.CTkLabel(frame_send, text="Select PC : ")
        label_ip.grid(row=0, column=0)
        vals = list(self.datas["look"].keys())
        self._option_ip = customtkinter.CTkOptionMenu(frame_send, values=vals if len(vals) != 0 else ["NoRegistered"])
        self._option_ip.grid(row=0, column=1, padx=20, pady=5)
        label_file = customtkinter.CTkLabel(frame_send, text="File Path : ")
        label_file.grid(row=2, column=0)
        self._folder = customtkinter.StringVar()
        self._entry_file = customtkinter.CTkEntry(frame_send, textvariable=self._folder)
        self._entry_file.grid(row=2, column=1, padx=20, pady=5)
        button_file = customtkinter.CTkButton(frame_send, text="Browse", command=self.select_folder)
        button_file.grid(row=2, column=2, padx=20, pady=5)

        button_start_send = customtkinter.CTkButton(tabview.tab("Send"), text="Start sending",
                                                    command=lambda: start_thread(self.start_sending))
        button_start_send.pack(pady=20)
        self._progress_bar_send = customtkinter.CTkProgressBar(tabview.tab("Send"), mode="determinate")
        self._progress_bar_send.set(0)
        self._progress_bar_send.configure(progress_color="#1ba62b")
        self._progress_bar_send.pack()
        button_stop_receive = customtkinter.CTkButton(tabview.tab("Send"), text="Stop sending",
                                                      command=lambda: exit_event.set())
        button_stop_receive.pack(pady=20)

        # receive tab
        button_start_receive = customtkinter.CTkButton(tabview.tab("Receive"), text="Start receiving",
                                                       command=lambda: start_thread(self.start_receiving))
        button_start_receive.pack(pady=20, anchor="n")
        self._progress_bar_receive = customtkinter.CTkProgressBar(tabview.tab("Receive"), mode="determinate")
        self._progress_bar_receive.set(0)
        self._progress_bar_receive.configure(progress_color="#1ba62b")
        self._progress_bar_receive.pack()
        button_stop_receive = customtkinter.CTkButton(tabview.tab("Receive"), text="Stop receiving",
                                                      command=lambda: exit_event.set())
        button_stop_receive.pack(pady=20, anchor="center")

        # add and delete PC tab
        label_add = customtkinter.CTkLabel(tabview.tab("Add/Delete PC"), text="Add")
        label_add.pack()
        frame_add = customtkinter.CTkFrame(tabview.tab("Add/Delete PC"))
        frame_add.pack()
        button_add_self = customtkinter.CTkButton(frame_add, text="Add self PC", command=lambda: self.add_current_pc())
        button_add_self.pack()
        button_add_new = customtkinter.CTkButton(frame_add, text="Add other PC", command=lambda: self.add_new_pc())
        button_add_new.pack(pady=10)

        label_delete = customtkinter.CTkLabel(tabview.tab("Add/Delete PC"), text="Delete")
        label_delete.pack()
        frame_delete = customtkinter.CTkFrame(tabview.tab("Add/Delete PC"))
        frame_delete.pack()
        self._option_ip_del = customtkinter.CTkOptionMenu(frame_delete,
                                                          values=vals if len(vals) != 0 else ["NoRegistered"])
        self._option_ip_del.grid(row=0, column=0, padx=(0, 10))
        button_del = customtkinter.CTkButton(frame_delete, text="Delete", command=lambda: self.delete_pc())
        button_del.grid(row=0, column=1)

        # + tab
        self._progress_bar_multiple = customtkinter.CTkProgressBar(tabview.tab("+"), mode="determinate")
        self._progress_bar_multiple.set(0)
        self._progress_bar_multiple.configure(progress_color="#1ba62b")
        self._progress_bar_multiple.pack()
        label_multiple_send = customtkinter.CTkLabel(tabview.tab("+"), text="Send Multiple Files")
        label_multiple_send.pack(pady=10)
        # multiple send
        frame_multiple_send = customtkinter.CTkFrame(tabview.tab("+"))
        frame_multiple_send.pack()
        vals = list(self.datas["look"].keys())
        self._option_ip_m = customtkinter.CTkOptionMenu(frame_multiple_send,
                                                        values=vals if len(vals) != 0 else ["NoRegistered"])
        self._option_ip_m.grid(row=0, column=0, padx=20, pady=5)
        button_send_multiple = customtkinter.CTkButton(frame_multiple_send, text="Send files",
                                                       command=lambda: start_thread(self.send_multiple_files))
        button_send_multiple.grid(row=0, column=1)

        # multiple receive
        label_multiple_receive = customtkinter.CTkLabel(tabview.tab("+"), text="Receive Multiple Files")
        label_multiple_receive.pack()
        button_receive_multiple = customtkinter.CTkButton(tabview.tab("+"), text="Receive Files",
                                                          command=lambda: start_thread(self.receive_multiple_files))
        button_receive_multiple.pack(pady=(5, 10))
        button_stop_multiple = customtkinter.CTkButton(tabview.tab("+"), text="Stop Running",
                                                       command=lambda: exit_event.set())
        button_stop_multiple.pack(pady=10)

        super().mainloop()

    def check_json_file(self):
        """ Method to check if the datas.json file exists otherwise creates it """
        if not os.path.exists("datas.json"):
            write_json_file({"ip": {}, "look": {}})
            CTkMessagebox(self, title="File added", message="datas.json file successfully added", icon="check")

    def select_folder(self):
        """ Method to select the folder path and change the needed entry """
        folder_path = askopenfilename(title="Select file")
        if folder_path != "":
            self._folder.set(folder_path)

    def add_current_pc(self):
        """ Method to add the current selected computer """
        mac_adress = str(getnode())
        current_ip = get_self_ip()
        if mac_adress in self.datas["ip"].keys():
            self.datas["ip"][mac_adress] = current_ip
            write_json_file(self.datas)
            return None

        current_ip = get_self_ip()

        pc_name = customtkinter.CTkInputDialog(title="Enter", text="Please, enter a name for your computer")

        self.datas["ip"][mac_adress] = current_ip
        self.datas["look"][pc_name.get_input()] = mac_adress
        write_json_file(self.datas)

        self._refresh_options_values()

    def add_new_pc(self):
        """ Method to add a new computer """
        # name
        pc_name = customtkinter.CTkInputDialog(title="Enter", text="Please, enter a name for your computer")
        pc_name_val = pc_name.get_input()
        if pc_name_val is None:
            CTkMessagebox(self, title="Error", message="Invalid name", icon="cancel")
            return None

        # ip
        pc_ip = customtkinter.CTkInputDialog(title="Enter", text="Please, enter the IP you want to add")
        pc_ip_val = pc_ip.get_input()
        if pc_ip_val is None:
            CTkMessagebox(self, title="Error", message="Invalid name", icon="cancel")
            return None
        if not re.search(r'^\d+.\d+.\d+.\d+$', pc_ip_val):
            CTkMessagebox(self, title="Error", message="IP doesn't follow the IPv4 format", icon="cancel")
            return None

        mac_adress = getnode()
        self.datas["ip"][mac_adress] = pc_ip_val
        self.datas["look"][pc_name_val] = mac_adress
        write_json_file(self.datas)

        self._refresh_options_values()

    def delete_pc(self):
        """ Method to delete a PC from the datas.json file """
        to_delete = self._option_ip_del.get()
        mac_adress = str(self.datas["look"][to_delete])
        self.datas["look"].pop(to_delete)
        self.datas["ip"].pop(mac_adress)
        write_json_file(self.datas)

        self._refresh_options_values()

    def _refresh_options_values(self):
        """ Method to update with the new datas the option menus """
        values = list(self.datas["look"].keys())
        self._option_ip_del.configure(values=values)
        self._option_ip.configure(values=list(self.datas["look"].keys()))
        self._option_ip_del.set(values[-1] if len(values) != 0 else "NoRegistered")
        self._option_ip_m.set(values[-1] if len(values) != 0 else "NoRegistered")

    def send_multiple_files(self):
        """ Method to send multiple files """
        self._progress_bar_multiple.set(0)

        files = askopenfilenames()
        if files == "":
            return None

        val_string = self._option_ip_m.get()
        host: str = self.datas["ip"][self.datas["look"][val_string]]
        s = socket.socket()

        # inputs verification
        assert re.search(r'^\d+.\d+.\d+.\d+$', host), "IP adress does not match"

        if not try_to_connect(s, host, 4711):
            CTkMessagebox(self, title="Error", message="Connection refused", icon="cancel")
            return None

        files_size = sum([os.path.getsize(file) for file in files])
        total_bytes = 0

        s.send(str(files_size).encode() + b'|')
        s.send(str(len(files)).encode() + b'|')

        for file in files:
            # initialized sending
            file_name = os.path.basename(file)

            s.send(file_name.encode())

        # send a delimiter to indicate the end of file names
        s.send(b"END_OF_FILE_NAMES")

        # sending
        for file in files:
            with open(file, "rb") as f:
                while True:
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:  # if file is fully readen
                        break
                    if exit_event.is_set():  # if user wants to cancel
                        break
                    s.send(bytes_read)
                    total_bytes += len(bytes_read)
                    self._progress_bar_multiple.set(math.ceil(total_bytes / files_size * 100)/100)

                if exit_event.is_set():
                    break

        if exit_event.is_set():
            exit_event.clear()
            CTkMessagebox(self, title="Cancel", message="Sending successfully canceled", icon="check")
        else:
            s.close()
            CTkMessagebox(self, title="Complete", message="Sending complete", icon="check")

    def receive_multiple_files(self):
        """ Method to receive multiple files """
        self._progress_bar_multiple.set(0)

        # socket initialization
        adresse = ""
        port = 4711
        s = socket.socket()
        s.bind((adresse, port))

        s.listen(1)

        client_socket, client_address = s.accept()

        # verify if the adress is in selectable adresses
        if client_address[0] not in self.datas["ip"].values():
            CTkMessagebox(self, title="Error", message="Connection refused, IP not registered", icon="cancel")
            return None

        # size
        total_bytes = 0
        file_size_bytes = ''.encode()
        while True:
            chunk = client_socket.recv(1)
            if chunk == '|'.encode():
                break
            file_size_bytes += chunk
        file_size = int(file_size_bytes)

        total_file_bytes = ''.encode()
        while True:
            chunk = client_socket.recv(1)
            if chunk == '|'.encode():
                break
            total_file_bytes += chunk
        total_files = int(total_file_bytes)

        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")

        # receiving
        file_names = []
        while True:
            filename = client_socket.recv(BUFFER_SIZE).decode()
            if filename == "END_OF_FILE_NAMES":
                break
            file_names.append(filename)

        for i in range(int(total_files)):
            # get final path
            # filename = client_socket.recv(BUFFER_SIZE)
            filepath = os.path.join(downloads_folder, file_names[i])

            with open(filepath, 'wb') as f:
                while True:
                    datas = client_socket.recv(BUFFER_SIZE)
                    if not datas:  # if file is fully readen
                        break
                    if exit_event.is_set():  # if user wants to cancel
                        break
                    f.write(datas)
                    total_bytes += len(datas)
                    self._progress_bar_multiple.set(math.ceil(total_bytes / int(file_size) * 100)/100)

                if exit_event.is_set():
                    break

        if exit_event.is_set():
            CTkMessagebox(self, title="Cancel", message="Receiving successfully canceled", icon="check")
            exit_event.clear()
        else:
            CTkMessagebox(self, title="Complete", message="Receiving complete", icon="check")
            client_socket.close()
            s.close()

    def start_sending(self):
        """ Method to start sending the file """
        self._progress_bar_send.set(0)

        # inputs selection
        val_string = self._option_ip_m.get()
        mac_adress = str(self.datas["look"][val_string])
        host: str = self.datas["ip"][mac_adress]
        file_path: str = self._entry_file.get()
        s = socket.socket()

        # inputs verification
        assert re.search(r'^\d+.\d+.\d+.\d+$', host), "IP adress does not match"

        if not os.path.exists(file_path):
            CTkMessagebox(self, title="Error", message="File does not exist", icon="cancel")
            return None

        if not try_to_connect(s, host, 4711):
            CTkMessagebox(self, title="Error", message="Connection refused", icon="cancel")
            return None

        # initialized sending
        total_bytes = 0
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        s.send(file_name.encode())
        s.send(str(file_size).encode())

        # sending
        with open(file_path, "rb") as f:
            while True:
                try:  # case receiving is canceled on other computer
                    bytes_read = f.read(BUFFER_SIZE)
                except ConnectionResetError:
                    CTkMessagebox(self, title="Cancel", message="Receiving canceled", icon="cancel")
                if not bytes_read:  # if file is fully readen
                    s.close()
                    CTkMessagebox(self, title="Complete", message="Sending complete", icon="check")
                    break
                if exit_event.is_set():  # if user wants to cancel
                    CTkMessagebox(self, title="Cancel", message="Sending successfully canceled", icon="check")
                    exit_event.clear()
                    break
                s.send(bytes_read)
                total_bytes += len(bytes_read)
                self._progress_bar_send.set(math.ceil(total_bytes / file_size * 100)/100)

    def start_receiving(self):
        """ Method to start receiving the file """
        self._progress_bar_receive.set(0)

        # socket initialization
        adresse = ""
        port = 4711
        s = socket.socket()
        s.bind((adresse, port))

        s.listen(1)

        client_socket, client_address = s.accept()

        # verify if the adress is in selectable adresses
        if client_address[0] not in self.datas["ip"].values():
            CTkMessagebox(self, title="Error", message="Connection refused, IP not registered", icon="cancel")
            return None

        # get final path
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        filename = client_socket.recv(BUFFER_SIZE).decode()
        filepath = os.path.join(downloads_folder, filename)

        # size
        file_size = int(client_socket.recv(BUFFER_SIZE).decode())
        total_bytes = 0

        # receiving
        with open(filepath, 'wb') as f:
            while True:
                datas = client_socket.recv(BUFFER_SIZE)
                if not datas:  # if file is fully readen
                    client_socket.close()
                    s.close()
                    CTkMessagebox(self, title="Complete", message="Receiving complete", icon="check")
                    break
                if exit_event.is_set():  # if user wants to cancel
                    CTkMessagebox(self, title="Cancel", message="Receiving successfully canceled", icon="check")
                    exit_event.clear()
                    break
                f.write(datas)
                total_bytes += len(datas)
                self._progress_bar_receive.set(math.ceil(total_bytes / file_size * 100)/100)


if __name__ == "__main__":
    a = App()
    exit_event.set()
