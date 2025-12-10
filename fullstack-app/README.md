# 🎮 Music Buzzer Game - Juego de Adivinanza Musical

Un juego multijugador en tiempo real donde los participantes deben adivinar canciones. El organizador reproduce música y los jugadores compiten para ser el primero en adivinar la canción.

## 🚀 Características

- **Multijugador en tiempo real**: Múltiples jugadores pueden conectarse simultáneamente
- **Sistema de puntuación**: Puntos por adivinar correctamente
- **Persistencia de scores**: Los scores se guardan y persisten por 24 horas
- **Importación de playlists**: Soporte para Spotify y YouTube Music
- **Controles de reproducción**: Play, pause, stop, preview de 2s y 5s
- **Sistema de buzz**: Los jugadores pueden "buzzear" para responder
- **Scoreboard en tiempo real**: Tabla de posiciones actualizada automáticamente

## 📋 Requisitos Previos

### Backend
- Python 3.8+
- pip

### Frontend
- Node.js 18+
- npm

## 🛠️ Instalación

### Backend

1. Navega al directorio del backend:
```bash
cd backend
```

2. Crea un entorno virtual:
```bash
python -m venv venv
```

3. Activa el entorno virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instala las dependencias:
```bash
pip install -r requirements.txt
```

5. Configura las variables de entorno (opcional, para Spotify/YouTube):
```bash
# Spotify
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret

# YouTube OAuth2 (opcional)
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/youtube/callback
```

6. Inicia el servidor:
```bash
python main.py
```

El backend estará disponible en `http://localhost:8000`

### Frontend

1. Navega al directorio del frontend:
```bash
cd frontend
```

2. Instala las dependencias:
```bash
npm install
```

3. Inicia el servidor de desarrollo:
```bash
npm start
```

El frontend estará disponible en `http://localhost:3000` (o el puerto que indique)

## 📖 Uso

### Como Organizador

1. Abre la aplicación en tu navegador
2. Ingresa tu nombre como "Organizador"
3. Importa una playlist de Spotify o YouTube Music
4. Selecciona una canción de la lista
5. Usa los controles para reproducir música
6. Cuando un jugador adivine, selecciona el ganador o ajusta puntos manualmente

### Como Jugador

1. Abre la aplicación en tu navegador
2. Ingresa tu nombre
3. Espera a que el organizador inicie una canción
4. Presiona el botón "BUZZ" cuando sepas la respuesta
5. Tu posición en la cola se mostrará automáticamente

## 🌐 Despliegue

### GitHub Pages (Frontend)

El frontend está configurado para desplegarse automáticamente en GitHub Pages usando GitHub Actions.

1. **Configura GitHub Pages**:
   - Ve a Settings > Pages en tu repositorio
   - Selecciona "GitHub Actions" como fuente

2. **Configura la URL del backend** (si el backend está en otro servidor):
   - Ve a Settings > Secrets and variables > Actions
   - Agrega un secreto llamado `REACT_APP_WS_URL` con la URL de tu WebSocket
   - Ejemplo: `wss://tu-backend.com/ws/sala`

3. **Push a main/master**:
   - El workflow se ejecutará automáticamente
   - El sitio se desplegará en `https://tu-usuario.github.io/tu-repo`

### Backend

El backend necesita estar en un servidor que soporte WebSockets. Opciones recomendadas:

- **Railway**: https://railway.app
- **Render**: https://render.com
- **Heroku**: https://heroku.com
- **Fly.io**: https://fly.io

Asegúrate de:
1. Configurar las variables de entorno en el servicio
2. Actualizar `REACT_APP_WS_URL` en GitHub Secrets con la URL de tu backend desplegado

## 📁 Estructura del Proyecto

```
fullstack-app/
├── backend/
│   ├── main.py              # Servidor FastAPI
│   ├── requirements.txt     # Dependencias Python
│   ├── scores.json         # Scores persistidos (generado)
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── hooks/          # Custom hooks
│   │   └── ...
│   ├── public/
│   └── package.json
└── README.md
```

## 🔧 Configuración Avanzada

### Spotify API

1. Crea una aplicación en https://developer.spotify.com/dashboard
2. Obtén tu Client ID y Client Secret
3. Configura las variables de entorno en el backend

### YouTube Music OAuth2

Ver `backend/SETUP_OAUTH2.md` para instrucciones detalladas.

### Cookies de YouTube (Alternativa a OAuth2)

Ver `backend/README_COOKIES.md` para usar cookies de sesión.

## 📝 Notas

- Los scores se guardan automáticamente en `backend/scores.json`
- Los scores expiran después de 24 horas
- Los jugadores pueden reconectarse y mantener sus scores si usan el mismo nombre
- El backend debe estar corriendo para que el frontend funcione

## 🐛 Solución de Problemas

### El frontend no se conecta al backend
- Verifica que el backend esté corriendo en el puerto 8000
- Verifica la URL del WebSocket en `useGameSocket.ts`
- Revisa la consola del navegador para errores

### Error al importar playlist de YouTube
- YouTube puede bloquear solicitudes automáticas (detección de bot)
- Usa OAuth2 o cookies de sesión (ver documentación)
- Considera usar Spotify como alternativa

### Los scores no persisten
- Verifica que el archivo `scores.json` tenga permisos de escritura
- Revisa los logs del backend para errores

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request
