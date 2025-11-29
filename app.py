import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from deep_translator import GoogleTranslator
import os

app = Flask(__name__)
socketio = SocketIO(app, async_mode="eventlet", cors_allowed_origins="*")

users = {}
user_languages = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate')
def translate():
    text = request.args.get('text')
    lang = request.args.get('lang')
    try:
        translator = GoogleTranslator(source='auto', target=lang)
        translation = translator.translate(text)
        return jsonify({"translation": translation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    pass

@socketio.on('set-username')
def handle_set_username(data):
    username = data['username']
    language = data['language']
    users[username] = request.sid
    user_languages[username] = language
    emit('user-joined', username, broadcast=True)

@socketio.on('offer')
def handle_offer(data):
    emit('offer', data, broadcast=True)

@socketio.on('answer')
def handle_answer(data):
    emit('answer', data, broadcast=True)

@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    emit('ice-candidate', data, broadcast=True)

@socketio.on('private-message')
def handle_private_message(data):
    to = data['to']
    message = data['message']

    from_username = None
    for u, sid in users.items():
        if sid == request.sid:
            from_username = u
            break

    to_sid = users.get(to)
    if to_sid and from_username:
        target_lang = user_languages.get(to, 'en')
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated_message = translator.translate(message)

        emit('private-message', {
            'from': from_username,
            'message': translated_message
        }, room=to_sid)

@socketio.on('disconnect')
def handle_disconnect():
    remove_user = None
    for username, sid in users.items():
        if sid == request.sid:
            remove_user = username
            break

    if remove_user:
        users.pop(remove_user, None)
        user_languages.pop(remove_user, None)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)
