import React, { useState, useEffect } from 'react';
import './Admin.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface RoomInfo {
  name: string;
  created_at: string;
  player_count: number;
  track_count: number;
  current_track_id: string | null;
  status: string;
}

interface RoomDetail extends RoomInfo {
  players: Record<string, { id: string; name: string; score: number }>;
  tracks: any[];
  buzz_queue: string[];
}

export function Admin() {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [rooms, setRooms] = useState<RoomInfo[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<RoomDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [adminPassword, setAdminPassword] = useState('');

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/admin/auth`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password }),
      });

      if (response.ok) {
        setAuthenticated(true);
        setAdminPassword(password);
        loadRooms();
      } else {
        setAuthError('Contraseña incorrecta');
      }
    } catch (error) {
      setAuthError('Error al autenticar');
    } finally {
      setLoading(false);
    }
  };

  const loadRooms = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/rooms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ admin_password: adminPassword }),
      });
      if (response.ok) {
        const data = await response.json();
        setRooms(data.rooms || []);
      }
    } catch (error) {
      console.error('Error cargando salas:', error);
    }
  };

  const loadRoomDetails = async (roomName: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/rooms/${encodeURIComponent(roomName)}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ admin_password: adminPassword }),
        }
      );
      if (response.ok) {
        const data = await response.json();
        setSelectedRoom(data);
      }
    } catch (error) {
      console.error('Error cargando detalles de sala:', error);
    }
  };

  const handleCloseRoom = async (roomName: string) => {
    if (!window.confirm(`¿Estás seguro de que quieres cerrar la sala "${roomName}"? Todos los jugadores serán desconectados.`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/admin/rooms/close`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room_name: roomName,
          admin_password: adminPassword,
        }),
      });

      if (response.ok) {
        await loadRooms();
        if (selectedRoom?.name === roomName) {
          setSelectedRoom(null);
        }
        alert(`Sala "${roomName}" cerrada exitosamente`);
      } else {
        const error = await response.json();
        console.error('Error cerrando sala:', error);
        alert(`Error: ${error.detail || 'No se pudo cerrar la sala'}`);
      }
    } catch (error) {
      alert('Error al cerrar la sala');
    }
  };

  const handleBanPlayer = async (roomName: string, playerId: string, playerName: string) => {
    if (!window.confirm(`¿Estás seguro de que quieres expulsar a "${playerName}" de la sala "${roomName}"?`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/admin/players/ban`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room_name: roomName,
          player_id: playerId,
          admin_password: adminPassword,
        }),
      });

      if (response.ok) {
        await loadRoomDetails(roomName);
        await loadRooms();
        alert(`Jugador "${playerName}" expulsado exitosamente`);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'No se pudo expulsar al jugador'}`);
      }
    } catch (error) {
      alert('Error al expulsar al jugador');
    }
  };

  useEffect(() => {
    if (authenticated) {
      loadRooms();
      const interval = setInterval(loadRooms, 5000); // Actualizar cada 5 segundos
      return () => clearInterval(interval);
    }
  }, [authenticated, adminPassword]);

  const handleBackToHome = () => {
    window.location.href = '/';
  };

  if (!authenticated) {
    return (
      <div className="admin-container">
        <div className="admin-auth">
          <h1>🔐 Panel de Administrador</h1>
          <p>Ingresa la contraseña de administrador para continuar</p>
          <form onSubmit={handleAuth}>
            <input
              type="password"
              placeholder="Contraseña de administrador"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
              autoFocus
            />
            {authError && <div className="error-message">{authError}</div>}
            <button type="submit" disabled={loading || !password}>
              {loading ? 'Verificando...' : 'Ingresar'}
            </button>
          </form>
          <button onClick={handleBackToHome} className="back-to-menu-button-auth">
            🏠 Volver al Menú
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-container">
      <div className="admin-header">
        <h1>🔐 Panel de Administrador</h1>
        <div className="admin-header-buttons">
          <button onClick={handleBackToHome} className="back-to-menu-button">
            🏠 Volver al Menú
          </button>
          <button onClick={() => setAuthenticated(false)} className="logout-button">
            Cerrar Sesión
          </button>
        </div>
      </div>

      <div className="admin-content">
        <div className="rooms-section">
          <div className="section-header">
            <h2>Salas Activas ({rooms.length})</h2>
            <button onClick={loadRooms} className="refresh-button">
              🔄 Actualizar
            </button>
          </div>

          {rooms.length === 0 ? (
            <p className="empty-message">No hay salas activas</p>
          ) : (
            <div className="rooms-list">
              {rooms.map((room) => (
                <div
                  key={room.name}
                  className={`room-card ${selectedRoom?.name === room.name ? 'selected' : ''}`}
                  onClick={() => loadRoomDetails(room.name)}
                >
                  <div className="room-card-header">
                    <h3>{room.name}</h3>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCloseRoom(room.name);
                      }}
                      className="close-room-button"
                      title="Cerrar sala"
                    >
                      ❌
                    </button>
                  </div>
                  <div className="room-card-info">
                    <span>👥 {room.player_count} jugadores</span>
                    <span>🎵 {room.track_count} canciones</span>
                    <span>📊 {room.status}</span>
                  </div>
                  <div className="room-card-date">
                    Creada: {new Date(room.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedRoom && (
          <div className="room-details-section">
            <div className="section-header">
              <h2>Detalles de Sala: {selectedRoom.name}</h2>
              <button onClick={() => setSelectedRoom(null)} className="close-button">
                ✕
              </button>
            </div>

            <div className="details-grid">
              <div className="detail-card">
                <h3>Jugadores ({Object.keys(selectedRoom.players).length})</h3>
                {Object.keys(selectedRoom.players).length === 0 ? (
                  <p className="empty-message">No hay jugadores</p>
                ) : (
                  <div className="players-list">
                    {Object.values(selectedRoom.players).map((player) => (
                      <div key={player.id} className="player-item">
                        <div className="player-info">
                          <strong>{player.name}</strong>
                          <span>Puntos: {player.score}</span>
                        </div>
                        <button
                          onClick={() => handleBanPlayer(selectedRoom.name, player.id, player.name)}
                          className="ban-button"
                          title="Expulsar jugador"
                        >
                          🚫 Expulsar
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="detail-card">
                <h3>Información de la Sala</h3>
                <div className="info-list">
                  <div className="info-item">
                    <strong>Estado:</strong> <span>{selectedRoom.status}</span>
                  </div>
                  <div className="info-item">
                    <strong>Canciones:</strong> <span>{selectedRoom.track_count}</span>
                  </div>
                  <div className="info-item">
                    <strong>Canción Actual:</strong>{' '}
                    <span>{selectedRoom.current_track_id || 'Ninguna'}</span>
                  </div>
                  <div className="info-item">
                    <strong>Buzzers en Cola:</strong> <span>{selectedRoom.buzz_queue.length}</span>
                  </div>
                  <div className="info-item">
                    <strong>Creada:</strong>{' '}
                    <span>{new Date(selectedRoom.created_at).toLocaleString()}</span>
                  </div>
                </div>
                <button
                  onClick={() => handleCloseRoom(selectedRoom.name)}
                  className="close-room-detail-button"
                >
                  🚫 Cerrar Sala
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
