# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from PIL import Image
import base64
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Для сессий (сменить на реальный)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Хранилище активных пользователей (room-based, все в одной комнате 'chat')
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
    username = data['username']
    users[request.sid] = username
    emit('system_message', f"[SYSTEM] {username} joined the chat!", broadcast=True, include_self=False)
    print(f"User {username} joined")

@socketio.on('change_nick')
def handle_change_nick(data):
    old_username = users.get(request.sid)
    new_username = data['new_username']
    if old_username and new_username:
        users[request.sid] = new_username
        emit('system_message', f"[SYSTEM] {old_username} changed nick to {new_username}", broadcast=True, include_self=False)

@socketio.on('text_message')
def handle_text_message(data):
    username = users.get(request.sid)
    if username:
        message = data['message']
        emit('text_message', {'username': username, 'message': message}, broadcast=True, include_self=False)

@socketio.on('image_message')
def handle_image_message(data):
    username = users.get(request.sid)
    if username:
        filename = data['filename']
        b64_img = data['image']
        emit('image_message', {'username': username, 'filename': filename, 'image': b64_img}, broadcast=True, include_self=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)