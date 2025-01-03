
let peerConnection;
let dataChannel;
let roomId = ""; 
let username = ""; 

const configuration = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' }, 
        { 
            urls: 'relay1.expressturn.com:3478', 
            username: 'efAABT4OYX6I3Z4TTR',
            credential: 'pra1CUrmcc86lRxWi' 
        }
    ]
};

const socket = io(); 

document.getElementById('createButton').onclick = () => {
    const roomInput = document.getElementById('roomInput');
    const usernameInput = document.getElementById('usernameInput');
    roomId = roomInput.value;
    username = usernameInput.value;

    if (roomId && username) {
        socket.emit('create_room', { room_id: roomId, username: username });
        startWebRTC(); 
    } else {
        alert('Please enter both Room ID and Username.');
    }
};

document.getElementById('joinButton').onclick = () => {
    const roomInput = document.getElementById('roomInput');
    const usernameInput = document.getElementById('usernameInput');
    roomId = roomInput.value;
    username = usernameInput.value;

    if (roomId && username) {
        socket.emit('join_room', { room_id: roomId, username: username });
        startWebRTC(); 
    } else {
        alert('Please enter both Room ID and Username.');
    }
};

function startWebRTC() {
    peerConnection = new RTCPeerConnection(configuration);

    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            socket.emit('signal', { candidate: event.candidate, room_id: roomId });
        }
    };

    peerConnection.ondatachannel = (event) => {
        dataChannel = event.channel;

        dataChannel.onmessage = (event) => {
            const message = event.data;
            displayMessage('Friend', message);
        };
    };

    dataChannel = peerConnection.createDataChannel('chat');

    dataChannel.onmessage = (event) => {
        const message = event.data;
        displayMessage('You', message); 
    };

    peerConnection.createOffer().then((offer) => {
        return peerConnection.setLocalDescription(offer);
    }).then(() => {
        socket.emit('signal', { sdp: peerConnection.localDescription, room_id: roomId });
    }).catch((error) => {
        console.error('Error creating offer: ', error);
    });
}

document.getElementById('sendButton').onclick = () => {
    sendMessage(); 
};

function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value;

    if (dataChannel && dataChannel.readyState === 'open') {
        dataChannel.send(message); 

        displayMessage('You', message);
        input.value = ''; 
    } else {
        console.error('Data channel is not open.');
    }
}

function displayMessage(sender, message) {
    const li = document.createElement('li');
    li.innerText = `${sender}: ${message}`;
    document.getElementById('messages').appendChild(li);
}

socket.on('signal', async (data) => {
    if (data.sdp) {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
        
        if (data.sdp.type === 'offer') {
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            socket.emit('signal', { sdp: peerConnection.localDescription, room_id: roomId });
        }
    } else if (data.candidate) {
        await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
    }
});
