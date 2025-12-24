# 🔧 Solución de CORS

## ⚠️ IMPORTANTE: Configura FRONTEND_URL en Railway

El código ahora maneja mejor CORS, pero **DEBES configurar** la variable `FRONTEND_URL` en Railway.

### Paso 1: Configurar FRONTEND_URL en Railway

1. Ve a Railway → Tu proyecto → Backend service → **Variables**
2. Agrega esta variable:
   ```
   FRONTEND_URL = https://tu-url-de-vercel.vercel.app
   ```
   **Reemplaza `tu-url-de-vercel.vercel.app` con la URL REAL de tu frontend en Vercel**

3. **IMPORTANTE**: 
   - La URL debe coincidir EXACTAMENTE con la URL de Vercel
   - Incluye `https://` al inicio
   - NO incluyas `/` al final (el código ahora maneja ambas variaciones)

4. Railway reiniciará automáticamente el servicio

### Paso 2: Verificar que funciona

1. Abre tu aplicación en el navegador
2. Abre la consola (F12) → Network tab
3. Intenta crear una sala
4. Si ves errores de CORS, verifica:
   - Que la URL en Railway coincida EXACTAMENTE con la URL de Vercel
   - Que hayas esperado a que Railway reinicie el servicio

### Ejemplo de URLs correctas:

✅ **Correcto:**
```
FRONTEND_URL = https://una-nota-two.vercel.app
```

❌ **Incorrecto:**
```
FRONTEND_URL = una-nota-two.vercel.app        (falta https://)
FRONTEND_URL = https://una-nota-two.vercel.app/  (no debería tener / al final, pero el código lo maneja)
```

## 📋 Checklist

- [ ] Identificaste la URL exacta de tu frontend en Vercel
- [ ] Agregaste `FRONTEND_URL` en Railway con esa URL exacta (con `https://`)
- [ ] Esperaste a que Railway reinicie el servicio
- [ ] Probaste crear una sala y no hay errores de CORS

## 🐛 Si sigue sin funcionar

1. Verifica los logs de Railway para ver si hay el warning:
   ```
   ⚠️ WARNING: FRONTEND_URL no está configurado. CORS permitirá solo localhost.
   ```
   Si ves este warning, significa que la variable no está configurada correctamente.

2. Verifica en la consola del navegador el error exacto de CORS:
   - El error te dirá qué origen está bloqueado
   - Compara ese origen con la URL que configuraste en Railway

3. Asegúrate de que la URL sea EXACTAMENTE la misma (case-sensitive)
