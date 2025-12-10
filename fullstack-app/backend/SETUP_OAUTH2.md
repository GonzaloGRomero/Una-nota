# Configuración de OAuth2 para YouTube

Para usar la autenticación OAuth2 con Google/YouTube, necesitas configurar las credenciales.

## Pasos para configurar OAuth2

### 1. Crear un proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la **YouTube Data API v3**:
   - Ve a "APIs & Services" > "Library"
   - Busca "YouTube Data API v3"
   - Haz clic en "Enable"

### 2. Crear credenciales OAuth2

1. Ve a "APIs & Services" > "Credentials"
2. Haz clic en "Create Credentials" > "OAuth client ID"
3. Si es la primera vez, configura la pantalla de consentimiento:
   - Tipo: "External"
   - Nombre de la app: "Music Buzzer"
   - Email de soporte: tu email
   - Dominios autorizados: deja vacío (solo para desarrollo local)
   - Guarda y continúa
4. Crea el OAuth client ID:
   - Tipo de aplicación: "Web application"
   - Nombre: "Music Buzzer Web Client"
   - **Authorized redirect URIs**: Agrega `http://localhost:8000/auth/youtube/callback`
   - Haz clic en "Create"
5. **Copia el Client ID y Client Secret**

### 3. Configurar variables de entorno

Agrega las siguientes variables de entorno antes de iniciar el backend:

```bash
# Windows (PowerShell)
$env:GOOGLE_CLIENT_ID="tu-client-id-aqui"
$env:GOOGLE_CLIENT_SECRET="tu-client-secret-aqui"
$env:GOOGLE_REDIRECT_URI="http://localhost:8000/auth/youtube/callback"

# Windows (CMD)
set GOOGLE_CLIENT_ID=tu-client-id-aqui
set GOOGLE_CLIENT_SECRET=tu-client-secret-aqui
set GOOGLE_REDIRECT_URI=http://localhost:8000/auth/youtube/callback
```

O crea un archivo `.env` en el directorio `backend/` (necesitarás instalar `python-dotenv`):

```
GOOGLE_CLIENT_ID=tu-client-id-aqui
GOOGLE_CLIENT_SECRET=tu-client-secret-aqui
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/youtube/callback
```

### 4. Instalar dependencias

```bash
cd backend
venv/Scripts/activate
pip install -r requirements.txt
```

### 5. Usar la autenticación

1. Inicia el backend
2. En el frontend, selecciona "YouTube Music" como fuente
3. Haz clic en "Autenticarse con YouTube"
4. Serás redirigido a Google para autorizar la aplicación
5. Después de autorizar, serás redirigido de vuelta a la aplicación
6. Ahora puedes importar playlists de YouTube sin problemas de bloqueo

## Notas importantes

- El token OAuth2 se guarda en memoria (solo durante la sesión del backend)
- Si reinicias el backend, necesitarás autenticarte nuevamente
- El token puede expirar; si eso sucede, simplemente autentícate de nuevo
- En producción, deberías usar un almacenamiento persistente para los tokens (base de datos)

## Solución de problemas

**Error: "Google OAuth2 no está configurado"**
- Verifica que las variables de entorno estén configuradas correctamente
- Reinicia el backend después de configurar las variables

**Error: "redirect_uri_mismatch"**
- Verifica que la URI de redirección en Google Cloud Console sea exactamente: `http://localhost:8000/auth/youtube/callback`
- Debe coincidir exactamente con `GOOGLE_REDIRECT_URI`

**Error: "access_denied"**
- Asegúrate de haber habilitado la YouTube Data API v3 en Google Cloud Console
- Verifica que el proyecto tenga los permisos correctos
