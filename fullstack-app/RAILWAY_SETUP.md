# 🚂 Guía de Despliegue en Railway

Esta guía te ayudará a desplegar el backend de Music Buzzer Game en Railway.

## 📋 Requisitos Previos

- Cuenta de GitHub (para conectar el repositorio)
- Cuenta en Railway (gratis): https://railway.app

## 🚀 Paso 1: Crear Cuenta en Railway

1. Ve a https://railway.app
2. Click en **"Login"** o **"Start a New Project"**
3. Selecciona **"Login with GitHub"** (recomendado)
4. Autoriza Railway para acceder a tu cuenta de GitHub

## 🔧 Paso 2: Crear un Nuevo Proyecto

1. En el dashboard de Railway, click en **"New Project"**
2. Selecciona **"Deploy from GitHub repo"**
3. Autoriza Railway si es necesario
4. Selecciona tu repositorio `fullstack-app`
5. Railway detectará automáticamente que es un proyecto con múltiples servicios

## 🎯 Paso 3: Configurar el Backend

### Opción A: Configuración Manual (Recomendado)

1. En el proyecto de Railway, click en **"New Service"**
2. Selecciona **"GitHub Repo"** nuevamente
3. Selecciona tu repositorio
4. Railway te preguntará qué directorio usar
5. **IMPORTANTE**: En **"Root Directory"**, escribe: `backend`
6. Click en **"Deploy"**

**⚠️ Nota**: Si no especificas el Root Directory como `backend`, Railway intentará compilar el frontend y fallará.

### Opción B: Usando railway.json (Ya configurado)

El archivo `backend/railway.json` ya está creado y Railway lo detectará automáticamente si seleccionas el directorio `backend`.

## ⚙️ Paso 4: Configurar Variables de Entorno

1. En el servicio del backend, ve a la pestaña **"Variables"**
2. Click en **"New Variable"** para cada una:

### Variables Requeridas (Opcional pero recomendado):

```
SPOTIFY_CLIENT_ID=tu_client_id_aqui
SPOTIFY_CLIENT_SECRET=tu_client_secret_aqui
```

### Variables para YouTube OAuth2 (Opcional):

```
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_client_secret
GOOGLE_REDIRECT_URI=https://tu-backend.railway.app/auth/youtube/callback
```

**Nota**: Obtendrás la URL de tu backend después del primer deploy. Railway la mostrará en el dashboard.

## 🔍 Paso 5: Verificar el Deploy

1. Railway comenzará a construir y desplegar automáticamente
2. Ve a la pestaña **"Deployments"** para ver el progreso
3. Una vez completado, verás una URL como: `https://tu-backend-production.up.railway.app`
4. Click en la URL para verificar que el backend está funcionando
5. Deberías ver: `{"message": "Music buzzer backend activo", ...}`

## 🔗 Paso 6: Obtener la URL del WebSocket

1. En el dashboard de Railway, en tu servicio del backend
2. Ve a la pestaña **"Settings"**
3. Busca **"Domains"** o **"Public URL"**
4. Copia la URL (ejemplo: `https://tu-backend-production.up.railway.app`)
5. La URL del WebSocket será: `wss://tu-backend-production.up.railway.app/ws/sala`

**Importante**: 
- Si Railway te da una URL con `https://`, usa `wss://` para WebSocket
- Si es `http://`, usa `ws://` (aunque Railway normalmente usa HTTPS)

## 🔐 Paso 7: Configurar GitHub Secrets

1. Ve a tu repositorio en GitHub
2. **Settings** > **Secrets and variables** > **Actions**
3. Click en **"New repository secret"**
4. Nombre: `REACT_APP_WS_URL`
5. Valor: `wss://tu-backend-production.up.railway.app/ws/sala`
6. Click en **"Add secret"**

## 🛠️ Paso 8: Configurar el Puerto (Si es necesario)

