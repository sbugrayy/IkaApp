const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Rooms
const rooms = new Map();

io.on('connection', (socket) => {
  console.log('🔌 Yeni bağlantı:', socket.id);

  socket.on('join-room', (data) => {
    const { roomId, role } = data;
    console.log(`👤 ${socket.id} odaya katılıyor: ${roomId} (${role})`);
    
    socket.join(roomId);
    
    if (!rooms.has(roomId)) {
      rooms.set(roomId, {
        id: roomId,
        participants: new Set(),
        cameras: []
      });
    }
    
    const room = rooms.get(roomId);
    room.participants.add(socket.id);
    
    socket.emit('room-joined', {
      roomId: roomId,
      role: role,
      participants: room.participants.size
    });
    
    socket.broadcast.to(roomId).emit('peer-joined', {
      peerId: socket.id,
      role: role
    });
    
    console.log(`✅ ${socket.id} odaya katıldı: ${roomId}`);
  });

  socket.on('camera-stream', (data) => {
    const { roomId, cameraId, frame } = data;
    console.log(`📹 Kamera ${cameraId} frame'i alındı - Room: ${roomId}, Frame size: ${frame ? frame.length : 0}`);
    
    // Room'daki diğer kullanıcılara gönder
    socket.broadcast.to(roomId).emit('camera-frame', {
      cameraId: cameraId,
      frame: frame,
      timestamp: Date.now()
    });
    
    console.log(`📤 Kamera ${cameraId} frame'i gönderildi - Room: ${roomId}`);
  });

  socket.on('disconnect', () => {
    console.log('❌ Bağlantı kesildi:', socket.id);
    
    // Remove from all rooms
    for (const [roomId, room] of rooms.entries()) {
      if (room.participants.has(socket.id)) {
        room.participants.delete(socket.id);
        
        if (room.participants.size === 0) {
          rooms.delete(roomId);
          console.log(`🗑️ Oda silindi: ${roomId}`);
        }
        
        socket.broadcast.to(roomId).emit('peer-left', {
          peerId: socket.id
        });
      }
    }
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`🚀 IKA WebRTC Server çalışıyor: http://localhost:${PORT}`);
  console.log(`📹 Çoklu kamera streaming hazır!`);
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    rooms: rooms.size,
    timestamp: new Date().toISOString()
  });
});
