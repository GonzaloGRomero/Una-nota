import asyncio
import json
import os
import random
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import spotipy
import yt_dlp
import requests
import bcrypt
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel
from spotipy.oauth2 import SpotifyClientCredentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest

app = FastAPI(title="Music Buzzer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://una-nota-two.vercel.app",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenamiento de tokens OAuth2 (en memoria, por sesión)
youtube_oauth_tokens: Dict[str, Credentials] = {}

# Archivo para persistir tokens de YouTube
YOUTUBE_TOKENS_FILE = Path(__file__).parent / "youtube_tokens.json"

def save_youtube_tokens():
    """Guarda los tokens de YouTube en un archivo JSON"""
    try:
        tokens_data = {}
        for session_id, credentials in youtube_oauth_tokens.items():
            if credentials and credentials.token:
                tokens_data[session_id] = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes,
                    'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                }
        
        with open(YOUTUBE_TOKENS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens_data, f, indent=2)
    except Exception as e:
        print(f"Error guardando tokens de YouTube: {e}")

def load_youtube_tokens():
    """Carga los tokens de YouTube desde el archivo JSON"""
    if not YOUTUBE_TOKENS_FILE.exists():
        return
    
    try:
        with open(YOUTUBE_TOKENS_FILE, 'r', encoding='utf-8') as f:
            tokens_data = json.load(f)
        
        for session_id, token_info in tokens_data.items():
            try:
                credentials = Credentials(
                    token=token_info.get('token'),
                    refresh_token=token_info.get('refresh_token'),
                    token_uri=token_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=token_info.get('client_id', GOOGLE_CLIENT_ID),
                    client_secret=token_info.get('client_secret', GOOGLE_CLIENT_SECRET),
                    scopes=token_info.get('scopes', SCOPES),
                )
                
                if token_info.get('expiry'):
                    credentials.expiry = datetime.fromisoformat(token_info['expiry'])
                
                # Verificar si el token es válido o puede refrescarse
                if not credentials.valid:
                    if credentials.refresh_token:
                        try:
                            credentials.refresh(GoogleRequest())
                            save_youtube_tokens()
                        except:
                            continue
                    else:
                        continue
                
                youtube_oauth_tokens[session_id] = credentials
            except Exception as e:
                print(f"Error cargando token para sesión {session_id}: {e}")
                continue
    except Exception as e:
        print(f"Error cargando tokens de YouTube: {e}")

# Cargar tokens al iniciar el servidor
load_youtube_tokens()

# Configuración OAuth2 de Google/YouTube
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://juego-en-una-nota-production.up.railway.app/auth/youtube/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://una-nota-two.vercel.app")

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']

# Contraseña de administrador (hasheada)
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
ADMIN_PASSWORD_PLAIN = os.getenv("ADMIN_PASSWORD", "admin123")  # Solo para desarrollo, cambiar en producción


class Track(BaseModel):
    id: str
    title: str
    url: str
    artist: Optional[str] = None
    video_id: Optional[str] = None  # Para carga bajo demanda de YouTube
    image_url: Optional[str] = None  # URL de la imagen del álbum/thumbnail
    lyrics: Optional[str] = None  # Letra de la canción


class Player(BaseModel):
    id: str
    name: str
    score: int = 0


class GameState(BaseModel):
    tracks: List[Track]
    track_order: List[str]
    current_track_id: Optional[str]
    status: str  # playing | paused | stopped | preview2 | preview5
    buzz_queue: List[str]
    players: Dict[str, Player]


class PlaylistImport(BaseModel):
    playlist_url: str
    source: Optional[str] = None  # "spotify" o "youtube", None para auto-detectar
    room_name: Optional[str] = None  # Nombre de la sala (requerido para salas)


class CreateRoomRequest(BaseModel):
    room_name: str
    password: str


class JoinRoomRequest(BaseModel):
    room_name: str
    password: str


class AdminAuthRequest(BaseModel):
    password: str


class CloseRoomRequest(BaseModel):
    room_name: str
    admin_password: str


class BanPlayerRequest(BaseModel):
    room_name: str
    player_id: str
    admin_password: str


TRACKS: List[Track] = [
    Track(id="t1", title="Track 1", url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"),
    Track(id="t2", title="Track 2", url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"),
    Track(id="t3", title="Track 3", url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"),
]


# Archivo para persistir scores
SCORES_FILE = Path(__file__).parent / "scores.json"

def load_scores() -> Dict[str, Dict]:
    """Carga los scores guardados del archivo JSON"""
    if not SCORES_FILE.exists():
        return {}
    
    try:
        with open(SCORES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Verificar si los datos son antiguos (más de 1 día)
        if 'timestamp' in data:
            saved_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - saved_time > timedelta(days=1):
                # Los datos son antiguos, limpiar
                return {}
        
        return data.get('players', {})
    except Exception as e:
        print(f"Error cargando scores: {e}")
        return {}

def save_scores(players: Dict[str, Player]) -> None:
    """Guarda los scores en el archivo JSON, manteniendo los scores históricos"""
    try:
        # Cargar scores existentes para mantener los históricos
        existing_scores = load_scores()
        
        # Actualizar o agregar los scores de los jugadores actuales
        for player_id, player in players.items():
            # Buscar si existe un jugador con el mismo nombre en los scores guardados
            # (puede tener un ID diferente si se reconectó)
            found_by_name = False
            for saved_id, saved_data in existing_scores.items():
                if saved_data['name'].strip().lower() == player.name.strip().lower():
                    # Actualizar el score del jugador existente (mantener el ID original)
                    existing_scores[saved_id] = {
                        'id': saved_id,  # Mantener el ID original
                        'name': player.name,
                        'score': player.score
                    }
                    found_by_name = True
                    break
            
            # Si no se encontró por nombre, agregar nuevo jugador
            if not found_by_name:
                existing_scores[player_id] = {
                    'id': player.id,
                    'name': player.name,
                    'score': player.score
                }
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'players': existing_scores
        }
        
        with open(SCORES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando scores: {e}")

class Room:
    def __init__(self, tracks: List[Track]) -> None:
        self.tracks = tracks
        self.track_order: List[str] = []
        self.current_track_id: Optional[str] = None
        self.status: str = "stopped"
        self.players: Dict[str, Player] = {}
        self.buzz_queue: List[str] = []
        self._lock = asyncio.Lock()
        self.reset_queue()
        # Cargar scores guardados
        self._load_persisted_scores()
    
    def _load_persisted_scores(self) -> None:
        """Carga los scores persistidos al inicializar (solo para referencia, no los carga como activos)"""
        persisted_scores = load_scores()
        if persisted_scores:
            print(f"Hay {len(persisted_scores)} jugadores con scores guardados (se cargarán cuando se conecten)")

    def reset_queue(self) -> None:
        self.track_order = [t.id for t in self.tracks]
        random.shuffle(self.track_order)
        self.current_track_id = self.track_order[0] if self.track_order else None
        self.status = "stopped"
        self.buzz_queue = []

    def to_state(self) -> GameState:
        return GameState(
            tracks=self.tracks,
            track_order=self.track_order,
            current_track_id=self.current_track_id,
            status=self.status,
            buzz_queue=self.buzz_queue,
            players=self.players,
        )

    async def add_player(self, name: str, active_player_ids: set) -> tuple[Optional[Player], bool]:
        """
        Agrega un jugador o reutiliza uno existente.
        Retorna (player, is_reused) donde:
        - player es None si el nombre está en uso por una conexión activa
        - is_reused es True si se reutilizó un jugador existente
        """
        async with self._lock:
            name_lower = name.strip().lower()
            name_clean = name.strip()
            
            # Buscar si existe un jugador con ese nombre en jugadores activos
            existing_player = None
            for player in self.players.values():
                if player.name.strip().lower() == name_lower:
                    existing_player = player
                    break
            
            if existing_player:
                # Si el jugador existe y está conectado, rechazar
                if existing_player.id in active_player_ids:
                    return (None, False)  # Nombre en uso por conexión activa
                # Si existe pero no está conectado, reutilizar manteniendo el score
                return (existing_player, True)
            
            # Buscar en scores persistidos por nombre
            persisted_scores = load_scores()
            persisted_player = None
            for saved_id, saved_data in persisted_scores.items():
                if saved_data['name'].strip().lower() == name_lower:
                    persisted_player = saved_data
                    break
            
            # Crear nuevo jugador o recuperar de persistencia
            if persisted_player:
                # Recuperar jugador con score guardado
                player = Player(
                    id=persisted_player['id'],
                    name=name_clean,
                    score=persisted_player['score']
                )
                self.players[persisted_player['id']] = player
                # Actualizar timestamp en persistencia
                save_scores(self.players)
                return (player, True)  # Es una reconexión
            else:
                # Crear nuevo jugador
                player_id = str(uuid.uuid4())
                player = Player(id=player_id, name=name_clean, score=0)
                self.players[player_id] = player
                # Guardar scores después de agregar jugador
                save_scores(self.players)
                return (player, False)

    async def remove_player(self, player_id: str) -> None:
        async with self._lock:
            # Guardar el score antes de remover (para mantenerlo en persistencia)
            player = self.players.get(player_id)
            if player:
                # Guardar el score antes de remover del diccionario activo
                save_scores(self.players)
            # Remover del diccionario activo (pero el score ya está guardado)
            self.players.pop(player_id, None)
            self.buzz_queue = [pid for pid in self.buzz_queue if pid != player_id]
            # No guardar después de remover, ya se guardó antes

    async def record_buzz(self, player_id: str) -> bool:
        async with self._lock:
            if player_id not in self.players:
                return False
            if player_id in self.buzz_queue:
                return False
            first_buzz = len(self.buzz_queue) == 0
            self.buzz_queue.append(player_id)
            if first_buzz:
                self.status = "paused"
            return True

    async def set_winner(self, player_id: str) -> Optional[Player]:
        async with self._lock:
            player = self.players.get(player_id)
            if not player:
                return None
            player.score += 1
            self.buzz_queue = []
            self.status = "stopped"
            # Guardar scores después de cambiar
            save_scores(self.players)
            return player
    
    async def adjust_score(self, player_id: str, points: int) -> Optional[Player]:
        """Ajusta la puntuación de un jugador (puede ser positivo o negativo)"""
        async with self._lock:
            player = self.players.get(player_id)
            if not player:
                return None
            player.score = player.score + points  # Permitir puntuación negativa
            # Guardar scores después de cambiar
            save_scores(self.players)
            return player

    async def set_status(self, status: str) -> None:
        async with self._lock:
            self.status = status
            if status == "stopped":
                self.buzz_queue = []

    async def next_track(self) -> None:
        async with self._lock:
            if not self.track_order:
                return
            idx = self.track_order.index(self.current_track_id) if self.current_track_id in self.track_order else -1
            next_idx = (idx + 1) % len(self.track_order)
            self.current_track_id = self.track_order[next_idx]
            self.status = "stopped"
            self.buzz_queue = []

    async def update_tracks(self, new_tracks: List[Track]) -> None:
        async with self._lock:
            self.tracks = new_tracks
            self.reset_queue()


class RoomManager:
    """Gestiona múltiples salas de juego"""
    def __init__(self):
        self.rooms: Dict[str, Dict] = {}  # room_name -> {password_hash, room_instance, created_at}
        self._lock = asyncio.Lock()
    
    async def create_room(self, room_name: str, password: str) -> bool:
        """Crea una nueva sala con contraseña hasheada"""
        async with self._lock:
            room_name_clean = room_name.strip().lower()
            if room_name_clean in self.rooms:
                return False  # Sala ya existe
            
            # Hash de la contraseña
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Crear nueva instancia de Room para esta sala
            new_room = Room(TRACKS.copy())
            
            self.rooms[room_name_clean] = {
                'password_hash': password_hash,
                'room': new_room,
                'created_at': datetime.now()
            }
            return True
    
    async def join_room(self, room_name: str, password: str) -> Optional[Room]:
        """Valida la contraseña y retorna la instancia de Room si es correcta"""
        async with self._lock:
            room_name_clean = room_name.strip().lower()
            if room_name_clean not in self.rooms:
                return None  # Sala no existe
            
            room_data = self.rooms[room_name_clean]
            password_hash = room_data['password_hash']
            
            # Verificar contraseña
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return room_data['room']
            return None
    
    async def room_exists(self, room_name: str) -> bool:
        """Verifica si una sala existe"""
        async with self._lock:
            room_name_clean = room_name.strip().lower()
            return room_name_clean in self.rooms
    
    async def get_room(self, room_name: str) -> Optional[Room]:
        """Obtiene la instancia de Room sin validar contraseña (para uso interno)"""
        async with self._lock:
            room_name_clean = room_name.strip().lower()
            if room_name_clean in self.rooms:
                return self.rooms[room_name_clean]['room']
            return None
    
    async def list_rooms(self) -> List[Dict]:
        """Lista todas las salas activas con información"""
        async with self._lock:
            rooms_info = []
            for room_name, room_data in self.rooms.items():
                room_instance = room_data['room']
                created_at = room_data.get('created_at', datetime.now())
                rooms_info.append({
                    'name': room_name,
                    'created_at': created_at.isoformat(),
                    'player_count': len(room_instance.players),
                    'track_count': len(room_instance.tracks),
                    'current_track_id': room_instance.current_track_id,
                    'status': room_instance.status
                })
            return rooms_info
    
    async def close_room(self, room_name: str) -> bool:
        """Cierra y elimina una sala"""
        async with self._lock:
            room_name_clean = room_name.strip().lower()
            if room_name_clean in self.rooms:
                del self.rooms[room_name_clean]
                return True
            return False
    
    async def get_room_info(self, room_name: str) -> Optional[Dict]:
        """Obtiene información detallada de una sala"""
        async with self._lock:
            room_name_clean = room_name.strip().lower()
            if room_name_clean not in self.rooms:
                return None
            
            room_instance = self.rooms[room_name_clean]['room']
            room_data = self.rooms[room_name_clean]
            
            return {
                'name': room_name_clean,
                'created_at': room_data.get('created_at', datetime.now()).isoformat(),
                'players': {pid: p.model_dump() for pid, p in room_instance.players.items()},
                'player_count': len(room_instance.players),
                'tracks': [t.model_dump() for t in room_instance.tracks],
                'track_count': len(room_instance.tracks),
                'current_track_id': room_instance.current_track_id,
                'status': room_instance.status,
                'buzz_queue': room_instance.buzz_queue
            }


room_manager = RoomManager()
room = Room(TRACKS)  # Mantener para compatibilidad temporal


class ConnectionManager:
    def __init__(self) -> None:
        self.active: Dict[WebSocket, Dict[str, Optional[str]]] = {}
        self.rooms: Dict[str, List[WebSocket]] = {}  # room_name -> [websockets]

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active[websocket] = {"player_id": None, "role": None, "room_name": None}

    def set_identity(self, websocket: WebSocket, player_id: Optional[str], role: Optional[str], room_name: Optional[str] = None) -> None:
        if websocket in self.active:
            self.active[websocket]["player_id"] = player_id
            self.active[websocket]["role"] = role
            if room_name:
                self.active[websocket]["room_name"] = room_name
                # Agregar a la lista de conexiones de la sala
                if room_name not in self.rooms:
                    self.rooms[room_name] = []
                if websocket not in self.rooms[room_name]:
                    self.rooms[room_name].append(websocket)

    def disconnect(self, websocket: WebSocket) -> Optional[str]:
        info = self.active.pop(websocket, None)
        room_name = info.get("room_name") if info else None
        if room_name and room_name in self.rooms:
            self.rooms[room_name] = [ws for ws in self.rooms[room_name] if ws != websocket]
            if not self.rooms[room_name]:
                del self.rooms[room_name]
        return info.get("player_id") if info else None
    
    def get_active_player_ids(self, room_name: Optional[str] = None) -> set:
        """Retorna un set con los IDs de jugadores activos (conectados) en una sala específica"""
        if room_name:
            room_websockets = self.rooms.get(room_name, [])
            return {self.active[ws]["player_id"] for ws in room_websockets if self.active.get(ws, {}).get("player_id")}
        return {info["player_id"] for info in self.active.values() if info.get("player_id")}

    async def broadcast(self, message: Dict, room_name: Optional[str] = None) -> None:
        """Broadcast a todos los clientes o solo a los de una sala específica"""
        if room_name:
            targets = self.rooms.get(room_name, [])
        else:
            targets = list(self.active.keys())
        
        dead = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


def build_state_message(room_instance: Optional[Room] = None) -> Dict:
    target_room = room_instance or room
    return {"type": "state", "payload": target_room.to_state().model_dump()}


@app.get("/tracks", response_model=List[Track])
async def get_tracks():
    random_order = room.track_order.copy()
    random.shuffle(random_order)
    order_index = {tid: i for i, tid in enumerate(random_order)}
    return sorted(TRACKS, key=lambda t: order_index.get(t.id, 0))


@app.get("/state", response_model=GameState)
async def get_state():
    return room.to_state()


@app.websocket("/ws/sala")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    current_room: Optional[Room] = None
    room_name: Optional[str] = None
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "join":
                try:
                    name = data.get("name", "Jugador")
                    role = data.get("role", "player")
                    room_name_param = data.get("room_name")
                    password = data.get("password", "")
                    
                    print(f"[DEBUG] Received join: name={name}, role={role}, room_name={room_name_param}")
                    
                    # Validar sala y contraseña
                    if not room_name_param:
                        await websocket.send_json({
                            "type": "join_error",
                            "payload": {"message": "Nombre de sala requerido"}
                        })
                        continue
                    
                    room_instance = await room_manager.join_room(room_name_param, password)
                    if not room_instance:
                        await websocket.send_json({
                            "type": "join_error",
                            "payload": {"message": "Nombre de sala o contraseña incorrectos"}
                        })
                        continue
                    
                    # Sala válida, usar esta instancia
                    current_room = room_instance
                    room_name = room_name_param.strip().lower()
                    
                    if role == "player":
                        active_ids = manager.get_active_player_ids(room_name)
                        print(f"[DEBUG] Active player IDs in room {room_name}: {active_ids}")
                        player, is_reused = await current_room.add_player(name, active_ids)
                        print(f"[DEBUG] Player created/reused: {player.id if player else None}, is_reused={is_reused}")
                        if player is None:
                            # Nombre en uso por conexión activa
                            print(f"[DEBUG] Player name '{name}' already in use by active connection")
                            await websocket.send_json({
                                "type": "join_error",
                                "payload": {"message": "Este nombre ya está en uso por un jugador conectado. Por favor elige otro nombre."}
                            })
                        else:
                            manager.set_identity(websocket, player.id, role, room_name)
                            print(f"[DEBUG] Set identity: player_id={player.id}, role={role}, room={room_name}")
                            if is_reused:
                                # Si se reutilizó, notificar que el jugador volvió
                                await manager.broadcast({"type": "player_rejoin", "payload": player.model_dump()}, room_name)
                            else:
                                # Si es nuevo, notificar normalmente
                                await manager.broadcast({"type": "player_join", "payload": player.model_dump()}, room_name)
                            print(f"[DEBUG] Sending join_ack for player {player.id}")
                            await websocket.send_json({"type": "join_ack", "payload": {"playerId": player.id, "isReused": is_reused}})
                            await websocket.send_json(build_state_message(current_room))
                            print(f"[DEBUG] Join completed successfully for player {player.id}")
                    else:
                        manager.set_identity(websocket, None, role, room_name)
                        await websocket.send_json({"type": "join_ack", "payload": {"playerId": None}})
                        await websocket.send_json(build_state_message(current_room))
                except Exception as e:
                    print(f"[ERROR] Error processing join message: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    await websocket.send_json({
                        "type": "join_error",
                        "payload": {"message": f"Error procesando la solicitud: {str(e)}"}
                    })
            else:
                # Para otros mensajes, obtener la sala de la conexión
                if not current_room:
                    room_name_from_ws = manager.active.get(websocket, {}).get("room_name")
                    if room_name_from_ws:
                        current_room = await room_manager.get_room(room_name_from_ws)
                        room_name = room_name_from_ws
                
                if not current_room:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Debes unirte a una sala primero"}
                    })
                    continue
                
                if msg_type == "buzz":
                    player_id = data.get("playerId")
                    accepted = await current_room.record_buzz(player_id)
                    if accepted:
                        await manager.broadcast({"type": "buzzer", "payload": {"queue": current_room.buzz_queue}}, room_name)
                        await manager.broadcast({"type": "control", "payload": {"status": current_room.status}}, room_name)
                elif msg_type == "control":
                    action = data.get("action")
                    if action in {"play", "pause", "stop", "preview2", "preview5"}:
                        status_map = {
                            "play": "playing",
                            "pause": "paused",
                            "stop": "stopped",
                            "preview2": "preview2",
                            "preview5": "preview5",
                        }
                        await current_room.set_status(status_map[action])
                        await manager.broadcast({"type": "control", "payload": {"status": current_room.status}}, room_name)
                elif msg_type == "set_winner":
                    player_id = data.get("playerId")
                    winner = await current_room.set_winner(player_id)
                    if winner:
                        # Obtener información de la canción actual
                        current_track = next((t for t in current_room.tracks if t.id == current_room.current_track_id), None)
                        track_info = {}
                        if current_track:
                            # Parsear título y artista
                            parts = current_track.title.split(' - ', 1)
                            track_info = {
                                "title": parts[0] if parts else current_track.title,
                                "artist": parts[1] if len(parts) > 1 else "Artista desconocido"
                            }
                        await manager.broadcast({"type": "scores", "payload": {"players": {pid: p.model_dump() for pid, p in current_room.players.items()}}}, room_name)
                        await manager.broadcast({"type": "buzzer", "payload": {"queue": current_room.buzz_queue}}, room_name)
                        await manager.broadcast({"type": "control", "payload": {"status": current_room.status}}, room_name)
                        await manager.broadcast({"type": "point_awarded", "payload": {"playerId": player_id, "playerName": winner.name, "points": 1, "track": track_info}}, room_name)
                elif msg_type == "adjust_score":
                    player_id = data.get("playerId")
                    points = data.get("points", 0)
                    adjusted_player = await current_room.adjust_score(player_id, points)
                    if adjusted_player:
                        # Obtener información de la canción actual
                        current_track = next((t for t in current_room.tracks if t.id == current_room.current_track_id), None)
                        track_info = {}
                        if current_track:
                            # Parsear título y artista
                            parts = current_track.title.split(' - ', 1)
                            track_info = {
                                "title": parts[0] if parts else current_track.title,
                                "artist": parts[1] if len(parts) > 1 else "Artista desconocido"
                            }
                        await manager.broadcast({"type": "scores", "payload": {"players": {pid: p.model_dump() for pid, p in current_room.players.items()}}}, room_name)
                        await manager.broadcast({"type": "point_awarded", "payload": {"playerId": player_id, "playerName": adjusted_player.name, "points": points, "track": track_info}}, room_name)
                elif msg_type == "next_track":
                    await current_room.next_track()
                    await manager.broadcast({"type": "track_changed", "payload": {"currentTrackId": current_room.current_track_id}}, room_name)
                    await manager.broadcast({"type": "control", "payload": {"status": current_room.status}}, room_name)
                elif msg_type == "select_track":
                    track_id = data.get("trackId")
                    if track_id:
                        async with current_room._lock:
                            if any(t.id == track_id for t in current_room.tracks):
                                current_room.current_track_id = track_id
                                current_room.status = "stopped"
                                current_room.buzz_queue = []
                        await manager.broadcast({"type": "track_changed", "payload": {"currentTrackId": current_room.current_track_id}}, room_name)
                        await manager.broadcast({"type": "control", "payload": {"status": current_room.status}}, room_name)
                elif msg_type == "remove_player":
                    player_id_to_remove = data.get("playerId")
                    if player_id_to_remove:
                        await current_room.remove_player(player_id_to_remove)
                        await manager.broadcast({"type": "player_leave", "payload": {"playerId": player_id_to_remove}}, room_name)
                        await manager.broadcast(build_state_message(current_room), room_name)
    except WebSocketDisconnect:
        player_id = manager.disconnect(websocket)
        if player_id and room_name:
            room_instance = await room_manager.get_room(room_name)
            if room_instance:
                await room_instance.remove_player(player_id)
                await manager.broadcast({"type": "player_leave", "payload": {"playerId": player_id}}, room_name)
                await manager.broadcast(build_state_message(room_instance), room_name)


def get_youtube_cookies_path() -> Optional[str]:
    """Obtiene la ruta del archivo de cookies de YouTube si existe y no está vacío"""
    cookies_path = os.getenv('YOUTUBE_COOKIES_FILE')
    if cookies_path and os.path.exists(cookies_path):
        # Verificar que el archivo no esté vacío
        if os.path.getsize(cookies_path) > 0:
            return cookies_path
    # También buscar en el directorio del backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(backend_dir, 'youtube_cookies.txt')
    if os.path.exists(default_path) and os.path.getsize(default_path) > 0:
        return default_path
    return None


def search_youtube_audio_url(track_name: str, artist_name: str) -> Optional[str]:
    """Busca una canción en YouTube y retorna la URL de audio"""
    try:
        # Limpiar nombres para mejor búsqueda
        clean_track = track_name.strip()
        clean_artist = artist_name.strip().split(',')[0]  # Tomar solo el primer artista
        query = f"{clean_track} {clean_artist}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'incomplete',  # Extraer información básica primero para evitar bloqueos
            'default_search': 'ytsearch1',
            'noplaylist': True,
            'socket_timeout': 15,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],  # Evitar formatos que requieren descarga
                }
            },
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        # Agregar cookies si están disponibles
        cookies_path = get_youtube_cookies_path()
        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                search_query = f"ytsearch1:{query}"
                search_results = ydl.extract_info(search_query, download=False)
                
                if search_results and 'entries' in search_results:
                    entries = search_results['entries']
                    if entries and len(entries) > 0:
                        video = entries[0]
                        # Si el video tiene URL directa, la usamos
                        if 'url' in video and video['url']:
                            return video['url']
                        # Si tiene webpage_url, extraemos la URL de audio
                        elif 'webpage_url' in video and video['webpage_url']:
                            video_url = video['webpage_url']
                            # Extraer URL de audio directamente
                            ydl2_opts = {
                                'format': 'bestaudio/best',
                                'quiet': True,
                                'no_warnings': True,
                                'socket_timeout': 15,
                                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            }
                            # Agregar cookies si están disponibles
                            cookies_path = get_youtube_cookies_path()
                            if cookies_path:
                                ydl2_opts['cookiefile'] = cookies_path
                            with yt_dlp.YoutubeDL(ydl2_opts) as ydl2:
                                info = ydl2.extract_info(video_url, download=False)
                                if info and 'url' in info and info['url']:
                                    return info['url']
            except Exception as e:
                # Si falla, intentamos con una búsqueda más simple
                try:
                    print(f"Primer intento falló para '{query}', intentando método alternativo...")
                    # Método alternativo: buscar directamente el video ID si lo tenemos
                    return None
                except:
                    print(f"Error extrayendo info de YouTube para '{query}': {str(e)}")
                    return None
                
    except Exception as e:
        print(f"Error buscando en YouTube para '{track_name} - {artist_name}': {str(e)}")
        return None
    return None