Railway automáticamente detecta el puerto, pero si necesitas configurarlo manualmente:

1. En Railway, ve a **Settings** > **Variables**
2. Agrega una variable:
   - Nombre: `PORT`
   - Valor: `8000` (o el puerto que uses)

**Nota**: Railway normalmente inyecta `PORT` automáticamente. Verifica en `main.py` que uses:
```python
import os
port = int(os.getenv("PORT", 8000))
```

## 📝 Paso 9: Verificar que main.py use el Puerto Correcto

Abre `backend/main.py` y verifica que el servidor use la variable de entorno PORT:

```python
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

## 🔄 Paso 10: Actualizar GOOGLE_REDIRECT_URI

Si usas YouTube OAuth2:

1. Ve a Railway > Variables
2. Actualiza `GOOGLE_REDIRECT_URI` con la URL real de tu backend:
   ```
   GOOGLE_REDIRECT_URI=https://tu-backend-production.up.railway.app/auth/youtube/callback
   ```
3. También actualiza esto en Google Cloud Console (en los redirect URIs permitidos)

## ✅ Verificación Final

1. ✅ Backend desplegado en Railway
2. ✅ URL del backend obtenida
3. ✅ Variables de entorno configuradas
4. ✅ `REACT_APP_WS_URL` configurado en GitHub Secrets
5. ✅ Backend responde en la URL de Railway
6. ✅ WebSocket funciona (puedes probarlo con una herramienta como WebSocket King)

## 🐛 Solución de Problemas

### El deploy falla con error de npm/build

**Problema**: Railway está intentando compilar el frontend en lugar del backend.

**Solución**:
1. Ve a tu servicio en Railway
2. Click en **Settings**
3. Busca **"Root Directory"** o **"Source"**
4. Asegúrate de que esté configurado como: `backend`
5. Si no existe esta opción, elimina el servicio y créalo de nuevo especificando `backend` como Root Directory

### El deploy falla

- **Revisa los logs**: En Railway, ve a la pestaña "Deployments" y click en el deployment fallido para ver los logs
- **Verifica requirements.txt**: Asegúrate de que todas las dependencias estén listadas
- **Verifica Python version**: Railway usa Python 3.11 por defecto, asegúrate de que tu código sea compatible
- **Verifica Root Directory**: Debe ser `backend`, no la raíz del proyecto

### El backend no responde

- **Verifica la URL**: Asegúrate de usar la URL correcta de Railway
- **Revisa los logs**: Los logs en Railway mostrarán errores
- **Verifica el puerto**: Railway inyecta `PORT` automáticamente, no uses un puerto fijo

### WebSocket no funciona

- **Verifica el protocolo**: Usa `wss://` para HTTPS, `ws://` para HTTP
- **Verifica CORS**: Asegúrate de que el backend permita CORS desde tu dominio de GitHub Pages
- **Revisa los logs**: Los errores de WebSocket aparecerán en los logs de Railway

### Variables de entorno no funcionan

- **Verifica el nombre**: Los nombres deben coincidir exactamente (case-sensitive)
- **Reinicia el servicio**: Después de agregar variables, Railway reinicia automáticamente
- **Revisa los logs**: Los errores de variables aparecerán en los logs

## 💰 Planes de Railway

- **Hobby Plan (Gratis)**: 
  - $5 de crédito gratis al mes
  - Suficiente para proyectos pequeños
  - El servicio se pausa después de usar el crédito

- **Pro Plan ($20/mes)**:
  - Crédito ilimitado
  - Mejor para producción

## 📚 Recursos Adicionales

- Documentación de Railway: https://docs.railway.app
- Soporte: https://railway.app/discord

## 🎉 ¡Listo!

Tu backend debería estar funcionando en Railway. La URL será algo como:
- `https://tu-backend-production.up.railway.app`

Y el WebSocket en:
- `wss://tu-backend-production.up.railway.app/ws/sala`
