# 🚀 Guía de Despliegue

Esta guía te ayudará a desplegar la aplicación en producción.

## 📋 Requisitos

- Cuenta de GitHub
- Servicio para el backend (Railway, Render, Heroku, etc.)
- Dominio opcional (puedes usar el subdominio del servicio)

## 🔧 Paso 1: Preparar el Backend

### Opción A: Railway (Recomendado)

1. Ve a https://railway.app y crea una cuenta
2. Crea un nuevo proyecto
3. Conecta tu repositorio de GitHub
4. Selecciona el directorio `backend`
5. Railway detectará automáticamente Python
6. Configura las variables de entorno:
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `GOOGLE_CLIENT_ID` (opcional)
   - `GOOGLE_CLIENT_SECRET` (opcional)
   - `GOOGLE_REDIRECT_URI` (debe ser la URL de tu backend + `/auth/youtube/callback`)
7. Railway generará una URL automáticamente (ej: `https://tu-app.railway.app`)

### Opción B: Render

1. Ve a https://render.com y crea una cuenta
2. Crea un nuevo "Web Service"
3. Conecta tu repositorio
4. Configura:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Root Directory**: `backend`
5. Configura las variables de entorno
6. Render generará una URL (ej: `https://tu-app.onrender.com`)

### Opción C: Fly.io

1. Instala Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. En el directorio `backend`, ejecuta: `fly launch`
3. Sigue las instrucciones
4. Configura las variables de entorno: `fly secrets set SPOTIFY_CLIENT_ID=...`

## 🔧 Paso 2: Configurar GitHub Pages

1. Ve a tu repositorio en GitHub
2. Settings > Pages
3. En "Source", selecciona "GitHub Actions"
4. Ve a Settings > Secrets and variables > Actions
5. Agrega un nuevo secreto:
   - **Name**: `REACT_APP_WS_URL`
   - **Value**: La URL de tu backend con protocolo `wss://` (WebSocket seguro)
     - Ejemplo: `wss://tu-app.railway.app/ws/sala`
     - Si tu backend usa HTTP (no HTTPS), usa `ws://` en su lugar

## 🔧 Paso 3: Verificar el Despliegue

1. Haz push a la rama `main` o `master`
2. Ve a Actions en GitHub para ver el progreso del build
3. Una vez completado, tu sitio estará disponible en:
   - `https://tu-usuario.github.io/tu-repositorio`

## 🔧 Paso 4: Configurar CORS (si es necesario)

Si el backend está en un dominio diferente, asegúrate de que el backend permita CORS desde tu dominio de GitHub Pages.

En `backend/main.py`, verifica que el CORS esté configurado:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Para producción, cambia `allow_origins` a:
```python
allow_origins=[
    "https://tu-usuario.github.io",
    "http://localhost:3000"  # Para desarrollo local
]
```

## 🔧 Paso 5: Actualizar URLs en el Frontend

El frontend ya está configurado para usar variables de entorno. Si necesitas cambiar la URL manualmente:

1. Edita `frontend/src/hooks/useGameSocket.ts`
2. Cambia la línea:
```typescript
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/sala';
```

## ✅ Verificación Final

1. ✅ Backend desplegado y accesible
2. ✅ Variables de entorno configuradas
3. ✅ GitHub Secrets configurado con `REACT_APP_WS_URL`
4. ✅ GitHub Pages activado
5. ✅ CORS configurado correctamente
6. ✅ Frontend desplegado y funcionando

## 🐛 Problemas Comunes

### El frontend no se conecta al backend

- Verifica que la URL del WebSocket sea correcta (debe incluir `/ws/sala`)
- Verifica que el backend esté corriendo
- Revisa la consola del navegador para errores de CORS

### Error 404 en GitHub Pages

- Asegúrate de que el build se haya completado correctamente
- Verifica que el workflow de GitHub Actions haya terminado sin errores

### WebSocket connection failed

- Verifica que el backend soporte WebSockets
- Si usas HTTP (no HTTPS), asegúrate de usar `ws://` en lugar de `wss://`
- Verifica que no haya un firewall bloqueando la conexión

## 📝 Notas Adicionales

- El backend debe estar siempre corriendo para que el frontend funcione
- Los scores se guardan en el servidor del backend, no en GitHub Pages
- Considera usar un servicio de base de datos para producción en lugar de archivos JSON