def extract_playlist_id(playlist_url: str) -> Optional[str]:
    """Extrae el ID de playlist desde una URL de Spotify"""
    if not playlist_url:
        return None
    
    # Limpiar la URL de espacios y caracteres extra
    playlist_url = playlist_url.strip()
    
    # Los IDs de Spotify pueden contener letras, números y algunos caracteres especiales
    # Pero típicamente son alfanuméricos. Algunos pueden tener guiones bajos o guiones
    patterns = [
        r"spotify\.com/playlist/([a-zA-Z0-9]+)",  # https://open.spotify.com/playlist/ID
        r"playlist/([a-zA-Z0-9]+)",  # playlist/ID
        r"^([a-zA-Z0-9]{22})$",  # Solo ID (22 caracteres es el tamaño típico)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, playlist_url)
        if match:
            playlist_id = match.group(1)
            # Validar que el ID tenga un tamaño razonable (típicamente 22 caracteres)
            if len(playlist_id) >= 15:
                return playlist_id
    
    return None


def get_spotify_client():
    """Obtiene un cliente de Spotify usando credenciales de entorno"""
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "5e3d0a02068b4d5bb56975d3d5577a74")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "d638749b26f94b73999441e79d5e6578")
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="Spotify credentials not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables."
        )
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id, client_secret=client_secret
    )
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def extract_youtube_playlist_id(playlist_url: str) -> Optional[str]:
    """Extrae el ID de playlist desde una URL de YouTube/YouTube Music"""
    if not playlist_url:
        return None
    
    playlist_url = playlist_url.strip()
    
    # Patrones para URLs de YouTube Music y YouTube
    # Nota: Los IDs de playlist de YouTube pueden tener guiones bajos y guiones
    patterns = [
        r"music\.youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)",  # YouTube Music
        r"youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)",  # YouTube regular
        r"youtu\.be/.*[?&]list=([a-zA-Z0-9_-]+)",  # youtu.be con playlist
        r"[?&]list=([a-zA-Z0-9_-]+)",  # Cualquier URL con parámetro list=
        r"^([a-zA-Z0-9_-]{13,})$",  # Solo ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, playlist_url)
        if match:
            playlist_id = match.group(1)
            # Los IDs de playlist de YouTube tienen al menos 13 caracteres
            # pero pueden tener más (típicamente 34 caracteres para playlists)
            if len(playlist_id) >= 13:
                return playlist_id
    
    return None


def import_youtube_playlist(playlist_url: str) -> tuple[List[Track], str, int]:
    """Importa una playlist de YouTube Music y retorna tracks, nombre y cantidad omitida"""
    playlist_id = extract_youtube_playlist_id(playlist_url)
    if not playlist_id:
        raise HTTPException(
            status_code=400,
            detail=f"URL de playlist de YouTube inválida. La URL recibida fue: '{playlist_url}'. Proporciona una URL válida de YouTube Music (ej: https://music.youtube.com/playlist?list=...) o YouTube (ej: https://www.youtube.com/playlist?list=...)"
        )
    
    try:
        # Configuración mejorada para evitar detección de bot
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'incomplete',  # Extraer información básica primero
            'socket_timeout': 60,  # Timeout más largo
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web'],  # Intentar múltiples clientes
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            },
            # Opciones adicionales para reducir detección
            'sleep_interval': 1,  # Esperar 1 segundo entre requests
            'sleep_interval_requests': 1,
            'sleep_interval_subtitles': 1,
        }
        
        # Agregar cookies si están disponibles (opcional)
        cookies_path = get_youtube_cookies_path()
        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path
            print(f"DEBUG: Usando cookies de YouTube desde: {cookies_path}")
        else:
            print("DEBUG: Usando yt-dlp sin cookies (puede ser más propenso a bloqueos)")
        
        full_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                playlist_info = ydl.extract_info(full_url, download=False)
            except Exception as e:
                error_msg = str(e)
                # Limpiar códigos ANSI del mensaje de error
                import re
                error_msg = re.sub(r'\x1b\[[0-9;]*m', '', error_msg)
                
                if "Sign in to confirm" in error_msg or "bot" in error_msg.lower() or "Sign in" in error_msg:
                    raise HTTPException(
                        status_code=400,
                        detail=f"YouTube está bloqueando las solicitudes automáticas (detección de bot). Soluciones: 1) Espera 10-15 minutos y vuelve a intentar, 2) Usa una playlist de Spotify en su lugar (más confiable), 3) La playlist puede ser privada o tener restricciones. Nota: YouTube puede bloquear solicitudes automáticas incluso con configuración optimizada."
                    )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error accediendo a la playlist de YouTube: {error_msg[:300]}"
                )
            
            if not playlist_info:
                raise HTTPException(status_code=400, detail="No se pudo acceder a la playlist de YouTube")
            
            playlist_name = playlist_info.get('title', 'Playlist de YouTube')
            entries = playlist_info.get('entries', [])
            
            tracks = []
            tracks_without_url = 0
            
            import time
            
            print(f"DEBUG: Procesando {len(entries)} videos de la playlist '{playlist_name}'")
            
            for idx, entry in enumerate(entries):
                if not entry:
                    continue
                
                # Agregar delay progresivo para evitar rate limiting de YouTube
                if idx > 0:
                    if idx % 2 == 0:
                        time.sleep(2)  # Esperar 2 segundos cada 2 videos
                    if idx % 5 == 0:
                        time.sleep(5)  # Esperar 5 segundos adicionales cada 5 videos
                        print(f"Delay aplicado después de {idx} videos...")
                
                try:
                    # Obtener información completa del video
                    video_id = entry.get('id')
                    if not video_id:
                        continue
                    
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Extraer URL de audio con configuración mejorada
                    audio_opts = {
                        'format': 'bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                        'socket_timeout': 60,
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                        'referer': 'https://www.youtube.com/',
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['android', 'ios', 'web'],  # Intentar múltiples clientes
                                'player_skip': ['webpage', 'configs'],
                            }
                        },
                        'http_headers': {
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                            'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'DNT': '1',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Sec-Fetch-User': '?1',
                            'Cache-Control': 'max-age=0',
                        },
                        'sleep_interval': 1,
                        'sleep_interval_requests': 1,
                    }
                    
                    # Agregar cookies si están disponibles (opcional)
                    cookies_path = get_youtube_cookies_path()
                    if cookies_path:
                        audio_opts['cookiefile'] = cookies_path
                    
                    with yt_dlp.YoutubeDL(audio_opts) as audio_ydl:
                        try:
                            video_info = audio_ydl.extract_info(video_url, download=False)
                            
                            if video_info and 'url' in video_info and video_info['url']:
                                title = video_info.get('title', entry.get('title', 'Sin título'))
                                # Obtener thumbnail de YouTube
                                thumbnail = video_info.get('thumbnail') or entry.get('thumbnail')
                                track_obj = Track(
                                    id=f"youtube_{video_id}",
                                    title=title,
                                    url=video_info['url'],
                                    image_url=thumbnail
                                )
                                tracks.append(track_obj)
                                print(f"✓ YouTube ({idx+1}/{len(entries)}): {title}")
                            else:
                                tracks_without_url += 1
                                print(f"✗ No se pudo obtener URL de audio para: {entry.get('title', 'Sin título')}")
                        except Exception as extract_error:
                            # Si falla la extracción, intentar usar el video_id directamente
                            # y construir una URL que el frontend pueda usar
                            tracks_without_url += 1
                            error_msg = str(extract_error)
                            if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
                                print(f"⚠ YouTube bloqueó la solicitud para: {entry.get('title', 'Sin título')}")
                            else:
                                print(f"Error extrayendo audio: {error_msg[:100]}")
                            
                except Exception as e:
                    tracks_without_url += 1
                    error_msg = str(e)
                    if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
                        print(f"⚠ YouTube bloqueó la solicitud (video {idx+1})")
                    else:
                        print(f"Error procesando video: {error_msg[:100]}")
                    continue
            
            if not tracks and tracks_without_url > 0:
                # Si no se pudo obtener ninguna canción y hay errores de bot
                raise HTTPException(
                    status_code=400,
                    detail=f"YouTube está bloqueando las solicitudes automáticas. Se intentaron {len(entries)} canciones pero ninguna pudo ser procesada debido a restricciones anti-bot. Intenta más tarde o considera usar una playlist de Spotify."
                )
            
            return tracks, playlist_name, tracks_without_url
    except HTTPException:
        # Re-lanzar errores HTTP directamente (incluyendo el de playlist_id inválido)
        raise
    except HTTPException:
        # Re-lanzar errores HTTP directamente (ya procesados)
        raise
    except Exception as e:
        error_msg = str(e)
        # Limpiar códigos ANSI del mensaje de error
        import re
        error_msg = re.sub(r'\x1b\[[0-9;]*m', '', error_msg)
        
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower() or "Sign in" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=f"YouTube está bloqueando las solicitudes automáticas (detección de bot). Soluciones: 1) Espera 10-15 minutos y vuelve a intentar, 2) Usa una playlist de Spotify en su lugar (más confiable), 3) La playlist puede ser privada o tener restricciones. Nota: YouTube puede bloquear solicitudes automáticas incluso con configuración optimizada."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error importando playlist de YouTube: {error_msg[:400]}"
        )


