import React, { useEffect, useRef, useState } from 'react';
import { useGameSocket } from '../hooks/useGameSocket';
import { Track, Player } from '../types';
import './Organizer.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface OrganizerProps {
  roomName: string;
  password: string;
}

export function Organizer({ roomName, password }: OrganizerProps) {
  const { connected, gameState, connect, control, setWinner, adjustScore, nextTrack, selectTrack, removePlayer } = useGameSocket();
  const [name, setName] = useState('Organizador');
  const [joined, setJoined] = useState(false);
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [playlistSource, setPlaylistSource] = useState<'spotify' | 'youtube'>('spotify');
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [youtubeAuthenticated, setYoutubeAuthenticated] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [tracksShuffled, setTracksShuffled] = useState(false);
  const [shuffledOrder, setShuffledOrder] = useState<string[]>([]);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [audioCache, setAudioCache] = useState<Record<string, string>>({});
  const tracksPerPage = 10;
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const previewTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!joined && name && roomName && password) {
      connect(name, 'organizer', roomName, password);
      setJoined(true);
    }
  }, [name, joined, roomName, password, connect]);

  useEffect(() => {
    const checkYoutubeAuth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/youtube/status`);
        const data = await response.json();
        setYoutubeAuthenticated(data.authenticated);
      } catch {
        setYoutubeAuthenticated(false);
      } finally {
        setCheckingAuth(false);
      }
    };
    checkYoutubeAuth();
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const authStatus = params.get('youtube_auth');
    if (authStatus === 'success') {
      setYoutubeAuthenticated(true);
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (authStatus === 'error') {
      const message = params.get('message');
      setImportError(`Error de autenticación: ${message || 'Error desconocido'}`);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const handleYoutubeAuth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/youtube/authorize`);
      const data = await response.json();
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      }
    } catch {
      setImportError('Error al iniciar autenticación de YouTube');
    }
  };

  const currentTrackIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!gameState || !gameState.current_track_id) return;

    const currentTrack = gameState.tracks.find(t => t.id === gameState.current_track_id);
    if (!currentTrack || !audioRef.current) return;

    const audio = audioRef.current;
    const trackChanged = currentTrackIdRef.current !== gameState.current_track_id;

    // Si cambió el track, actualizar la referencia
    if (trackChanged) {
      currentTrackIdRef.current = gameState.current_track_id;
    }

    const playAudio = async () => {
      let audioUrl = currentTrack.url;

      // Si no hay URL pero hay video_id, cargar bajo demanda
      if (!audioUrl && currentTrack.video_id) {
        const cachedUrl = audioCache[currentTrack.video_id];
        if (cachedUrl) {
          audioUrl = cachedUrl;
        } else {
          setLoadingAudio(true);
          const fetchedUrl = await fetchAudioUrl(currentTrack.video_id);
          setLoadingAudio(false);
          if (fetchedUrl) {
            audioUrl = fetchedUrl;
            setAudioCache(prev => ({ ...prev, [currentTrack.video_id!]: fetchedUrl }));
          }
        }
      }

      if (!audioUrl) return;
      
      // Solo cambiar el src si cambió el track o si no hay src establecido
      if (trackChanged || !audio.src || audio.src !== audioUrl) {
        audio.src = audioUrl;
      }

      if (gameState.status === 'playing') {
        audio.play().catch(() => {});
      } else if (gameState.status === 'preview2') {
        audio.currentTime = 0;
        audio.play().catch(() => {});
        if (previewTimeoutRef.current) clearTimeout(previewTimeoutRef.current);
        previewTimeoutRef.current = setTimeout(() => {
          audio.pause();
          audio.currentTime = 0;
        }, 2000);
      } else if (gameState.status === 'preview5') {
        audio.currentTime = 0;
        audio.play().catch(() => {});
        if (previewTimeoutRef.current) clearTimeout(previewTimeoutRef.current);
        previewTimeoutRef.current = setTimeout(() => {
          audio.pause();
          audio.currentTime = 0;
        }, 5000);
      }
    };

    // Manejar controles de reproducción
    if (gameState.status === 'paused') {
      // Solo pausar, NO resetear currentTime ni cambiar src
      audio.pause();
    } else if (gameState.status === 'stopped') {
      // Stop: pausar y resetear a 0
      audio.pause();
      audio.currentTime = 0;
    } else if (['playing', 'preview2', 'preview5'].includes(gameState.status)) {
      // Reproducir: cargar audio si es necesario y reproducir
      playAudio();
    }
  }, [gameState?.status, gameState?.current_track_id, gameState?.tracks, audioCache]);

  const handleImportPlaylist = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedUrl = playlistUrl.trim();
    if (!trimmedUrl) {
      setImportError('Por favor ingresa una URL de playlist');
      return;
    }

    setImporting(true);
    setImportError(null);
    setImportSuccess(null);

    const isYouTube = trimmedUrl.includes('youtube.com') || trimmedUrl.includes('music.youtube.com') || trimmedUrl.includes('youtu.be');
    const useAuthEndpoint = isYouTube && youtubeAuthenticated;

    try {
      const endpoint = useAuthEndpoint 
        ? `${API_BASE_URL}/playlist/import-authenticated`
        : `${API_BASE_URL}/playlist/import`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          playlist_url: trimmedUrl,
          source: playlistSource,
          room_name: roomName
        }),
      });

      if (!response.ok) {
        let errorMessage = 'Error al importar playlist';
        try {
          const error = await response.json();
          errorMessage = error.detail || errorMessage;
        } catch {
          errorMessage = `Error ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      let successMessage = `Playlist "${data.playlist_name}" importada exitosamente! ${data.total_tracks || data.tracks_count} canciones cargadas.`;
      if (data.tracks_skipped && data.tracks_skipped > 0) {
        successMessage += ` (${data.tracks_skipped} canciones omitidas)`;
      }
      if (data.requires_audio_fetch) {
        successMessage += ' (Audio se cargará al reproducir)';
      }
      setImportSuccess(successMessage);
      setPlaylistUrl('');
      setCurrentPage(1);
      setTracksShuffled(false);
      setShuffledOrder([]);
    } catch (error) {
      let errorMessage = 'Error desconocido';
      if (error instanceof Error) {
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
          errorMessage = 'No se pudo conectar al servidor';
        } else {
          errorMessage = error.message;
        }
      }
      setImportError(errorMessage);
    } finally {
      setImporting(false);
    }
  };

  const fetchAudioUrl = async (videoId: string): Promise<string | null> => {
    // Usar el endpoint de streaming que evita problemas de CORS y 403
    return `${API_BASE_URL}/youtube/stream/${videoId}`;
  };

  const getShuffledTracks = (): Track[] => {
    if (!gameState) return [];
    if (tracksShuffled && shuffledOrder.length > 0) {
      const orderMap = new Map(shuffledOrder.map((id, idx) => [id, idx]));
      return [...gameState.tracks].sort((a, b) => {
        const idxA = orderMap.get(a.id) ?? 9999;
        const idxB = orderMap.get(b.id) ?? 9999;
        return idxA - idxB;
      });
    }
    return [...gameState.tracks].sort((a, b) => {
      const titleA = a.title.split(' - ')[0] || a.title;
      const titleB = b.title.split(' - ')[0] || b.title;
      return titleA.localeCompare(titleB);
    });
  };
  
  const handleShuffleTracks = () => {
    if (!gameState) return;
    const tracks = [...gameState.tracks];
    for (let i = tracks.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [tracks[i], tracks[j]] = [tracks[j], tracks[i]];
    }
    setShuffledOrder(tracks.map(t => t.id));
    setTracksShuffled(true);
    setCurrentPage(1);
  };

  const getPaginatedTracks = (): { tracks: Track[]; totalPages: number } => {
    const allTracks = getShuffledTracks();
    const totalPages = Math.ceil(allTracks.length / tracksPerPage);
    const startIndex = (currentPage - 1) * tracksPerPage;
    const endIndex = startIndex + tracksPerPage;
    const paginatedTracks = allTracks.slice(startIndex, endIndex);
    return { tracks: paginatedTracks, totalPages };
  };


  const getCurrentTrack = (): Track | undefined => {
    if (!gameState || !gameState.current_track_id) return undefined;
    return gameState.tracks.find(t => t.id === gameState.current_track_id);
  };

  const getPlayersInBuzzOrder = (): Player[] => {
    if (!gameState) return [];
    return gameState.buzz_queue
      .map(pid => gameState.players[pid])
      .filter((p): p is Player => p !== undefined);
  };

  const getPlayersSortedByScore = (): Player[] => {
    if (!gameState) return [];
    return Object.values(gameState.players).sort((a, b) => b.score - a.score);
  };

  if (!joined) {
    return (
      <div className="organizer-container">
        <div className="join-form">
          <h1>Organizador</h1>
          <input
            type="text"
            placeholder="Tu nombre"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && name.trim() && setJoined(true)}
          />
          <button onClick={() => name.trim() && setJoined(true)} disabled={!name.trim()}>
            Entrar como Organizador
          </button>
        </div>
      </div>
    );
  }

  const handleBackToHome = () => {
    window.location.href = '/';
  };

  return (
    <div className="organizer-container">
      <div className="organizer-header">
        <div className="header-left">
          <h1>🎵 Organizador</h1>
          <div className="connection-status">
            {connected ? '🟢 Conectado' : '🔴 Desconectado'}
          </div>
        </div>
        <button onClick={handleBackToHome} className="back-to-menu-button" title="Volver al menú principal">
          🏠 Volver al Menú
        </button>
        </div>
      </div>

      <audio ref={audioRef} preload="auto" />

      <div className="playlist-import-section">
        <h2>Importar Playlist</h2>
        <div className="playlist-source-selector">
          <label>
            <input
              type="radio"
              value="spotify"
              checked={playlistSource === 'spotify'}
              onChange={(e) => setPlaylistSource(e.target.value as 'spotify' | 'youtube')}
              disabled={importing}
            />
            Spotify
          </label>
          <label>
            <input
              type="radio"
              value="youtube"
              checked={playlistSource === 'youtube'}
              onChange={(e) => setPlaylistSource(e.target.value as 'spotify' | 'youtube')}
              disabled={importing}
            />
            YouTube Music
          </label>
        </div>
        {playlistSource === 'youtube' && (
          <div className="youtube-auth-section">
            {checkingAuth ? (
              <p>Verificando autenticación...</p>
            ) : youtubeAuthenticated ? (
              <div className="auth-status success">
                ✅ Autenticado con YouTube - Importación rápida habilitada
              </div>
            ) : (
              <div className="auth-status warning">
                <p>⚠️ Sin autenticación: la importación puede ser lenta o bloqueada por YouTube</p>
                <button 
                  type="button"
                  onClick={handleYoutubeAuth}
                  className="youtube-auth-button"
                >
                  🔐 Iniciar sesión con YouTube (Recomendado)
                </button>
              </div>
            )}
          </div>
        )}
        {loadingAudio && (
          <div className="loading-audio">
            🎵 Cargando audio...
          </div>
        )}
        <form onSubmit={handleImportPlaylist}>
          <input
            type="text"
            placeholder={
              playlistSource === 'spotify'
                ? "URL de playlist de Spotify (ej: https://open.spotify.com/playlist/...)"
                : "URL de playlist de YouTube Music (ej: https://music.youtube.com/playlist?list=...)"
            }
            value={playlistUrl}
            onChange={(e) => {
              const url = e.target.value;
              setPlaylistUrl(url);
              if (url.includes('youtube.com') || url.includes('music.youtube.com') || url.includes('youtu.be')) {
                setPlaylistSource('youtube');
              } else if (url.includes('spotify.com') || url.includes('open.spotify.com')) {
                setPlaylistSource('spotify');
              }
            }}
            disabled={importing}
          />
          <button type="submit" disabled={importing || !playlistUrl.trim()}>
            {importing ? 'Importando...' : 'Importar Playlist'}
          </button>
        </form>
        {importError && (
          <div className="error-message">
            <p>{importError}</p>
            <button onClick={() => setImportError(null)}>Cerrar</button>
          </div>
        )}
        {importSuccess && (
          <div className="success-message">
            <p>{importSuccess}</p>
            <button onClick={() => setImportSuccess(null)}>Cerrar</button>
          </div>
        )}
      </div>

      {gameState && gameState.tracks.length > 0 && (
        <>
          <div className="tracks-section">
            <div className="tracks-section-header">
              <h2>Lista de Canciones {tracksShuffled ? '(Desordenadas)' : '(Ordenadas)'}</h2>
              {!tracksShuffled && (
                <button
                  onClick={handleShuffleTracks}
                  className="shuffle-button"
                  title="Desordenar canciones una vez"
                >
                  🔀 Desordenar
                </button>
              )}
            </div>
            {(() => {
              const { tracks: paginatedTracks, totalPages } = getPaginatedTracks();
              return (
                <>
                  <div className="tracks-grid">
                    {paginatedTracks.map((track) => {
                      const parts = track.title.split(' - ');
                      const trackTitle = parts[0] || track.title;
                      const trackArtist = parts.slice(1).join(' - ') || track.artist || 'Artista desconocido';
                      
                      return (
                        <div
                          key={track.id}
                          className={`track-card ${gameState.current_track_id === track.id ? 'active' : ''}`}
                        >
                          {track.image_url && (
                            <div className="track-image-container">
                              <img 
                                src={track.image_url} 
                                alt={trackTitle}
                                className="track-image"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = 'none';
                                }}
                              />
                            </div>
                          )}
                          <div className="track-title-container">
                            <h3 className="track-title">{trackTitle}</h3>
                          </div>
                          <div className="track-artist-container">
                            <p className="track-artist">{trackArtist}</p>
                          </div>
                          <button
                            className="select-track-button"
                            onClick={() => selectTrack(track.id)}
                            disabled={gameState.current_track_id === track.id}
                          >
                            {gameState.current_track_id === track.id ? '▶ Reproduciendo' : '▶ Seleccionar'}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                  {totalPages > 1 && (
                    <div className="pagination">
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                        className="pagination-button"
                      >
                        « Anterior
                      </button>
                      <span className="pagination-info">
                        Página {currentPage} de {totalPages}
                      </span>
                      <button
                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                        disabled={currentPage === totalPages}
                        className="pagination-button"
                      >
                        Siguiente »
                      </button>
                    </div>
                  )}
                </>
              );
            })()}
          </div>

          <div className="controls-section">
            <h2>Controles de Reproducción</h2>
            <div className="controls-grid">
              <button onClick={() => control('play')} disabled={gameState.status === 'playing'}>
                ▶️ Play
              </button>
              <button onClick={() => control('pause')} disabled={gameState.status === 'paused'}>
                ⏸️ Pausa
              </button>
              <button onClick={() => control('stop')} disabled={gameState.status === 'stopped'}>
                ⏹️ Stop
              </button>
              <button onClick={() => control('preview2')}>
                ⏩ Preview 2s
              </button>
              <button onClick={() => control('preview5')}>
                ⏩⏩ Preview 5s
              </button>
              <button onClick={nextTrack}>
                ⏭️ Siguiente Canción
              </button>
            </div>
            {getCurrentTrack() && (
              <div className="current-track-info">
                <p><strong>Reproduciendo:</strong> {getCurrentTrack()?.title}</p>
                <p><strong>Estado:</strong> {gameState.status}</p>
              </div>
            )}
          </div>

          {gameState.current_track_id && (() => {
            const currentTrack = gameState.tracks.find(t => t.id === gameState.current_track_id);
            if (!currentTrack) return null;

            // Extraer artista y nombre de canción
            // El formato del título es: "Nombre de Canción - Artista"
            // O puede tener el artista en el campo currentTrack.artist
            const titleParts = currentTrack.title.split(' - ');
            
            let artist = '';
            let songName = '';
            
            if (currentTrack.artist) {
              // Si hay campo artist, usarlo directamente
              artist = currentTrack.artist.trim();
              // El nombre de la canción es la primera parte del título (antes del " - ")
              songName = titleParts[0].trim();
            } else if (titleParts.length > 1) {
              // Si no hay campo artist pero hay separador, asumir formato "Canción - Artista"
              songName = titleParts[0].trim();
              artist = titleParts[1].trim();
            } else {
              // Si no hay separador ni campo artist, usar todo el título como canción
              songName = titleParts[0].trim();
              artist = '';
            }

            // Normalizar para URL (minúsculas, reemplazar espacios y caracteres especiales)
            const normalizeForUrl = (text: string): string => {
              if (!text) return '';
              return text
                .toLowerCase()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '') // Eliminar acentos
                .replace(/[^a-z0-9]+/g, '-') // Reemplazar caracteres especiales con guiones
                .replace(/^-+|-+$/g, ''); // Eliminar guiones al inicio y final
            };

            const artistSlug = normalizeForUrl(artist);
            const songSlug = normalizeForUrl(songName);
            const lyricsUrl = `https://www.letras.com/${artistSlug}/${songSlug}`;

            return (
              <div className="lyrics-section">
                <h2>Letra de la Canción</h2>
                <div className="lyrics-button-container">
                  <a
                    href={lyricsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="lyrics-button"
                  >
                    📝 Ver letra en Letras.com
                  </a>
                </div>
              </div>
            );
          })()}

          <div className="buzzers-section">
            <h2>Orden de Buzzers</h2>
            {getPlayersInBuzzOrder().length === 0 ? (
              <p>Nadie ha presionado el buzzer aún</p>
            ) : (
              <ol>
                {getPlayersInBuzzOrder().map((player, index) => (
                  <li key={player.id}>
                    {index + 1}. {player.name} (Score: {player.score})
                  </li>
                ))}
              </ol>
            )}
          </div>

          <div className="winner-section">
            <h2>Gestionar Puntos</h2>
            {getPlayersInBuzzOrder().length === 0 ? (
              <p>Esperando que alguien presione el buzzer...</p>
            ) : (
              <div className="winner-buttons">
                {getPlayersInBuzzOrder().map((player) => (
                  <div key={player.id} className="score-control-row">
                    <span className="player-name">{player.name}</span>
                    <div className="score-buttons">
                      <button
                        onClick={() => adjustScore(player.id, -1)}
                        className="score-button score-button-minus"
                        title="Restar 1 punto"
                      >
                        -1
                      </button>
                      <button
                        onClick={() => setWinner(player.id)}
                        className="score-button score-button-plus"
                        title="Sumar 1 punto"
                      >
                        +1
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="scores-section">
            <h2>Scoreboard</h2>
            {getPlayersSortedByScore().length === 0 ? (
              <p>No hay jugadores conectados</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Posición</th>
                    <th>Nombre</th>
                    <th>Puntos</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {getPlayersSortedByScore().map((player, index) => (
                    <tr key={player.id}>
                      <td>{index + 1}</td>
                      <td>{player.name}</td>
                      <td>{player.score}</td>
                      <td>
                        <div className="player-actions">
                          <button
                            onClick={() => adjustScore(player.id, 1)}
                            className="score-button score-button-plus"
                            title="Sumar 1 punto"
                          >
                            +1
                          </button>
                          <button
                            onClick={() => adjustScore(player.id, -1)}
                            className="score-button score-button-minus"
                            title="Restar 1 punto"
                          >
                            -1
                          </button>
                          <button
                            onClick={() => removePlayer(player.id)}
                            className="remove-player-button"
                            title="Eliminar jugador"
                          >
                            🗑️ Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {gameState && gameState.tracks.length === 0 && (
        <div className="no-tracks-message">
          <p>No hay canciones cargadas. Importa una playlist de Spotify para comenzar.</p>
        </div>
      )}
    </div>
  );
}
