# Inicio Rápido para Desarrollo Local

## Configuración Inicial

### 1. Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar archivo de ejemplo de variables de entorno
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Editar .env y agregar tus credenciales (opcional)
# Si no tienes credenciales, el backend funcionará pero sin Spotify/YouTube OAuth

# Iniciar servidor
python main.py
# O usar el script:
start_dev.bat  # Windows
```

El backend estará disponible en: `http://localhost:8000`

### 2. Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Copiar archivo de ejemplo de variables de entorno
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# El .env.example ya tiene las URLs correctas para desarrollo local
# No necesitas modificarlo a menos que uses un backend remoto

# Iniciar servidor de desarrollo
npm start
```

El frontend estará disponible en: `http://localhost:3000`

---

## Variables de Entorno

### Backend (.env)

```env
GOOGLE_CLIENT_ID=          # Opcional
GOOGLE_CLIENT_SECRET=      # Opcional
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/youtube/callback
FRONTEND_URL=http://localhost:3000
PORT=8000
SPOTIFY_CLIENT_ID=         # Opcional
SPOTIFY_CLIENT_SECRET=     # Opcional
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws/sala
PORT=3000
```

---

## Notas

- **Sin credenciales:** El backend funcionará pero no podrás importar playlists de Spotify/YouTube
- **Solo lectura:** Los archivos `.env` están en `.gitignore` y no se suben al repositorio
- **Hot Reload:** Ambos servidores tienen hot reload, los cambios se reflejan automáticamente

---

## Troubleshooting

### Puerto 8000 ya en uso
```bash
# Windows: Encontrar y matar proceso
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# O cambiar el puerto en .env
PORT=8001
```

### Puerto 3000 ya en uso
```bash
# El frontend te preguntará si quieres usar otro puerto
# O cambiar en .env
PORT=3001
```

### Módulos no encontrados
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

