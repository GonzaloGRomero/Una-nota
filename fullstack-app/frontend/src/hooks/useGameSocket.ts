import { useEffect, useRef, useState, useCallback } from 'react';
import { GameState, Player, ControlAction } from '../types';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/sala';

export type GameSocketMessage =
  | { type: 'state'; payload: GameState }
  | { type: 'player_join'; payload: Player }
  | { type: 'player_leave'; payload: { playerId: string } }
  | { type: 'buzzer'; payload: { queue: string[] } }
  | { type: 'control'; payload: { status: string } }
  | { type: 'scores'; payload: { players: Record<string, Player> } }
  | { type: 'track_changed'; payload: { currentTrackId: string } }
  | { type: 'join_ack'; payload: { playerId: string | null; isReused?: boolean } }
  | { type: 'join_error'; payload: { message: string } }
  | { type: 'point_awarded'; payload: { playerId: string; playerName: string; points: number; track: { title: string; artist: string } } }
  | { type: 'player_rejoin'; payload: Player };

export function useGameSocket() {
  const [connected, setConnected] = useState(false);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [playerId, setPlayerId] = useState<string | null>(null);
  const [lastPointAwarded, setLastPointAwarded] = useState<{ playerId: string; playerName: string; points: number; track: { title: string; artist: string } } | null>(null);
  const [joinError, setJoinError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pointAwardedTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const joinErrorRef = useRef<string | null>(null);
  const connectParamsRef = useRef<{ name: string; role: 'player' | 'organizer'; roomName: string; password: string } | null>(null);
  const isConnectingRef = useRef<boolean>(false);

  const connect = useCallback((name: string, role: 'player' | 'organizer' = 'player', roomName: string, password: string) => {
    if (isConnectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    isConnectingRef.current = true;
    connectParamsRef.current = { name, role, roomName, password };
    
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {
        // Ignorar errores al cerrar
      }
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setJoinError(null);
    joinErrorRef.current = null;
    setConnected(false);

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WebSocket] Conexión abierta, enviando join...');
      setConnected(true);
      isConnectingRef.current = false;
      const joinMessage = { type: 'join', name, role, room_name: roomName, password: password };
      console.log('[WebSocket] Enviando join:', joinMessage);
      ws.send(JSON.stringify(joinMessage));
    };

    ws.onmessage = (event) => {
      const message: GameSocketMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'join_ack':
          setJoinError(null);
          joinErrorRef.current = null;
          setConnected(true);
          isConnectingRef.current = false;
          if (message.payload.playerId) {
            setPlayerId(message.payload.playerId);
          }
          break;
        case 'join_error':
          const errorMsg = message.payload.message;
          setJoinError(errorMsg);
          joinErrorRef.current = errorMsg;
          isConnectingRef.current = false;
          setConnected(false);
          if (wsRef.current === ws) {
            ws.close();
            wsRef.current = null;
          }
          connectParamsRef.current = null;
          break;
        case 'state':
          setGameState(message.payload);
          break;
        case 'player_join':
        case 'player_rejoin':
          setGameState(prev => {
            if (!prev) return prev;
            return {
              ...prev,
              players: {
                ...prev.players,
                [message.payload.id]: message.payload
              }
            };
          });
          break;
        case 'player_leave':
          setGameState(prev => {
            if (!prev) return prev;
            const newPlayers = { ...prev.players };
            delete newPlayers[message.payload.playerId];
            return {
              ...prev,
              players: newPlayers,
              buzz_queue: prev.buzz_queue.filter(id => id !== message.payload.playerId)
            };
          });
          break;
        case 'buzzer':
          setGameState(prev => prev ? { ...prev, buzz_queue: message.payload.queue } : null);
          break;
        case 'control':
          setGameState(prev => prev ? { ...prev, status: message.payload.status as GameState['status'] } : null);
          break;
        case 'scores':
          setGameState(prev => prev ? { ...prev, players: message.payload.players } : null);
          break;
        case 'track_changed':
          setGameState(prev => prev ? { ...prev, current_track_id: message.payload.currentTrackId } : null);
          break;
        case 'point_awarded':
          if (pointAwardedTimeoutRef.current) {
            clearTimeout(pointAwardedTimeoutRef.current);
          }
          setLastPointAwarded(message.payload);
          pointAwardedTimeoutRef.current = setTimeout(() => {
            setLastPointAwarded(null);
            pointAwardedTimeoutRef.current = null;
          }, 5000);
          break;
      }
    };

    ws.onerror = () => {
      // Error manejado silenciosamente
    };

    ws.onclose = () => {
      setConnected(false);
      const shouldReconnect = wsRef.current === ws && !joinErrorRef.current;
      if (shouldReconnect && connectParamsRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          if (connectParamsRef.current) {
            connect(
              connectParamsRef.current.name,
              connectParamsRef.current.role,
              connectParamsRef.current.roomName,
              connectParamsRef.current.password
            );
          }
        }, 3000);
      } else {
        wsRef.current = null;
      }
    };
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    connectParamsRef.current = null;
    isConnectingRef.current = false;
    joinErrorRef.current = null;
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
    setPlayerId(null);
    setGameState(null);
    setJoinError(null);
  }, []);

  const sendMessage = useCallback((message: any) => {
    console.log('[WebSocket] sendMessage llamado:', message, 'readyState:', wsRef.current?.readyState, 'OPEN:', WebSocket.OPEN);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Enviando mensaje:', message);
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] No se puede enviar mensaje, WebSocket no está abierto. ReadyState:', wsRef.current?.readyState, 'Esperado:', WebSocket.OPEN);
      console.warn('[WebSocket] wsRef.current existe:', wsRef.current !== null, 'connected state:', connected);
    }
  }, [connected]);

  const buzz = useCallback(() => {
    if (playerId) {
      sendMessage({ type: 'buzz', playerId });
    }
  }, [playerId, sendMessage]);

  const control = useCallback((action: ControlAction) => {
    sendMessage({ type: 'control', action });
  }, [sendMessage]);

  const setWinner = useCallback((winnerPlayerId: string) => {
    sendMessage({ type: 'set_winner', playerId: winnerPlayerId });
  }, [sendMessage]);

  const adjustScore = useCallback((playerId: string, points: number) => {
    sendMessage({ type: 'adjust_score', playerId, points });
  }, [sendMessage]);

  const nextTrack = useCallback(() => {
    sendMessage({ type: 'next_track' });
  }, [sendMessage]);

  const selectTrack = useCallback((trackId: string) => {
    sendMessage({ type: 'select_track', trackId });
  }, [sendMessage]);

  const removePlayer = useCallback((playerId: string) => {
    sendMessage({ type: 'remove_player', playerId });
  }, [sendMessage]);

  useEffect(() => {
    return () => {
      disconnect();
      if (pointAwardedTimeoutRef.current) {
        clearTimeout(pointAwardedTimeoutRef.current);
      }
    };
  }, [disconnect]);

  return {
    connected,
    gameState,
    playerId,
    lastPointAwarded,
    joinError,
    connect,
    disconnect,
    buzz,
    control,
    setWinner,
    adjustScore,
    nextTrack,
    selectTrack,
    removePlayer,
  };
}
