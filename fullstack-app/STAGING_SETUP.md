# Configuración de Entorno de Staging/Desarrollo

Esta guía te ayudará a configurar un entorno de prueba separado de producción para poder probar cambios antes de hacer merge a `master`.

## Opción 1: Entorno de Staging en Railway y Vercel (Recomendado)

### Backend (Railway)

1. **Crear un nuevo proyecto en Railway:**
   - Ve a https://railway.app/
   - Click en "New Project"
   - Selecciona "Deploy from GitHub repo"
   - Selecciona tu repositorio
   - **Importante:** En "Settings" → "Source", cambia la branch a `develop` (o la branch que quieras usar para staging)

2. **Configurar variables de entorno:**
   - Ve a "Variables" en el proyecto de staging
   - Agrega las mismas variables que en producción:
     ```
     GOOGLE_CLIENT_ID=tu_client_id
     GOOGLE_CLIENT_SECRET=tu_client_secret
     GOOGLE_REDIRECT_URI=https://tu-backend-staging.up.railway.app/auth/youtube/callback
     FRONTEND_URL=https://tu-frontend-staging.vercel.app
     ```
   - **Nota:** Usa URLs diferentes para staging

3. **Configurar Root Directory:**
   - En "Settings" → "Root Directory", establece: `fullstack-app/backend`

4. **Obtener la URL del backend de staging:**
   - Ve a "Settings" → "Domains"
   - Copia la URL pública (ej: `tu-proyecto-staging.up.railway.app`)

### Frontend (Vercel)

1. **Crear un nuevo proyecto en Vercel:**
   - Ve a https://vercel.com/
   - Click en "Add New..." → "Project"
   - Importa tu repositorio de GitHub
   - **Importante:** En "Configure Project", cambia la branch a `develop`

2. **Configurar variables de entorno:**
   - Ve a "Settings" → "Environment Variables"
   - Agrega:
     ```
     REACT_APP_API_URL=https://tu-backend-staging.up.railway.app
     REACT_APP_WS_URL=wss://tu-backend-staging.up.railway.app/ws/sala
     ```
   - **Nota:** Usa `wss://` (WebSocket seguro) si Railway usa HTTPS

3. **Configurar Root Directory:**
   - En "Settings" → "General" → "Root Directory", establece: `fullstack-app/frontend`

4. **Obtener la URL del frontend de staging:**
   - Después del deploy, Vercel te dará una URL (ej: `tu-proyecto-staging.vercel.app`)

### Actualizar URLs en Google Cloud Console

1. Ve a https://console.cloud.google.com/
2. Ve a "APIs & Services" → "Credentials"
3. Click en tu OAuth Client ID
4. En "Authorized redirect URIs", agrega:
   ```
   https://tu-backend-staging.up.railway.app/auth/youtube/callback
   ```

---

## Opción 2: Desarrollo Local con Variables de Entorno

### Backend Local

1. **Crear archivo `.env` en `backend/`:**
   ```env
   GOOGLE_CLIENT_ID=tu_client_id
   GOOGLE_CLIENT_SECRET=tu_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/youtube/callback
   FRONTEND_URL=http://localhost:3000
   PORT=8000
   ```

2. **Instalar dependencias:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Ejecutar:**
   ```bash
   python main.py
   ```

### Frontend Local

1. **Crear archivo `.env` en `frontend/`:**
   ```env
   REACT_APP_API_URL=http://localhost:8000
   REACT_APP_WS_URL=ws://localhost:8000/ws/sala
   PORT=3000
   ```

2. **Instalar dependencias:**
   ```bash
   cd frontend
   npm install
   ```

3. **Ejecutar:**
   ```bash
   npm start
   ```

---

## Flujo de Trabajo Recomendado

1. **Desarrollo:**
   - Trabaja en la branch `develop` (o crea branches feature desde `develop`)
   - Haz commits y push a `develop`
   - Railway y Vercel staging se actualizarán automáticamente

2. **Testing:**
   - Prueba en el entorno de staging
   - Verifica que todo funcione correctamente

3. **Producción:**
   - Cuando estés listo, haz merge de `develop` a `master`
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

- **Staging y Producción son completamente independientes:** Cada uno tiene su propia base de datos, salas, y estado
- **Las contraseñas de salas en staging no afectan producción:** Son entornos separados
- **Los tokens de YouTube OAuth:** Puedes usar la misma cuenta, pero necesitas agregar ambas URLs de callback en Google Cloud Console
- **Costos:** Railway y Vercel tienen planes gratuitos generosos, pero verifica los límites

---

## Troubleshooting

### El frontend no se conecta al backend de staging
- Verifica que `REACT_APP_API_URL` y `REACT_APP_WS_URL` apunten a la URL correcta de staging
- Verifica que el backend de staging esté corriendo
- Revisa los logs de Railway para errores

### Error de CORS
- Verifica que `FRONTEND_URL` en el backend incluya la URL de staging de Vercel
- Verifica que `allow_origins` en `main.py` incluya la URL de staging

### WebSocket no conecta
- Verifica que uses `wss://` (no `ws://`) si Railway usa HTTPS
- Verifica que el endpoint `/ws/sala` esté accesible
