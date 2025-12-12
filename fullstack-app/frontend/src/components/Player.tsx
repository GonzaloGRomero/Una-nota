import React, { useEffect, useState } from 'react';
import { useGameSocket } from '../hooks/useGameSocket';
import { Player as PlayerType } from '../types';
import './Player.css';

export function Player() {
  const { connected, gameState, playerId, connect, buzz, lastPointAwarded, joinError } = useGameSocket();
  const [name, setName] = useState('');
  const [joined, setJoined] = useState(false);
  const [hasBuzzed, setHasBuzzed] = useState(false);

  useEffect(() => {
    if (gameState && gameState.status === 'stopped') {
      setHasBuzzed(false);
    }
  }, [gameState]);

  const handleJoin = () => {
    if (name.trim()) {
      setJoined(true);
      connect(name.trim(), 'player');
    }
  };

  useEffect(() => {
    if (joinError) {
      setJoined(false);
    }
  }, [joinError]);

  const handleBuzz = () => {
    if (!hasBuzzed && playerId) {
      buzz();
      setHasBuzzed(true);
    }
  };

  const getMyPosition = (): number => {
    if (!gameState || !playerId) return 0;
    const index = gameState.buzz_queue.indexOf(playerId);
    return index >= 0 ? index + 1 : 0;
  };

  const getMyPlayer = (): PlayerType | undefined => {
    if (!gameState || !playerId) return undefined;
    return gameState.players[playerId];
  };

  const getPlayersSortedByScore = (): PlayerType[] => {
    if (!gameState) return [];
    return Object.values(gameState.players).sort((a, b) => b.score - a.score);
  };

  if (!joined) {
    return (
      <div className="player-container">
        <div className="join-form">
          <h1>🎮 Jugador</h1>
          <input
            type="text"
            placeholder="Tu nombre"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && name.trim() && handleJoin()}
          />
          {joinError && (
            <div className="error-message">
              <p>{joinError}</p>
            </div>
          )}
          <button onClick={handleJoin} disabled={!name.trim()}>
            Unirse al Juego
          </button>
        </div>
      </div>
    );
  }

  const myPlayer = getMyPlayer();

  return (
    <div className="player-container">
      <div className="player-header">
        <h1>🎮 {name}</h1>
        <div className="connection-status">
          {connected ? '🟢 Conectado' : '🔴 Desconectado'}
        </div>
      </div>

      <div className="game-info-section">
        <h2>Información del Juego</h2>
        {lastPointAwarded ? (
          <div className={`point-awarded-notification ${lastPointAwarded.points < 0 ? 'point-lost' : 'point-won'}`}>
            {lastPointAwarded.points > 0 ? (
              <>
                <p className="notification-title">¡{lastPointAwarded.playerName} ganó {lastPointAwarded.points} punto{lastPointAwarded.points > 1 ? 's' : ''}!</p>
                <p className="track-info-label">La canción era:</p>
                <p className="track-name"><strong>{lastPointAwarded.track.title}</strong></p>
                <p className="track-artist">{lastPointAwarded.track.artist}</p>
              </>
            ) : (
              <>
                <p className="notification-title">¡{lastPointAwarded.playerName} perdió {Math.abs(lastPointAwarded.points)} punto{Math.abs(lastPointAwarded.points) > 1 ? 's' : ''}!</p>
                <p className="track-info-label">La canción era:</p>
                <p className="track-name"><strong>{lastPointAwarded.track.title}</strong></p>
                <p className="track-artist">{lastPointAwarded.track.artist}</p>
              </>
            )}
          </div>
        ) : (
          <p>Esperando que el organizador inicie una canción...</p>
        )}
      </div>

      <div className="buzz-section">
        <h2>¡Buzz!</h2>
        <button
          className={`buzz-button ${hasBuzzed ? 'buzzed' : ''}`}
          onClick={handleBuzz}
          disabled={hasBuzzed || !connected || gameState?.status === 'stopped'}
        >
          {hasBuzzed ? '✅ Ya presionaste!' : '🔔 ¡BUZZ!'}
        </button>
        {getMyPosition() > 0 && (
          <p className="position-info">
            Tu posición en la cola: <strong>#{getMyPosition()}</strong>
          </p>
        )}
        {hasBuzzed && getMyPosition() === 0 && (
          <p className="waiting-info">Esperando que el organizador reinicie...</p>
        )}
      </div>

      <div className="my-score-section">
        <h2>Mi Puntuación</h2>
        <div className="score-display">
          <span className="score-value">{myPlayer?.score || 0}</span>
          <span className="score-label">puntos</span>
        </div>
      </div>

      <div className="scoreboard-section">
        <h2>Scoreboard</h2>
        {getPlayersSortedByScore().length === 0 ? (
          <p>No hay jugadores aún</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Posición</th>
                <th>Nombre</th>
                <th>Puntos</th>
              </tr>
            </thead>
            <tbody>
              {getPlayersSortedByScore().map((player, index) => (
                <tr key={player.id} className={player.id === playerId ? 'my-row' : ''}>
                  <td>{index + 1}</td>
                  <td>{player.name} {player.id === playerId ? '(Tú)' : ''}</td>
                  <td>{player.score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}