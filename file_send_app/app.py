import math
import os
import socket
import re
import customtkinter
import threading
from tkinter.filedialog import askopenfilename
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

        self.datas: dict[str: dict[str: str]] = read_json_file("datas.json")

        ips = self.datas["ip"]
        ips = {name: ip for name, ip in ips.items() if ip != get_self_ip()}

        self.title("File Sender app")
        self.geometry(f"{450}x{290}")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        tabview = customtkinter.CTkTabview(self)
        tabview.add("Send")
        tabview.add("Receive")
        tabview.add("Add/Delete PC")
        tabview.pack(expand=True, fill="both", padx=10, pady=(0, 10))

        # send tab
        frame_send = customtkinter.CTkFrame(tabview.tab("Send"))
        frame_send.pack()
        label_ip = customtkinter.CTkLabel(frame_send, text="Select PC : ")
        label_ip.grid(row=0, column=0)
        values = [key for key in ips.keys()]
        self._option_ip = customtkinter.CTkOptionMenu(frame_send, values=values)
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
        self._progress_bar_receive.configure(progress_color="#158f24")
        self._progress_bar_receive.pack()
        button_stop_receive = customtkinter.CTkButton(tabview.tab("Receive"), text="Stop receiving",
                                                      command=lambda: exit_event.set())
        button_stop_receive.pack(pady=20, anchor="center")

        # add and delete PC tab
        label_add = customtkinter.CTkLabel(tabview.tab("Add/Delete PC"), text="Add :")
        label_add.pack()
        frame_add = customtkinter.CTkFrame(tabview.tab("Add/Delete PC"))
        frame_add.pack()
        button_add_self = customtkinter.CTkButton(frame_add, text="Add self PC", command=lambda: self.add_current_pc())
        button_add_self.pack()
        button_add_new = customtkinter.CTkButton(frame_add, text="Add other PC", command=lambda: self.add_new_pc())
        button_add_new.pack(pady=10)

        label_delete = customtkinter.CTkLabel(tabview.tab("Add/Delete PC"), text="Delete :")
        label_delete.pack()
        frame_delete = customtkinter.CTkFrame(tabview.tab("Add/Delete PC"))
        frame_delete.pack()
        self._option_ip_del = customtkinter.CTkOptionMenu(frame_delete, values=[key for key in self.datas["ip"].keys()])
        self._option_ip_del.grid(row=0, column=0, padx=(0, 10))
        button_del = customtkinter.CTkButton(frame_delete, text="Delete", command=lambda: self.delete_pc())
        button_del.grid(row=0, column=1)

        super().mainloop()

    def select_folder(self):
        """ Method to select the folder path and change the needed entry """
        folder_path = askopenfilename(title="Select file")
        if folder_path != "":
            self._folder.set(folder_path)

    def add_current_pc(self):
        """ Method to add the current selected computer """
        current_ip = get_self_ip()

        if current_ip in self.datas["ip"].values():
            return None

        pc_name = customtkinter.CTkInputDialog(title="Enter", text="Please, enter a name for your computer")

        self.datas["ip"][pc_name.get_input()] = current_ip
        write_json_file(self.datas)

        self._option_ip_del.configure(values=[key for key in self.datas["ip"].keys()])
        self._option_ip.configure(values=[key for key, val in self.datas["ip"].items() if val != get_self_ip()])

    def add_new_pc(self):
        """ Method to add a new computer """
        pc_name = customtkinter.CTkInputDialog(title="Enter", text="Please, enter a name for your computer")
        pc_ip = customtkinter.CTkInputDialog(title="Enter", text="Please, enter the IP you want to add")

        if pc_ip.get_input() in self.datas["ip"].values():
            return None

        self.datas["ip"][pc_name.get_input()] = pc_ip.get_input()
        write_json_file(self.datas)

        self._option_ip_del.configure(values=[key for key in self.datas["ip"].keys()])
        self._option_ip.configure(values=[key for key, val in self.datas["ip"].items() if val != get_self_ip()])

    def delete_pc(self):
        to_delete = self._option_ip_del.get()
        self.datas["ip"].pop(to_delete)
        write_json_file(self.datas)

        self._option_ip_del.configure(values=[key for key in self.datas["ip"].keys()])
        self._option_ip.configure(values=[key for key, val in self.datas["ip"].items() if val != get_self_ip()])

    def start_sending(self):
        """ Method to start sending the file """
        # inputs selection
        host: str = self.datas["ip"][self._option_ip.get()]
        file_path: str = self._entry_file.get()
        s = socket.socket()

        # inputs verification
        assert re.search(r'^\d+.\d+.\d+.\d+$', host), "IP adress does not match"

        if not os.path.exists(file_path):
            CTkMessagebox(title="Error", message="File does not exist", icon="cancel")
            return None

        if not try_to_connect(s, host, 4711):
            CTkMessagebox(title="Error", message="Connection refused", icon="cancel")
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
                try:    # case receiving is canceled on other computer
                    bytes_read = f.read(BUFFER_SIZE)
                except ConnectionResetError:
                    CTkMessagebox(title="Cancel", message="Receiving canceled", icon="cancel")
                if not bytes_read:      # if file is fully readen
                    s.close()
                    CTkMessagebox(title="Complete", message="Sending complete", icon="check")
                    break
                if exit_event.is_set():  # if user wants to cancel
                    CTkMessagebox(title="Cancel", message="Sending successfully canceled", icon="check")
                    exit_event.clear()
                    break
                s.send(bytes_read)
                total_bytes += len(bytes_read)
                self._progress_bar_send.set(math.ceil(total_bytes / file_size))

    def start_receiving(self):
        """ Method to start receiving the file """
        # socket initialization
        adresse = ""
        port = 4711
        s = socket.socket()
        s.bind((adresse, port))

        s.listen(1)

        client_socket, client_address = s.accept()

        # verify if the adress is in selectable adresses
        if client_address[0] not in self.datas["ip"].values():
            CTkMessagebox(title="Error", message="Connection refused, IP not registered", icon="cancel")
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
                if not datas:    # if file is fully readen
                    client_socket.close()
                    s.close()
                    CTkMessagebox(title="Complete", message="Receiving complete", icon="check")
                    break
                if exit_event.is_set():     # if user wants to cancel
                    CTkMessagebox(title="Cancel", message="Receiving successfully canceled", icon="check")
                    exit_event.clear()
                    break
                f.write(datas)
                total_bytes += len(datas)
                self._progress_bar_send.set(math.ceil(total_bytes / file_size))


if __name__ == "__main__":
    a = App()
    exit_event.set()
