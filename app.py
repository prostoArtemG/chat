# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from PIL import Image
import base64
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-me')  # Из env для Railway
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)

# Хранилище активных пользователей (все в одной комнате 'chat')
users = {}  # {sid: username}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    username = users.get(request.sid)
    if username:
        emit('system_message', f"[SYSTEM] {username} left the chat!", broadcast=True, include_self=False)
        del users[request.sid]
    print('Client disconnected')

@socketio.on('join')
def handle_join(data):
    username = data.get('username', 'Anonymous').strip()
    if not username:
        username = 'Anonymous'
    users[request.sid] = username
    emit('system_message', f"[SYSTEM] {username} joined the chat!", broadcast=True, include_self=False)
    print(f"User {username} joined")

@socketio.on('change_nick')
def handle_change_nick(data):
    old_username = users.get(request.sid)
    new_username = data.get('new_username', '').strip()
    if old_username and new_username and new_username != old_username:
        users[request.sid] = new_username
        emit('system_message', f"[SYSTEM] {old_username} changed nick to {new_username}", broadcast=True, include_self=False)
        print(f"User changed nick: {old_username} -> {new_username}")

@socketio.on('text_message')
def handle_text_message(data):
    username = users.get(request.sid)
    if username:
        message = data.get('message', '').strip()
        if message and len(message) <= 500:  # Лимит на длину для спама
            emit('text_message', {'username': username, 'message': message}, broadcast=True, include_self=False)
            print(f"Message from {username}: {message}")
        else:
            emit('system_message', "Message too long or empty!", to=request.sid)

@socketio.on('image_message')
def handle_image_message(data):
    username = users.get(request.sid)
    if username:
        filename = data.get('filename', 'image.png').strip()
        b64_img = data.get('image', '').strip()
        if b64_img and len(b64_img) <= 1048576:  # Лимит ~1MB base64
            try:
                # Валидация base64
                img_data = base64.b64decode(b64_img)
                pil_img = Image.open(io.BytesIO(img_data))
                # Проверка: только изображения
                if pil_img.format in ['PNG', 'JPEG', 'JPG', 'GIF', 'BMP']:
                    emit('image_message', {'username': username, 'filename': filename, 'image': b64_img}, broadcast=True, include_self=False)
                    print(f"Image from {username}: {filename}")
                else:
                    emit('system_message', "Invalid image format!", to=request.sid)
            except Exception as e:
                print(f"Image error: {e}")
                emit('system_message', "Invalid image data!", to=request.sid)
        else:
            emit('system_message', "Image too large or missing!", to=request.sid)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
