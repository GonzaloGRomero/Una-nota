import React, { useState } from 'react';
import './App.css';
import { Organizer } from './components/Organizer';
import { Player } from './components/Player';

type ViewMode = 'select' | 'organizer' | 'player';

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('select');

  if (viewMode === 'organizer') {
    return <Organizer />;
  }

  if (viewMode === 'player') {
    return <Player />;
  }

  return (
    <div className="App">
      <div className="mode-selector">
        <h1>🎵 Juego Musical Multijugador</h1>
        <p>Selecciona tu rol:</p>
        <div className="mode-buttons">
          <button 
            className="mode-button organizer-button"
            onClick={() => setViewMode('organizer')}
          >
            🎵 Organizador
          </button>
          <button 
            className="mode-button player-button"
            onClick={() => setViewMode('player')}
          >
            🎮 Jugador
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