@app.post("/playlist/import")
async def import_playlist(playlist_data: PlaylistImport):
    """Importa una playlist de Spotify o YouTube Music y actualiza los tracks del juego"""
    try:
        playlist_url = playlist_data.playlist_url.strip()
        room_name_param = playlist_data.room_name
        
        # Obtener la sala correcta
        target_room = None
        if room_name_param:
            target_room = await room_manager.get_room(room_name_param)
            if not target_room:
                raise HTTPException(status_code=404, detail="Sala no encontrada")
        else:
            target_room = room  # Usar sala por defecto para compatibilidad
        
        # Obtener source del modelo, con valor por defecto
        source = getattr(playlist_data, 'source', None)
        if source:
            source = source.lower()
        
        # Detectar automáticamente la fuente basándose en la URL (tiene prioridad)
        # Esto asegura que incluso si el frontend envía un source incorrecto, se detecte correctamente
        if "youtube.com" in playlist_url or "music.youtube.com" in playlist_url or "youtu.be" in playlist_url:
            source = "youtube"
            print(f"DEBUG: Detectado YouTube desde URL: {playlist_url}")
        elif "spotify.com" in playlist_url or "open.spotify.com" in playlist_url:
            source = "spotify"
            print(f"DEBUG: Detectado Spotify desde URL: {playlist_url}")
        elif not source:
            # Si no se puede detectar y no hay source, asumir Spotify por defecto
            source = "spotify"
            print(f"DEBUG: No se pudo detectar fuente, usando Spotify por defecto: {playlist_url}")
        
        print(f"DEBUG: Source final: {source}, URL: {playlist_url}")
        
        # Importar desde YouTube Music
        if source == "youtube":
            try:
                tracks, playlist_name, tracks_without_url = import_youtube_playlist(playlist_url)
                
                if not tracks:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No se pudieron obtener canciones de la playlist de YouTube. Verifica que la playlist sea pública y tenga videos disponibles."
                    )
                
                await target_room.update_tracks(tracks)
                if room_name_param:
                    await manager.broadcast(build_state_message(target_room), room_name_param)
                else:
                    await manager.broadcast(build_state_message(target_room))
                
                message = f"Playlist de YouTube importada exitosamente. {len(tracks)} canciones cargadas."
                if tracks_without_url > 0:
                    message += f" {tracks_without_url} canciones no pudieron ser procesadas."
                
                return {
                    "message": message,
                    "playlist_name": playlist_name,
                    "tracks_count": len(tracks),
                    "tracks_skipped": tracks_without_url,
                    "tracks": [t.model_dump() for t in tracks],
                }
            except HTTPException:
                # Re-lanzar errores HTTP directamente
                raise
            except HTTPException:
                # Re-lanzar errores HTTP directamente
                raise
            except Exception as e:
                # Cualquier otro error al importar de YouTube
                error_msg = str(e)
                # Limpiar códigos ANSI del mensaje de error
                import re
                error_msg = re.sub(r'\x1b\[[0-9;]*m', '', error_msg)
                
                if "Sign in to confirm" in error_msg or "bot" in error_msg.lower() or "Sign in" in error_msg:
                    raise HTTPException(
                        status_code=400,
                        detail=f"YouTube está bloqueando las solicitudes automáticas (detección de bot). Soluciones: 1) Espera 10-15 minutos y vuelve a intentar, 2) Usa una playlist de Spotify en su lugar (más confiable), 3) La playlist puede ser privada o tener restricciones. Nota: YouTube puede bloquear solicitudes automáticas incluso con configuración optimizada."
                    )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error importando playlist de YouTube: {error_msg[:400]}"
                )
        
        # Importar desde Spotify (solo si no es YouTube)
        if source != "youtube":
            playlist_id = extract_playlist_id(playlist_url)
            
            if not playlist_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"URL de playlist inválida. La URL recibida fue: '{playlist_url}'. Por favor proporciona una URL válida de Spotify (ej: https://open.spotify.com/playlist/...) o solo el ID de la playlist."
                )
        
        sp = get_spotify_client()
        playlist = sp.playlist(playlist_id)
        
        tracks = []
        results = playlist["tracks"]
        tracks_without_url = 0
        tracks_found = 0
        
        while results:
            for item in results["items"]:
                track = item["track"]
                if track:
                    track_name = track['name']
                    artist_names = ', '.join([a['name'] for a in track['artists']])
                    full_title = f"{track_name} - {artist_names}"
                    
                    # Primero intentamos usar preview_url de Spotify si está disponible
                    audio_url = track.get("preview_url")
                    source = "spotify_preview"
                    
                    # Si no hay preview_url, buscamos en YouTube
                    if not audio_url:
                        print(f"Buscando en YouTube: {full_title}")
                        audio_url = search_youtube_audio_url(track_name, artist_names)
                        if audio_url:
                            source = "youtube"
                    
                    if audio_url:
                        # Obtener imagen del álbum (preferir medium, luego large, luego small)
                        image_url = None
                        album = track.get('album', {})
                        images = album.get('images', [])
                        if images:
                            # Buscar imagen medium (300x300) o la más grande disponible
                            for img in images:
                                if img.get('width', 0) >= 300:
                                    image_url = img.get('url')
                                    break
                            # Si no hay medium, usar la primera (generalmente la más grande)
                            if not image_url and images:
                                image_url = images[0].get('url')
                        
                        track_obj = Track(
                            id=f"spotify_{track['id']}",
                            title=full_title,
                            url=audio_url,
                            artist=artist_names,
                            image_url=image_url
                        )
                        tracks.append(track_obj)
                        tracks_found += 1
                        print(f"✓ Encontrada ({source}): {full_title}")
                    else:
                        tracks_without_url += 1
                        print(f"✗ No se pudo encontrar URL de audio para: {full_title}")
            
            if results["next"]:
                results = sp.next(results)
            else:
                break
        
        if not tracks:
            total_attempted = tracks_without_url + tracks_found
            detail_msg = f"No se pudieron encontrar URLs de audio para las canciones de esta playlist. "
            detail_msg += f"Se intentaron {total_attempted} canciones pero ninguna pudo ser procesada. "
            detail_msg += f"Esto puede deberse a: (1) Restricciones de región en Spotify, (2) YouTube bloqueando solicitudes automáticas, "
            detail_msg += f"o (3) Problemas de conexión. Intenta con otra playlist o verifica tu conexión a internet."
            raise HTTPException(status_code=400, detail=detail_msg)
        
        await target_room.update_tracks(tracks)
        if room_name_param:
            await manager.broadcast(build_state_message(target_room), room_name_param)
        else:
            await manager.broadcast(build_state_message(target_room))
        
        message = f"Playlist importada exitosamente. {tracks_found} canciones cargadas."
        if tracks_without_url > 0:
            message += f" {tracks_without_url} canciones no pudieron ser procesadas (sin preview URL disponible y YouTube bloqueado)."
        
        return {
            "message": message,
            "playlist_name": playlist["name"],
            "tracks_count": len(tracks),
            "tracks_skipped": tracks_without_url,
            "tracks": [t.model_dump() for t in tracks],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error importing playlist: {str(e)}"
        )


