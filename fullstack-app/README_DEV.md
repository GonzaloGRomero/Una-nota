# Desarrollo Local

## Inicio Rápido

**Ejecuta desde la raíz del proyecto:**
```cmd
start_dev.bat
```

Este script inicia backend y frontend en ventanas separadas.

## Configuración Manual

### Backend

1. Ve a la carpeta backend:
   ```cmd
   cd backend
   ```

2. Crea entorno virtual (solo primera vez):
   ```cmd
   python -m venv venv
   ```

3. Activa entorno virtual:
   ```cmd
   venv\Scripts\activate
   ```

4. Instala dependencias (solo primera vez):
   ```cmd
   pip install -r requirements.txt
   ```

5. Crea archivo `.env` desde `.env.example`:
   ```cmd
   copy .env.example .env
   ```
   (Opcional: edita `.env` para agregar credenciales)

6. Inicia el servidor:
   ```cmd
   python main.py
   ```
   O usa el script: `start.bat`

El backend estará en: **http://localhost:8000**

### Frontend

1. Ve a la carpeta frontend:
   ```cmd
   cd frontend
   ```

2. Instala dependencias (solo primera vez):
   ```cmd
   npm install
   ```

3. Crea archivo `.env` desde `.env.example`:
   ```cmd
   copy .env.example .env
   ```

4. Inicia el servidor:
   ```cmd
   npm start
   ```

El frontend estará en: **http://localhost:3000**

## Notas

- Los archivos `.env` no se suben a git (están en `.gitignore`)
- Para producción, usa la branch `master` que se despliega automáticamente
