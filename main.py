# -*- coding: utf-8 -*-
import base64
import io
import threading
import os
from socket import socket, AF_INET, SOCK_STREAM
from customtkinter import *
from tkinter import filedialog, END
from PIL import Image


class MainWindow(CTk):
    def __init__(self):
        super().__init__()

        self.geometry('600x600')
        self.title("Chat Client")

        # Server settings (change for remote connection)
        self.server_host = "hopper.proxy.rlwy.net"  # “в≥й прокс≥
        self.server_port = 23527  # “в≥й порт

        self.username = "KTO-TO"

        # Menu
        self.label = None
        self.menu_frame = CTkFrame(self, width=30, height=300)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)
        self.is_show_menu = False
        self.speed_animate_menu = -20
        self.btn = CTkButton(self, text='??', command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)

        # Main chat field
        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(relx=0, rely=0, anchor='nw')

        # Input field and buttons
        self.message_entry = CTkEntry(self, placeholder_text='Enter message:', height=40)
        self.message_entry.place(x=0, y=0)
        self.send_button = CTkButton(self, text='>', width=50, height=40, command=self.send_message)
        self.send_button.place(x=0, y=0)

        self.open_img_button = CTkButton(self, text='??', width=50, height=40, command=self.open_image)
        self.open_img_button.place(x=0, y=0)

        self.adaptive_ui()

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((self.server_host, self.server_port))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} joined the chat!\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
            # Handle window closing
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
        except Exception as e:
            self.add_message(f"Failed to connect to server {self.server_host}:{self.server_port}: {e}")

    def on_closing(self):
        if hasattr(self, 'sock') and self.sock:
            try:
                leave_msg = f"TEXT@{self.username}@[LEAVE] Left chat.\n"
                self.sock.send(leave_msg.encode('utf-8'))
            except:
                pass
            self.sock.close()
        self.destroy()

    def toggle_show_menu(self):
        if self.is_show_menu:
            self.is_show_menu = False
            self.speed_animate_menu *= -1
            self.btn.configure(text='??')
            self.show_menu()
        else:
            self.is_show_menu = True
            self.speed_animate_menu *= -1
            self.btn.configure(text='??')
            self.show_menu()
            # On menu open - add name change
            self.label = CTkLabel(self.menu_frame, text='Name')
            self.label.pack(pady=30)
            self.entry = CTkEntry(self.menu_frame, placeholder_text="Your nick...")
            self.entry.pack()
            # Save button
            self.save_button = CTkButton(self.menu_frame, text="Save", command=self.save_name)
            self.save_button.pack()

    def show_menu(self):
        self.menu_frame.configure(width=self.menu_frame.winfo_width() + self.speed_animate_menu)
        if self.menu_frame.winfo_width() < 200 and self.is_show_menu:
            self.after(10, self.show_menu)
        elif self.menu_frame.winfo_width() > 60 and not self.is_show_menu:
            self.after(10, self.show_menu)
            if self.label:
                self.label.destroy()
            if hasattr(self, "entry"):
                self.entry.destroy()
            if hasattr(self, "save_button"):
                self.save_button.destroy()

    def save_name(self):
        new_name = self.entry.get().strip()
        if new_name:
            self.username = new_name
            self.add_message(f"Your new nick: {self.username}")

    def adaptive_ui(self):
        self.menu_frame.configure(height=self.winfo_height())
        self.chat_field.place(x=self.menu_frame.winfo_width())
        self.chat_field.configure(width=self.winfo_width() - self.menu_frame.winfo_width() - 20,
                                  height=self.winfo_height() - 40)
        self.send_button.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)
        self.message_entry.place(x=self.menu_frame.winfo_width(), y=self.send_button.winfo_y())
        self.message_entry.configure(width=self.winfo_width() - self.menu_frame.winfo_width() - 110)
        self.open_img_button.place(x=self.winfo_width() - 105, y=self.send_button.winfo_y())

        self.after(50, self.adaptive_ui)

    def add_message(self, message, img=None):
        message_frame = CTkFrame(self.chat_field, fg_color='gray')
        message_frame.pack(pady=5, anchor='w')
        wrapleng_size = self.winfo_width() - self.menu_frame.winfo_width() - 40

        if img is None:
            CTkLabel(message_frame, text=message, wraplength=wrapleng_size,
                     text_color='white', justify='left').pack(padx=10, pady=5)
        else:
            CTkLabel(message_frame, text=message, wraplength=wrapleng_size,
                     text_color='white', image=img, compound='top',
                     justify='left').pack(padx=10, pady=5)

    def send_message(self):
        message = self.message_entry.get()
        if message:
            self.add_message(f"{self.username}: {message}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode('utf-8'))
            except:
                pass
        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode('utf-8', errors='ignore')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())

            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                b64_img = parts[3]
                try:
                    img_data = base64.b64decode(b64_img)
                    pil_img = Image.open(io.BytesIO(img_data))
                    ctk_img = CTkImage(pil_img, size=(300, 300))
                    self.add_message(f"{author} sent image: {filename}", img=ctk_img)
                except Exception as e:
                    self.add_message(f"Error displaying image: {e}")
        else:
            self.add_message(line)

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
            b64_data = base64.b64encode(raw).decode('utf-8')
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            self.sock.sendall(data.encode('utf-8'))
            self.add_message(f"{self.username} sent image: {short_name}", CTkImage(light_image=Image.open(file_name), size=(300, 300)))
        except Exception as e:
            self.add_message(f"Failed to send image: {e}")


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()