@app.get("/auth/youtube/authorize")
async def youtube_authorize():
    """Inicia el flujo OAuth2 de Google/YouTube"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth2 no está configurado. Configura GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET."
        )
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Guardar el state para verificación (en producción usar sesiones)
    return {"authorization_url": authorization_url, "state": state}


@app.get("/auth/youtube/callback")
async def youtube_callback(code: str, state: Optional[str] = None):
    """Callback de OAuth2 de Google/YouTube"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth2 no está configurado.")
    
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Guardar las credenciales (usar un ID único, por ejemplo de sesión)
        session_id = "default"  # En producción, usar un ID de sesión real
        youtube_oauth_tokens[session_id] = credentials
        save_youtube_tokens()  # Guardar en archivo
        
        # Redirigir al frontend con éxito
        return RedirectResponse(url=f"{FRONTEND_URL}/?youtube_auth=success")
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/?youtube_auth=error&message={str(e)}")


@app.get("/auth/youtube/status")
async def youtube_auth_status():
    """Verifica si hay un token OAuth2 activo"""
    session_id = "default"
    has_token = session_id in youtube_oauth_tokens
    
    if has_token:
        credentials = youtube_oauth_tokens[session_id]
        # Verificar si el token es válido
        try:
            if credentials.valid:
                return {"authenticated": True, "message": "Autenticado con YouTube"}
            else:
                # Intentar refrescar el token
                if credentials.refresh_token:
                    try:
                        credentials.refresh(Request())
                        save_youtube_tokens()
                        return {"authenticated": True, "message": "Autenticado con YouTube (token refrescado)"}
                    except:
                        del youtube_oauth_tokens[session_id]
                        save_youtube_tokens()
                        return {"authenticated": False, "message": "Token expirado y no se pudo refrescar"}
                else:
                    del youtube_oauth_tokens[session_id]
                    save_youtube_tokens()
                    return {"authenticated": False, "message": "Token expirado"}
        except:
            return {"authenticated": False, "message": "Error verificando token"}
    
    return {"authenticated": False, "message": "No autenticado"}


