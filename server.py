# -*- coding: utf-8 -*-
import socket
import threading
import os
from PIL import Image
import io
import base64

# List of active clients and their usernames
clients = {}  # {sock: username}
lock = threading.Lock()

def broadcast(message):
    """Broadcast message to all clients"""
    with lock:
        for client_sock in list(clients.keys()):
            try:
                client_sock.sendall(message.encode('utf-8'))
            except:
                # Remove disconnected client
                if client_sock in clients:
                    del clients[client_sock]

def handle_client(client_sock, addr):
    """Handle one client"""
    username = None
    try:
        while True:
            data = client_sock.recv(4096).decode('utf-8', errors='ignore')
            if not data:
                break
            
            lines = data.strip().split('\n')
            for line in lines:
                if not line:
                    continue
                parts = line.split("@", 3)
                msg_type = parts[0]
                
                if msg_type == "TEXT" and len(parts) >= 3:
                    username = parts[1]
                    message = parts[2]
                    # Add username to dict
                    with lock:
                        clients[client_sock] = username
                    # Form message for broadcast
                    broadcast_msg = f"TEXT@{username}@{message}\n"
                    broadcast(broadcast_msg)
                    
                elif msg_type == "IMAGE" and len(parts) >= 4:
                    if username is None:
                        continue
                    filename = parts[2]
                    b64_img = parts[3]
                    # Broadcast image to all
                    broadcast_msg = f"IMAGE@{username}@{filename}@{b64_img}\n"
                    broadcast(broadcast_msg)
                    
                elif "[SYSTEM]" in line and len(parts) >= 3:
                    # Join
                    username = parts[2]
                    with lock:
                        clients[client_sock] = username
                    join_msg = f"TEXT@SYSTEM@[SYSTEM] {username} joined the chat!\n"
                    broadcast(join_msg)
                
                elif "[LEAVE]" in line:
                    # Leave (handled in finally)
                    pass
                
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        # Disconnect
        if username:
            leave_msg = f"TEXT@SYSTEM@[SYSTEM] {username} left the chat!\n"
            broadcast(leave_msg)
        with lock:
            if client_sock in clients:
                del clients[client_sock]
        client_sock.close()
        print(f"Client {addr} disconnected.")

def start_server():
    host = '0.0.0.0'  # For cloud hosting (Railway)
    port = int(os.environ.get('PORT', 8080))  # Railway sets PORT via env
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"Server started on {host}:{port}. Waiting for clients...")

    while True:
        client_sock, addr = server.accept()
        print(f"New client from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_sock, addr))
        client_thread.daemon = True
        client_thread.start()

if __name__ == "__main__":
    start_server()