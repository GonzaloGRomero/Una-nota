import React, { useState } from 'react';
import './Home.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

type HomeProps = {
  onJoinRoom: (roomName: string, password: string, role: 'organizer' | 'player') => void;
};

export function Home({ onJoinRoom }: HomeProps) {
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const [roomName, setRoomName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!roomName.trim()) {
      setError('El nombre de la sala es requerido');
      return;
    }

    if (!password || password.length < 4) {
      setError('La contraseña debe tener al menos 4 caracteres');
      return;
    }

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/rooms/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room_name: roomName.trim(),
          password: password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear la sala');
      }

      // Sala creada exitosamente, ahora unirse como organizador
      onJoinRoom(roomName.trim(), password, 'organizer');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear la sala');
    } finally {
      setLoading(false);
    }
  };

  const handleJoinRoom = async (e: React.FormEvent, role: 'organizer' | 'player') => {
    e.preventDefault();
    setError(null);

    if (!roomName.trim()) {
      setError('El nombre de la sala es requerido');
      return;
    }

    if (!password) {
      setError('La contraseña es requerida');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/rooms/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          room_name: roomName.trim(),
          password: password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al unirse a la sala');
      }

      // Unirse exitosamente
      onJoinRoom(roomName.trim(), password, role);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al unirse a la sala');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-container">
      <div className="home-header">
        <h1>🎵 Juego Musical Multijugador</h1>
        <p>Selecciona una opción para comenzar</p>
      </div>

      <div className="home-actions">
        <div className="action-card">
          <h2>Crear Sala</h2>
          <p>Crea una nueva sala de juego</p>
          <button
            className="action-button create-button"
            onClick={() => {
              setShowCreate(true);
              setShowJoin(false);
              setError(null);
            }}
          >
            ➕ Crear Sala
          </button>
        </div>

        <div className="action-card">
          <h2>Unirse a Sala</h2>
          <p>Únete a una sala existente</p>
          <button
            className="action-button join-button"
            onClick={() => {
              setShowJoin(true);
              setShowCreate(false);
              setError(null);
            }}
          >
            🚪 Unirse a Sala
          </button>
        </div>
      </div>

      {showCreate && (
        <div className="room-form-container">
          <h2>Crear Nueva Sala</h2>
          <form onSubmit={handleCreateRoom}>
            <div className="form-group">
              <label htmlFor="create-room-name">Nombre de la Sala</label>
              <input
                id="create-room-name"
                type="text"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                placeholder="Ej: Sala de Juan"
                maxLength={50}
                disabled={loading}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="create-password">Contraseña</label>
              <input
                id="create-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mínimo 4 caracteres"
                minLength={4}
                disabled={loading}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirm-password">Confirmar Contraseña</label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repite la contraseña"
                disabled={loading}
                required
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <div className="form-actions">
              <button type="submit" disabled={loading} className="submit-button">
                {loading ? 'Creando...' : 'Crear Sala como Organizador'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreate(false);
                  setRoomName('');
                  setPassword('');
                  setConfirmPassword('');
                  setError(null);
                }}
                className="cancel-button"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {showJoin && (
        <div className="room-form-container">
          <h2>Unirse a una Sala</h2>
          <form onSubmit={(e) => e.preventDefault()}>
            <div className="form-group">
              <label htmlFor="join-room-name">Nombre de la Sala</label>
              <input
                id="join-room-name"
                type="text"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                placeholder="Ej: Sala de Juan"
                disabled={loading}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="join-password">Contraseña</label>
              <input
                id="join-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Contraseña de la sala"
                disabled={loading}
                required
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <div className="form-actions">
              <button
                type="button"
                onClick={(e) => handleJoinRoom(e, 'organizer')}
                disabled={loading}
                className="submit-button organizer-join"
              >
                {loading ? 'Uniéndose...' : '🎵 Unirse como Organizador'}
              </button>
              <button
                type="button"
                onClick={(e) => handleJoinRoom(e, 'player')}
                disabled={loading}
                className="submit-button player-join"
              >
                {loading ? 'Uniéndose...' : '🎮 Unirse como Jugador'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowJoin(false);
                  setRoomName('');
                  setPassword('');
                  setError(null);
                }}
                className="cancel-button"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="admin-link-container">
        <a href="/admin" className="admin-link" title="Panel de Administrador">
          ⚙️ Admin
        </a>
      </div>
    </div>
  );
}