def get_youtube_service():
    """Obtiene un servicio de YouTube autenticado"""
    session_id = "default"
    if session_id in youtube_oauth_tokens:
        credentials = youtube_oauth_tokens[session_id]
        if credentials.valid:
            return build('youtube', 'v3', credentials=credentials)
        else:
            try:
                credentials.refresh(Request())
                save_youtube_tokens()  # Guardar tokens refrescados
                return build('youtube', 'v3', credentials=credentials)
            except:
                del youtube_oauth_tokens[session_id]
                save_youtube_tokens()  # Guardar después de eliminar
    return None


def import_youtube_playlist_authenticated(playlist_id: str) -> tuple[List[Track], str]:
    """Importa una playlist de YouTube usando la API autenticada (sin delays, sin detección de bots)"""
    youtube = get_youtube_service()
    if not youtube:
        raise HTTPException(status_code=401, detail="No autenticado con YouTube. Inicia sesión primero.")
    
    try:
        playlist_response = youtube.playlists().list(
            part="snippet",
            id=playlist_id
        ).execute()
        
        if not playlist_response.get('items'):
            raise HTTPException(status_code=404, detail="Playlist no encontrada o es privada")
        
        playlist_name = playlist_response['items'][0]['snippet']['title']
        
        tracks = []
        next_page_token = None
        
        while True:
            playlist_items = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            for item in playlist_items.get('items', []):
                snippet = item.get('snippet', {})
                video_id = snippet.get('resourceId', {}).get('videoId')
                
                if not video_id:
                    continue
                
                title = snippet.get('title', 'Sin título')
                channel = snippet.get('videoOwnerChannelTitle', '')
                
                if title in ['Deleted video', 'Private video']:
                    continue
                
                if ' - ' in title:
                    parts = title.split(' - ', 1)
                    artist = parts[0].strip()
                    song_title = parts[1].strip()
                else:
                    song_title = title
                    artist = channel.replace(' - Topic', '') if channel else 'Artista desconocido'
                
                # Obtener thumbnail (preferir high quality, luego medium, luego default)
                thumbnails = snippet.get('thumbnails', {})
                image_url = None
                if thumbnails.get('high'):
                    image_url = thumbnails['high'].get('url')
                elif thumbnails.get('medium'):
                    image_url = thumbnails['medium'].get('url')
                elif thumbnails.get('default'):
                    image_url = thumbnails['default'].get('url')
                
                track = Track(
                    id=f"yt_{video_id}",
                    title=f"{song_title} - {artist}",
                    url="",  # Se cargará bajo demanda
                    artist=artist,
                    video_id=video_id,
                    image_url=image_url
                )
                tracks.append(track)
            
            next_page_token = playlist_items.get('nextPageToken')
            if not next_page_token:
                break
        
        return tracks, playlist_name
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importando playlist: {str(e)}")


