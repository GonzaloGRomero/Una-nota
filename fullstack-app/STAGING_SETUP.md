# Configuración de Entorno de Desarrollo Local

Esta guía te ayudará a configurar un entorno de desarrollo local para poder probar cambios antes de subir a producción en la nube.

## Desarrollo Local (Recomendado)

### Inicio Rápido

**Opción 1: Script Automático (Recomendado)**

Desde PowerShell, en la raíz del proyecto (`fullstack-app/`):
```powershell
.\start_local.ps1
```

O desde CMD:
```cmd
start_local.bat
```

Este script automáticamente:
- Crea los archivos `.env` si no existen
- Crea el entorno virtual si no existe
- Instala dependencias si faltan
- Inicia backend y frontend en ventanas separadas

---

## Configuración Manual

### 1. Backend Local

1. **Navegar al directorio del backend:**
   ```bash
   cd fullstack-app/backend
   ```

2. **Crear entorno virtual (si no existe):**
   ```bash
   python -m venv venv
   ```

3. **Activar entorno virtual:**
   ```bash
   # Windows:
   venv\Scripts\activate
   
   # Linux/Mac:
   source venv/bin/activate
   ```

4. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configurar variables de entorno:**
   - Copia el archivo de ejemplo:
     ```bash
     # Windows:
     copy .env.example .env
     
     # Linux/Mac:
     cp .env.example .env
     ```
   - Edita el archivo `.env` y agrega tus credenciales (opcional):
     ```env
     GOOGLE_CLIENT_ID=tu_client_id
     GOOGLE_CLIENT_SECRET=tu_client_secret
     GOOGLE_REDIRECT_URI=http://localhost:8000/auth/youtube/callback
     FRONTEND_URL=http://localhost:3000
     PORT=8000
     SPOTIFY_CLIENT_ID=tu_client_id
     SPOTIFY_CLIENT_SECRET=tu_client_secret
     ```
   - **Nota:** Si no tienes credenciales, el backend funcionará pero sin importar playlists de Spotify/YouTube

6. **Iniciar el servidor:**
   ```bash
   python main.py
   # O en Windows desde el directorio backend:
   .\start_backend.bat
   # O desde PowerShell:
   .\start_backend.bat
   ```
   
   El backend estará disponible en: **http://localhost:8000**

### 2. Frontend Local

1. **Abrir una nueva terminal y navegar al directorio del frontend:**
   ```bash
   cd fullstack-app/frontend
   ```

2. **Instalar dependencias (solo la primera vez):**
   ```bash
   npm install
   ```

3. **Configurar variables de entorno:**
   - Copia el archivo de ejemplo:
     ```bash
     # Windows:
     copy .env.example .env
     
     # Linux/Mac:
     cp .env.example .env
     ```
   - El archivo `.env.example` ya tiene las URLs correctas para desarrollo local:
     ```env
     REACT_APP_API_URL=http://localhost:8000
     REACT_APP_WS_URL=ws://localhost:8000/ws/sala
     PORT=3000
     ```
   - **No necesitas modificar nada** a menos que quieras usar un backend remoto

4. **Iniciar el servidor de desarrollo:**
   ```bash
   npm start
   ```
   
   El frontend estará disponible en: **http://localhost:3000**

---

## Verificar que Todo Funciona

1. **Backend:** Abre http://localhost:8000 en tu navegador
   - Deberías ver: `{"message":"Music buzzer backend activo",...}`

2. **Frontend:** Abre http://localhost:3000
   - Deberías ver la pantalla de inicio con opciones para crear/unirse a salas

3. **Probar conexión:**
   - Crea una sala desde el frontend
   - Verifica que puedas conectarte como organizador y jugador

---

## Flujo de Trabajo Recomendado

1. **Desarrollo Local:**
   - Trabaja en la branch `develop` (o crea branches feature desde `develop`)
   - Inicia backend y frontend localmente
   - Prueba todos los cambios localmente
   - Haz commits en `develop`

2. **Testing Local:**
   - Prueba todas las funcionalidades
   - Verifica que todo funcione correctamente
   - Crea salas, importa playlists, prueba con jugadores

3. **Subir a Producción:**
   - Cuando estés satisfecho con los cambios locales
   - Haz merge de `develop` a `master`
   - Push a `master`
   - Railway y Vercel producción se actualizarán automáticamente

---

## Comandos Útiles

```bash
# Crear nueva branch de feature desde develop
git checkout develop
git pull origin develop
git checkout -b feature/nueva-funcionalidad

# Hacer merge a develop después de probar
git checkout develop
git merge feature/nueva-funcionalidad
git push origin develop

# Cuando esté listo para producción
git checkout master
git merge develop
git push origin master
```

---

## Notas Importantes

- **Desarrollo Local es completamente independiente de Producción:** Tu entorno local no afecta la producción en la nube
- **Hot Reload:** Ambos servidores (backend y frontend) tienen hot reload, los cambios se reflejan automáticamente
- **Sin necesidad de redeploy:** Puedes probar cambios instantáneamente sin esperar deploys
- **Los archivos `.env` no se suben al repositorio:** Están en `.gitignore` para mantener tus credenciales seguras
- **Tokens de YouTube OAuth:** Para desarrollo local, usa `http://localhost:8000/auth/youtube/callback` (ya está en el .env.example)

---

## Troubleshooting

### El frontend no se conecta al backend
- **Verifica que el backend esté corriendo:** Debe estar en http://localhost:8000
- **Verifica las variables de entorno:** Asegúrate de que `.env` en frontend tenga:
  ```
  REACT_APP_API_URL=http://localhost:8000
  REACT_APP_WS_URL=ws://localhost:8000/ws/sala
  ```
- **Reinicia el frontend:** A veces necesita reiniciarse para cargar nuevas variables de entorno

### Error de CORS
- **Verifica que el backend tenga:** `FRONTEND_URL=http://localhost:3000` en su `.env`
- **Verifica que el backend esté corriendo:** El CORS se configura al iniciar

### WebSocket no conecta
- **Verifica que uses `ws://` (no `wss://`) para localhost**
- **Verifica que el backend esté corriendo** en el puerto 8000
- **Revisa la consola del navegador** para ver errores específicos

### Puerto 8000 ya en uso
```bash
# Windows: Encontrar y matar proceso
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# O cambiar el puerto en backend/.env
PORT=8001
# Y actualizar frontend/.env
REACT_APP_API_URL=http://localhost:8001
REACT_APP_WS_URL=ws://localhost:8001/ws/sala
```

### Puerto 3000 ya en uso
- El frontend te preguntará si quieres usar otro puerto
- O cambia en `frontend/.env`: `PORT=3001`

### Módulos no encontrados
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

