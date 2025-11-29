from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from deep_translator import GoogleTranslator
import os
from pyngrok import ngrok

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")

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
    print('A user connected')

@socketio.on('set-username')
def handle_set_username(data):
    username = data['username']
    language = data['language']
    users[username] = request.sid 
    user_languages[username] = language  
    print(f'{username} has joined the chat with preferred language {language}.')
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
    for username, sid in users.items():
        if sid == request.sid:
            from_username = username
            break
    to_sid = users.get(to)
    if to_sid and from_username:
        target_language = user_languages.get(to, 'en')
        translator = GoogleTranslator(source='auto', target=target_language)
        translated_message = translator.translate(message)
        emit('private-message', {'from': from_username, 'message': translated_message}, room=to_sid)

@socketio.on('disconnect')
def handle_disconnect():
    for username, sid in users.items():
        if sid == request.sid:
            del users[username]
            del user_languages[username]
            break
    print('A user disconnected')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    public_url = ngrok.connect(port)
    print("Ngrok Tunnel URL:", public_url)

    socketio.run(app, host='0.0.0.0', port=port)
