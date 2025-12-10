# Configuración de Cookies de YouTube

Para evitar que YouTube detecte las solicitudes como bots, puedes usar cookies de sesión de YouTube.

## Cómo obtener las cookies

### Opción 1: Usando una extensión del navegador (Recomendado)

1. Instala la extensión "Get cookies.txt LOCALLY" o "cookies.txt" en Chrome/Edge
2. Ve a https://www.youtube.com (asegúrate de estar logueado)
3. Haz clic en la extensión y exporta las cookies
4. Guarda el archivo como `youtube_cookies.txt` en la carpeta `backend/`

### Opción 2: Usando variable de entorno

1. Exporta las cookies usando una extensión o herramienta
2. Guarda el archivo en cualquier ubicación
3. Configura la variable de entorno:
   ```bash
   # Windows (PowerShell)
   $env:YOUTUBE_COOKIES_FILE="C:\ruta\a\tu\cookies.txt"
   
   # Windows (CMD)
   set YOUTUBE_COOKIES_FILE=C:\ruta\a\tu\cookies.txt
   ```

## Formato del archivo de cookies

El archivo debe estar en formato Netscape (el que exportan las extensiones). Ejemplo:

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	1734567890	VISITOR_INFO1_LIVE	abc123...
.youtube.com	TRUE	/	FALSE	1734567890	YSC	def456...
```

## Notas importantes

- Las cookies expiran después de un tiempo. Si YouTube vuelve a bloquear, exporta nuevas cookies.
- No compartas tus cookies públicamente, contienen información de tu sesión.
- El archivo `youtube_cookies.txt` está en `.gitignore` para no subirlo al repositorio.

## Verificación

Si las cookies están configuradas correctamente, verás en los logs del backend:
```
DEBUG: Usando cookies de YouTube desde: f:\programacion\fullstack-app\backend\youtube_cookies.txt
```
