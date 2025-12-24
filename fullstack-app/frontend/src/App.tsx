import React, { useState, useEffect } from 'react';
import './App.css';
import { Home } from './components/Home';
import { Organizer } from './components/Organizer';
import { Player } from './components/Player';
import { Admin } from './components/Admin';

type ViewMode = 'home' | 'organizer' | 'player' | 'admin';

interface RoomInfo {
  roomName: string;
  password: string;
}

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('home');
  const [roomInfo, setRoomInfo] = useState<RoomInfo | null>(null);

  useEffect(() => {
    // Detectar si la URL es /admin
    const path = window.location.pathname;
    if (path === '/admin') {
      setViewMode('admin');
    }
  }, []);

  const handleJoinRoom = (roomName: string, password: string, role: 'organizer' | 'player') => {
    setRoomInfo({ roomName, password });
    setViewMode(role);
  };

  if (viewMode === 'admin') {
    return <Admin />;
  }

  if (viewMode === 'organizer' && roomInfo) {
    return <Organizer roomName={roomInfo.roomName} password={roomInfo.password} />;
  }

  if (viewMode === 'player' && roomInfo) {
    return <Player roomName={roomInfo.roomName} password={roomInfo.password} />;
  }

  return <Home onJoinRoom={handleJoinRoom} />;
}

export default App;
