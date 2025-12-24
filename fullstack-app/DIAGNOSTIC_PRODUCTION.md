# 🔍 Diagnóstico de Problemas de Conexión

Si estás recibiendo "Failed to fetch" al intentar crear una sala, sigue estos pasos:

## ✅ Verificación Rápida

### 1. ¿Estás probando localmente o en producción?

#### Si es LOCAL (desarrollo):
- Verifica que el backend esté corriendo en `http://localhost:8000`
- Verifica que el frontend use `http://localhost:8000` (default)
- Verifica que no haya errores de CORS en la consola del navegador

#### Si es PRODUCCIÓN (Vercel):
- Verifica que el backend esté funcionando: `https://juego-en-una-nota-production.up.railway.app`
- Verifica que las variables de entorno estén configuradas en Vercel

## 🔧 Solución Paso a Paso

### Paso 1: Verificar que el Backend está funcionando

Abre en el navegador:
```
https://juego-en-una-nota-production.up.railway.app
```

Deberías ver:
```json
{"message": "Music buzzer backend activo", "tracks": [...]}
```

Si NO ves esto:
- El backend no está funcionando
- Ve a Railway y verifica los logs
- Verifica que el servicio esté activo

### Paso 2: Verificar Variables de Entorno en Vercel

1. Ve a Vercel → Tu proyecto → Settings → Environment Variables
2. Verifica que existan estas variables:
   - `REACT_APP_API_URL` = `https://juego-en-una-nota-production.up.railway.app`
   - `REACT_APP_WS_URL` = `wss://juego-en-una-nota-production.up.railway.app/ws/sala`

3. Si NO existen o están mal:
   - Agrégalas/corrígelas
   - **IMPORTANTE**: Haz un nuevo deploy (Vercel → Deployments → Redeploy)

### Paso 3: Verificar Variables de Entorno en Railway

1. Ve a Railway → Tu proyecto → Backend service → Variables
2. Verifica que exista:
   - `FRONTEND_URL` = URL de tu frontend en Vercel (ej: `https://una-nota-two.vercel.app`)

3. Si NO existe:
   - Agrégala
   - Railway reiniciará automáticamente

### Paso 4: Verificar en la Consola del Navegador

1. Abre tu aplicación en el navegador
2. Presiona F12 para abrir DevTools
3. Ve a la pestaña "Console"
4. Intenta crear una sala
5. Revisa los errores:

#### Error de CORS:
```
Access to fetch at 'https://...' from origin 'https://...' has been blocked by CORS policy
```
**Solución**: Verifica que `FRONTEND_URL` en Railway coincida exactamente con la URL de Vercel

#### Error de red:
```
Failed to fetch
```
**Solución**: 
- Verifica que el backend esté funcionando (Paso 1)
- Verifica que `REACT_APP_API_URL` esté configurado en Vercel
- Verifica que hayas hecho redeploy después de agregar las variables

#### Error 404:
```
404 Not Found
```
**Solución**: Verifica que la URL del backend sea correcta

### Paso 5: Verificar la URL que está usando el Frontend

1. Abre la consola del navegador (F12)
2. En la pestaña "Network", intenta crear una sala
3. Busca la petición a `/rooms/create`
4. Revisa la URL completa:
   - Si dice `http://localhost:8000` → Las variables NO están configuradas en Vercel
   - Si dice `https://juego-en-una-nota-production.up.railway.app` → Las variables están bien

## 🐛 Problemas Específicos

### El frontend usa localhost en producción
- **Causa**: `REACT_APP_API_URL` no está configurado en Vercel
- **Solución**: Agrega la variable en Vercel y haz redeploy

### Error de CORS
- **Causa**: `FRONTEND_URL` no está configurado en Railway o no coincide
- **Solución**: 
  1. Verifica la URL exacta de tu frontend en Vercel
  2. Agrega/actualiza `FRONTEND_URL` en Railway con esa URL exacta (incluyendo `https://`)

### El backend no responde
- **Causa**: El servicio está pausado o tiene errores
- **Solución**: 
  1. Ve a Railway → Logs
  2. Revisa los errores
  3. Verifica que el servicio esté activo

## ✅ Checklist Final

- [ ] Backend responde en `https://juego-en-una-nota-production.up.railway.app`
- [ ] `REACT_APP_API_URL` está configurado en Vercel
- [ ] `REACT_APP_WS_URL` está configurado en Vercel
- [ ] `FRONTEND_URL` está configurado en Railway
- [ ] Se hizo redeploy en Vercel después de agregar las variables
- [ ] No hay errores de CORS en la consola del navegador
- [ ] La URL en Network tab muestra la URL correcta del backend (no localhost)
