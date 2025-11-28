# 📤 Instrucciones para subir a GitHub

## Paso 1: Crear el repositorio en GitHub
1. Ve a https://github.com/new
2. Nombre del repositorio: `peak-finder-gui` (o el que prefieras)
3. Descripción: "SiPM Waveform Analyzer - GUI para análisis de picos en señales de fotomultiplicadores"
4. Público o Privado (tú eliges)
5. **NO** marques "Add a README file"
6. Click "Create repository"

## Paso 2: Ejecutar estos comandos en PowerShell

Abre PowerShell en este directorio y ejecuta:

```powershell
# Inicializar git (solo la primera vez)
git init

# Añadir todos los archivos
git add .

# Hacer el primer commit
git commit -m "Initial commit: Peak Finder GUI con análisis de waveforms"

# Añadir el repositorio remoto (REEMPLAZA con tu URL de GitHub)
git remote add origin https://github.com/TU_USUARIO/peak-finder-gui.git

# Cambiar a la rama main
git branch -M main

# Subir todo a GitHub
git push -u origin main
```

## Paso 3: Comandos para futuras actualizaciones

Cuando hagas cambios en el futuro:

```powershell
# Ver qué archivos han cambiado
git status

# Añadir los cambios
git add .

# Hacer commit con mensaje descriptivo
git commit -m "Descripción de los cambios"

# Subir a GitHub
git push
```

## 📝 Notas importantes:

- Si no tienes git instalado, descárgalo de: https://git-scm.com/download/win
- La primera vez que hagas push, te pedirá tus credenciales de GitHub
- Si tienes 2FA activado, necesitarás crear un Personal Access Token en GitHub

## 🔐 Crear Personal Access Token (si es necesario):

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token
3. Selecciona "repo" scope
4. Copia el token y úsalo como contraseña cuando git te lo pida

## ⚠️ Datos sensibles:

El archivo `.gitignore` ya está configurado para NO subir:
- Archivos de Python compilados
- Configuraciones del IDE
- Archivos del sistema

Si NO quieres subir tus archivos de datos (*.txt), descomenta estas líneas en `.gitignore`:
```
# *.txt
# SiPMG_*/
```
