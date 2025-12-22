import React, { useState } from 'react';
import './App.css';
import { Home } from './components/Home';
import { Organizer } from './components/Organizer';
import { Player } from './components/Player';

type ViewMode = 'home' | 'organizer' | 'player';

interface RoomInfo {
  roomName: string;
  password: string;
}

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('home');
  const [roomInfo, setRoomInfo] = useState<RoomInfo | null>(null);

  const handleJoinRoom = (roomName: string, password: string, role: 'organizer' | 'player') => {
    setRoomInfo({ roomName, password });
    setViewMode(role);
  };

  if (viewMode === 'organizer' && roomInfo) {
    return <Organizer roomName={roomInfo.roomName} password={roomInfo.password} />;
  }

  if (viewMode === 'player' && roomInfo) {
    return <Player roomName={roomInfo.roomName} password={roomInfo.password} />;
  }

  return <Home onJoinRoom={handleJoinRoom} />;
}

export default App;
