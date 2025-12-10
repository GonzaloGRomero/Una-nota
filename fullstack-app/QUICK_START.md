# 🚀 Inicio Rápido - GitHub Pages + Railway

## ✅ Paso 1: Asegúrate de que los cambios estén guardados

1. Haz commit de todos los cambios:
```bash
git add .
git commit -m "Fix ESLint errors and prepare for deployment"
git push origin main
```

## 🔧 Paso 2: Configurar GitHub Pages

1. Ve a tu repositorio en GitHub
2. Click en **Settings** (Configuración)
3. En el menú lateral, busca **Pages**
4. En **Source**, selecciona **"GitHub Actions"**
5. Guarda los cambios

## 🔐 Paso 3: Configurar la URL del Backend (Railway)

1. En Railway, ve a tu servicio del backend
2. Copia la URL pública (ejemplo: `https://tu-backend-production.up.railway.app`)
3. La URL del WebSocket será: `wss://tu-backend-production.up.railway.app/ws/sala`

4. En GitHub:
   - Ve a **Settings** > **Secrets and variables** > **Actions**
   - Click en **"New repository secret"**
   - **Name**: `REACT_APP_WS_URL`
   - **Value**: `wss://tu-backend-production.up.railway.app/ws/sala`
   - Click en **"Add secret"**

## 🚀 Paso 4: Desplegar

1. Haz push a main (si aún no lo hiciste):
```bash
git push origin main
```

2. Ve a la pestaña **Actions** en GitHub
3. Verás el workflow "Deploy to GitHub Pages" ejecutándose
4. Espera 2-5 minutos
5. Una vez completado, tu sitio estará en:
   - `https://tu-usuario.github.io/tu-repositorio`

## ✅ Verificación

1. Abre la URL de GitHub Pages en tu navegador
2. Abre la consola del navegador (F12)
3. Verifica que no haya errores de conexión
4. Prueba conectarte como jugador u organizador

## 🐛 Si Railway sigue dando error

1. **Elimina el servicio actual** en Railway
2. **Crea uno nuevo** y asegúrate de:
   - Root Directory: `backend`
   - No debe intentar compilar el frontend

3. O verifica en Railway Settings que el Root Directory esté configurado como `backend`
