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


def start_thread(to_execute: ..., *args):
    """ Function to execute a thread
        :param to_execute: ... -> object to execute in the new thread
        :param args: Any -> arguments to pass
    """
    threading.Thread(target=to_execute, args=args).start()


def try_to_connect(s: socket.socket, host: str, port: int) -> bool:
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

        # receive tab
        button_start_receive = customtkinter.CTkButton(tabview.tab("Receive"), text="Start receiving",
                                                       command=lambda: start_thread(self.start_receiving()))
        button_start_receive.pack(anchor="center")

        super().mainloop()

    def select_folder(self):
        folder_path = askopenfilename(title="Select file")
        self.folder.set(folder_path)

    def start_sending(self):
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

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        BUFFER_SIZE = 4096

        s.send(f"{file_name}".encode())

        with open(file_path, "rb") as f:
            while True:
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break
                print(bytes_read)
                s.send(bytes_read)

        s.close()

    def start_receiving(self):
        adresse = ""
        port = 4711
        s = socket.socket()
        s.bind((adresse, port))

        s.listen(1)

        client_socket, client_address = s.accept()
        if client_address[0] not in self.datas["ip"].values():
            CTkMessagebox(title="Error", message="Connection refused, IP not registered", icon="cancel")
            return None

        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")

        filename = client_socket.recv(4096).decode()
        filepath = os.path.join(downloads_folder, filename)
        with open(filepath, 'wb') as f:
            while True:
                datas = client_socket.recv(4096)
                if not datas:
                    break
                f.write(datas)

        client_socket.close()
        s.close()

        CTkMessagebox(title="Complete", message="Download complete", icon="check")


if __name__ == "__main__":
    a = App()