def get_youtube_audio_url_internal(video_id: str) -> Optional[str]:
    """Obtiene la URL de audio de un video de YouTube (función interna)"""
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        cookies_path = get_youtube_cookies_path()
        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if info and info.get('url'):
                return info['url']
            
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            if audio_formats:
                best_audio = max(audio_formats, key=lambda x: x.get('abr', 0) or 0)
                return best_audio.get('url')
            
            if formats:
                return formats[-1].get('url')
        
        return None
    except Exception as e:
        print(f"Error obteniendo URL de audio: {e}")
        return None


@app.get("/youtube/audio/{video_id}")
async def get_youtube_audio_url(video_id: str):
    """Obtiene la URL de audio de un video de YouTube bajo demanda (deprecated, usar /youtube/stream)"""
    url = get_youtube_audio_url_internal(video_id)
    if url:
        return {"url": url, "video_id": video_id}
    raise HTTPException(status_code=404, detail="No se pudo obtener el audio")


@app.get("/youtube/stream/{video_id}")
async def stream_youtube_audio(video_id: str, request: FastAPIRequest):
    """Stream del audio de YouTube a través del backend (evita problemas de CORS y 403)"""
    audio_url = get_youtube_audio_url_internal(video_id)
    
    if not audio_url:
        raise HTTPException(status_code=404, detail="No se pudo obtener el audio")
    
    try:
        # Obtener el header Range del cliente si existe
        range_header = request.headers.get('Range', '')
        
        headers = {
            'Referer': 'https://www.youtube.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        if range_header:
            headers['Range'] = range_header
        
        response = requests.get(audio_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        response_headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": response.headers.get("Content-Type", "audio/webm"),
        }
        
        # Si hay Range, copiar los headers de respuesta relevantes
        if range_header:
            if 'Content-Range' in response.headers:
                response_headers['Content-Range'] = response.headers['Content-Range']
            if 'Content-Length' in response.headers:
                response_headers['Content-Length'] = response.headers['Content-Length']
        else:
            if 'Content-Length' in response.headers:
                response_headers['Content-Length'] = response.headers['Content-Length']
        
        status_code = 206 if range_header else 200
        
        return StreamingResponse(
            generate(),
            status_code=status_code,
            media_type="audio/webm",
            headers=response_headers
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error streaming audio: {str(e)}")


@app.post("/playlist/import-authenticated")
async def import_playlist_authenticated(data: PlaylistImport):
    """Importa una playlist de YouTube usando la API autenticada (rápido, sin detección de bots)"""
    global TRACKS
    
    playlist_id = extract_youtube_playlist_id(data.playlist_url)
    if not playlist_id:
        raise HTTPException(
            status_code=400,
            detail="URL de playlist de YouTube inválida"
        )
    
    room_name_param = data.room_name
    
    # Obtener la sala correcta
    target_room = None
    if room_name_param:
        target_room = await room_manager.get_room(room_name_param)
        if not target_room:
            raise HTTPException(status_code=404, detail="Sala no encontrada")
    else:
        target_room = room  # Usar sala por defecto para compatibilidad
        TRACKS = []  # Solo actualizar TRACKS global si no hay sala específica
    
    tracks, playlist_name = import_youtube_playlist_authenticated(playlist_id)
    
    if not tracks:
        raise HTTPException(status_code=400, detail="La playlist está vacía o no tiene videos disponibles")
    
    if not room_name_param:
        TRACKS = tracks
    
    await target_room.update_tracks(tracks)
    if room_name_param:
        await manager.broadcast(build_state_message(target_room), room_name_param)
    else:
        await manager.broadcast(build_state_message(target_room))
    
    return {
        "success": True,
        "message": f"Playlist '{playlist_name}' importada. {len(tracks)} canciones cargadas.",
        "tracks": [t.model_dump() for t in tracks],
        "playlist_name": playlist_name,
        "total_tracks": len(tracks),
        "requires_audio_fetch": True  # Indica que las URLs se cargan bajo demanda
    }


@app.post("/rooms/create")
async def create_room(data: CreateRoomRequest):
    """Crea una nueva sala con nombre y contraseña"""
    if not data.room_name or not data.room_name.strip():
        raise HTTPException(status_code=400, detail="El nombre de la sala no puede estar vacío")
    
    if not data.password or len(data.password) < 4:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 4 caracteres")
    
    if len(data.room_name) > 50:
        raise HTTPException(status_code=400, detail="El nombre de la sala es demasiado largo (máximo 50 caracteres)")
    
    success = await room_manager.create_room(data.room_name, data.password)
    if not success:
        raise HTTPException(status_code=400, detail="La sala ya existe")
    
    return {"success": True, "message": f"Sala '{data.room_name}' creada exitosamente", "room_name": data.room_name}


@app.post("/rooms/join")
async def join_room(data: JoinRoomRequest):
    """Valida la contraseña y permite unirse a una sala"""
    if not data.room_name or not data.room_name.strip():
        raise HTTPException(status_code=400, detail="El nombre de la sala no puede estar vacío")
    
    if not data.password:
        raise HTTPException(status_code=400, detail="La contraseña es requerida")
    
    room_instance = await room_manager.join_room(data.room_name, data.password)
    if not room_instance:
        raise HTTPException(status_code=401, detail="Nombre de sala o contraseña incorrectos")
    
    return {"success": True, "message": f"Unido a la sala '{data.room_name}' exitosamente", "room_name": data.room_name}


@app.get("/rooms/check/{room_name}")
async def check_room(room_name: str):
    """Verifica si una sala existe (sin validar contraseña)"""
    exists = await room_manager.room_exists(room_name)
    return {"exists": exists, "room_name": room_name}


def verify_admin_password(password: str) -> bool:
    """Verifica la contraseña de administrador"""
    # Si hay hash configurado, usar verificación segura con bcrypt
    if ADMIN_PASSWORD_HASH:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), ADMIN_PASSWORD_HASH.encode('utf-8'))
        except:
            return False
    # Si no hay hash configurado, comparar directamente (solo desarrollo)
    # En producción siempre debe usarse ADMIN_PASSWORD_HASH
    return password == ADMIN_PASSWORD_PLAIN


