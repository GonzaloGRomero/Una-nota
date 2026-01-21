# 🔧 Solución: Error 400 invalid_request en YouTube OAuth

El error "Error 400: invalid_request" generalmente ocurre porque `GOOGLE_REDIRECT_URI` no está configurado correctamente o no coincide con lo configurado en Google Cloud Console.

## ✅ Solución

### Paso 1: Configurar GOOGLE_REDIRECT_URI en Railway

1. Ve a Railway → Tu proyecto → Backend service → **Variables**
2. Agrega/verifica esta variable:
   ```
   GOOGLE_REDIRECT_URI = https://juego-en-una-nota-production-0f49.up.railway.app/auth/youtube/callback
   ```
   **IMPORTANTE**: 
   - Debe ser la URL completa de tu backend
   - Debe terminar en `/auth/youtube/callback`
   - NO debe tener `/` al final

3. Railway reiniciará automáticamente

### Paso 2: Verificar en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto
3. Ve a **APIs & Services** → **Credentials**
4. Click en tu **OAuth 2.0 Client ID**
5. En **Authorized redirect URIs**, verifica que esté:
   ```
   https://juego-en-una-nota-production-0f49.up.railway.app/auth/youtube/callback
   ```
6. Si NO está, agrégala y guarda

### Paso 3: Verificar otras variables

Asegúrate de que también estén configuradas en Railway:

```
GOOGLE_CLIENT_ID = tu_client_id
GOOGLE_CLIENT_SECRET = tu_client_secret
```

## 🐛 Verificación

Después de configurar:

1. Reinicia el backend (Railway lo hace automáticamente)
2. Intenta autenticarte de nuevo con YouTube
3. Si sigue fallando, revisa los logs de Railway para ver el error exacto

## 📝 Notas

- El `GOOGLE_REDIRECT_URI` debe coincidir **EXACTAMENTE** con el configurado en Google Cloud Console
- No puede tener espacios al inicio o final
- Debe usar `https://` (Railway usa HTTPS)
- La ruta debe ser exactamente `/auth/youtube/callback`


