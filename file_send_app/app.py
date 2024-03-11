import os
import socket
import re
import customtkinter
import threading
from tkinter.filedialog import askopenfilename
from CTkMessagebox import CTkMessagebox
from datas_extraction import read_json_file, get_self_ip

customtkinter.set_appearance_mode("System")
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

        self.datas = read_json_file("datas.json")
        self.stop_process = False

        ips = self.datas["ip"]
        ips = {name: ip for name, ip in ips.items() if ip != get_self_ip()}

        self.title("File Sender app")
        self.geometry(f"{450}x{280}")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        tabview = customtkinter.CTkTabview(self)
        tabview.add("Send")
        tabview.add("Receive")
        tabview.grid(row=1, column=0, columnspan=4, sticky="nswe", padx=10, pady=5)

        # send tab
        label_ip = customtkinter.CTkLabel(tabview.tab("Send"), text="Select ip : ")
        label_ip.grid(row=0, column=0)
        values = [key for key in ips.keys()]
        self.option_ip = customtkinter.CTkOptionMenu(tabview.tab("Send"), values=values)
        self.option_ip.grid(row=0, column=1, padx=20, pady=5)
        label_file = customtkinter.CTkLabel(tabview.tab("Send"), text="File Path : ")
        label_file.grid(row=2, column=0)
        self.folder = customtkinter.StringVar()
        self.entry_file = customtkinter.CTkEntry(tabview.tab("Send"), textvariable=self.folder)
        self.entry_file.grid(row=2, column=1, padx=20, pady=5)
        button_file = customtkinter.CTkButton(tabview.tab("Send"), text="Browse", command=self.select_folder)
        button_file.grid(row=2, column=2, padx=20, pady=5)

        tabview.grid_rowconfigure(3, weight=1)
        button_start_send = customtkinter.CTkButton(tabview.tab("Send"), text="Start sending",
                                                    command=lambda: start_thread(self.start_sending))
        button_start_send.grid(row=3, column=1, pady=20, sticky="e")
        button_stop_receive = customtkinter.CTkButton(tabview.tab("Send"), text="Stop sending",
                                                      command=lambda: exit_event.set())
        button_stop_receive.grid(row=4, column=1, pady=20, sticky="e")

        # receive tab
        button_start_receive = customtkinter.CTkButton(tabview.tab("Receive"), text="Start receiving",
                                                       command=lambda: start_thread(self.start_receiving))
        button_start_receive.pack(anchor="center")
        button_stop_receive = customtkinter.CTkButton(tabview.tab("Receive"), text="Stop receiving",
                                                      command=lambda: exit_event.set())
        button_stop_receive.pack(anchor="center", pady=20)

        super().mainloop()

    def select_folder(self):
        """ Method to select the folder path and change the needed entry """
        folder_path = askopenfilename(title="Select file")
        if folder_path != "":
            self.folder.set(folder_path)

    def start_sending(self):
        """ Method to start sending the file """
        # inputs selection
        host: str = self.datas["ip"][self.option_ip.get()]
        file_path: str = self.entry_file.get()
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
        file_name = os.path.basename(file_path)

        s.send(f"{file_name}".encode())

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


if __name__ == "__main__":
    a = App()