@app.post("/admin/auth")
async def admin_auth(data: AdminAuthRequest):
    """Autentica al administrador con contraseña"""
    if verify_admin_password(data.password):
        return {"authenticated": True, "message": "Autenticación exitosa"}
    raise HTTPException(status_code=401, detail="Contraseña incorrecta")


class AdminPasswordRequest(BaseModel):
    admin_password: str


@app.post("/admin/rooms")
async def admin_list_rooms(data: AdminPasswordRequest):
    """Lista todas las salas activas (requiere contraseña de admin)"""
    if not verify_admin_password(data.admin_password):
        raise HTTPException(status_code=401, detail="Contraseña de administrador incorrecta")
    
    rooms = await room_manager.list_rooms()
    return {"rooms": rooms, "total": len(rooms)}


@app.post("/admin/rooms/{room_name}")
async def admin_get_room_info(room_name: str, data: AdminPasswordRequest):
    """Obtiene información detallada de una sala (requiere contraseña de admin)"""
    if not verify_admin_password(data.admin_password):
        raise HTTPException(status_code=401, detail="Contraseña de administrador incorrecta")
    
    room_info = await room_manager.get_room_info(room_name)
    if not room_info:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    return room_info


@app.post("/admin/rooms/close")
async def admin_close_room(data: CloseRoomRequest):
    """Cierra y elimina una sala (requiere contraseña de admin)"""
    if not verify_admin_password(data.admin_password):
        raise HTTPException(status_code=401, detail="Contraseña de administrador incorrecta")
    
    # Normalizar el nombre de la sala
    room_name_clean = data.room_name.strip().lower()
    
    # Verificar que la sala existe en room_manager
    async with room_manager._lock:
        if room_name_clean not in room_manager.rooms:
            # Listar todas las salas disponibles para debug
            available_rooms = list(room_manager.rooms.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Sala no encontrada. Sala buscada: '{room_name_clean}'. Salas disponibles: {available_rooms}"
            )
    
    # Obtener la instancia de la sala
    room_instance = await room_manager.get_room(room_name_clean)
    if not room_instance:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    # Desconectar todos los WebSockets de esa sala
    if room_name_clean in manager.rooms:
        websockets_to_close = manager.rooms[room_name_clean].copy()
        for ws in websockets_to_close:
            try:
                await ws.close()
            except:
                pass
        del manager.rooms[room_name_clean]
    
    # Eliminar la sala (usar el nombre normalizado)
    success = await room_manager.close_room(room_name_clean)
    if success:
        return {"success": True, "message": f"Sala '{data.room_name}' cerrada exitosamente"}
    raise HTTPException(status_code=404, detail="Sala no encontrada")


