# 🚀 Guía Rápida: Configurar GitHub Pages

Sigue estos pasos para desplegar tu aplicación en GitHub Pages:

## 📝 Paso 1: Preparar el Repositorio

1. **Inicializa Git** (si no lo has hecho):
```bash
git init
git add .
git commit -m "Initial commit"
```

2. **Crea el repositorio en GitHub** y conéctalo:
```bash
git remote add origin https://github.com/tu-usuario/tu-repositorio.git
git branch -M main
git push -u origin main
```

## ⚙️ Paso 2: Configurar GitHub Pages

1. Ve a tu repositorio en GitHub
2. Click en **Settings** (Configuración)
3. En el menú lateral, busca **Pages**
4. En **Source**, selecciona **"GitHub Actions"**
5. Guarda los cambios

## 🔐 Paso 3: Configurar el Backend URL (Opcional)

Si tu backend está desplegado en otro servidor (Railway, Render, etc.):

1. Ve a **Settings** > **Secrets and variables** > **Actions**
2. Click en **"New repository secret"**
3. Nombre: `REACT_APP_WS_URL`
4. Valor: La URL de tu WebSocket (ej: `wss://tu-backend.railway.app/ws/sala`)
5. Click en **"Add secret"**

**Nota**: Si el backend usa HTTP (no HTTPS), usa `ws://` en lugar de `wss://`

## 🚀 Paso 4: Desplegar

1. Haz push a la rama `main`:
```bash
git add .
git commit -m "Prepare for GitHub Pages deployment"
git push origin main
```

2. Ve a la pestaña **Actions** en GitHub
3. Verás el workflow ejecutándose automáticamente
4. Espera a que termine (puede tomar 2-5 minutos)
5. Una vez completado, tu sitio estará disponible en:
   - `https://tu-usuario.github.io/tu-repositorio`

## ✅ Verificación

1. Abre la URL de tu sitio en el navegador
2. Verifica que la aplicación carga correctamente
3. Si el backend está configurado, prueba conectarte

## 🔧 Solución de Problemas

### El workflow falla
- Verifica que el archivo `.github/workflows/deploy.yml` existe
- Revisa los logs en la pestaña Actions para ver el error específico

### El sitio no carga
- Espera unos minutos después del deploy
- Verifica que GitHub Pages esté activado en Settings > Pages
- Limpia la caché del navegador (Ctrl+Shift+R)

### No se conecta al backend
- Verifica que `REACT_APP_WS_URL` esté configurado correctamente en Secrets
- Asegúrate de que el backend esté corriendo y accesible
- Revisa la consola del navegador para errores de conexión

## 📝 Notas Importantes

- **El backend debe estar desplegado por separado** (GitHub Pages solo sirve archivos estáticos)
- **Cada push a main** desplegará automáticamente una nueva versión
- **El build puede tardar** 2-5 minutos la primera vez
- **Los cambios pueden tardar** unos minutos en aparecer después del deploy

## 🎉 ¡Listo!

Una vez completado, tu aplicación estará disponible públicamente en GitHub Pages.