@app.post("/admin/players/ban")
async def admin_ban_player(data: BanPlayerRequest):
    """Banea/expulsa a un jugador de una sala (requiere contraseña de admin)"""
    if not verify_admin_password(data.admin_password):
        raise HTTPException(status_code=401, detail="Contraseña de administrador incorrecta")
    
    room_instance = await room_manager.get_room(data.room_name)
    if not room_instance:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    
    # Remover el jugador de la sala
    player = room_instance.players.get(data.player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado en la sala")
    
    await room_instance.remove_player(data.player_id)
    
    # Desconectar el WebSocket del jugador
    room_name_clean = data.room_name.strip().lower()
    if room_name_clean in manager.rooms:
        for ws in manager.rooms[room_name_clean]:
            if manager.active.get(ws, {}).get("player_id") == data.player_id:
                try:
                    await ws.close()
                except:
                    pass
                break
    
    # Notificar a los demás en la sala
    await manager.broadcast(
        {"type": "player_banned", "payload": {"playerId": data.player_id, "playerName": player.name}},
        room_name_clean
    )
    await manager.broadcast(build_state_message(room_instance), room_name_clean)
    
    return {"success": True, "message": f"Jugador '{player.name}' expulsado de la sala"}


@app.get("/")
async def root():
    return {"message": "Music buzzer backend activo", "tracks": [t.model_dump() for t in TRACKS]}


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Railway inyecta PORT automáticamente, usar 8000 como fallback
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
