# 🚀 Guía de Deployment - Render

Esta guía te ayudará a desplegar el proyecto en Render.com

---

## 📋 Prerrequisitos

- Cuenta en GitHub (ya tienes ✅)
- Cuenta en Render.com (crear gratis)
- Cuenta en SendGrid (ya tienes ✅)

---

## 🎯 Paso 1: Crear cuenta en Render

1. Ve a https://render.com
2. Click en "Get Started"
3. Conecta con tu cuenta de GitHub
4. Autoriza a Render para acceder a tus repositorios

---

## 🗄️ Paso 2: Crear PostgreSQL Database

1. En el dashboard de Render, click en "New +"
2. Selecciona "PostgreSQL"
3. Configuración:
   - **Name:** `imss-pension-db`
   - **Database:** `imss_pension`
   - **User:** (se genera automáticamente)
   - **Region:** Oregon (US West) - es gratis
   - **PostgreSQL Version:** 16
   - **Plan:** Free
4. Click en "Create Database"
5. **IMPORTANTE:** Guarda la "Internal Database URL" que aparece

---

## 🌐 Paso 3: Crear Web Service

1. En el dashboard, click en "New +" → "Web Service"
2. Conecta tu repositorio: `heli-paul/imss-pension-analyzer`
3. Configuración:

### Configuración Básica:
```
Name: imss-pension-api
Region: Oregon (US West)
Branch: main
Root Directory: (dejar vacío)
Runtime: Docker
```

### Build Command:
```bash
# Render detectará automáticamente el Dockerfile
# No necesitas especificar nada aquí
```

### Start Command:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

### Plan:
- Selecciona "Free" (0$/mes)

---

## 🔐 Paso 4: Configurar Variables de Entorno

En la sección "Environment Variables" del Web Service, agrega:

```bash
# Seguridad
SECRET_KEY=tu_clave_secreta_aqui_genera_una_nueva
JWT_SECRET_KEY=tu_jwt_secret_aqui_genera_otra
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Base de datos (copiar de tu PostgreSQL en Render)
DATABASE_URL=postgresql://user:password@host:5432/imss_pension

# SendGrid
SENDGRID_API_KEY=SG.tu_api_key_aqui
SENDGRID_FROM_EMAIL=contacto@pensionasoft.com
SENDGRID_FROM_NAME=Pensionasoft

# URLs (actualizar después del primer deploy)
FRONTEND_URL=https://pensionasoft.com
BACKEND_URL=https://imss-pension-api.onrender.com
```

### 🔑 Generar claves secretas:

En tu terminal local, genera claves seguras:

```bash
# Generar SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generar JWT_SECRET_KEY (diferente)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📦 Paso 5: Deploy

1. Click en "Create Web Service"
2. Render automáticamente:
   - Clonará tu repositorio
   - Construirá la imagen Docker
   - Iniciará la aplicación
3. Esto toma ~5 minutos la primera vez

---

## ✅ Paso 6: Verificar el Deployment

Una vez que el deploy termine:

1. Render te dará una URL: `https://imss-pension-api.onrender.com`
2. Verifica que funciona:
   ```bash
   # Healthcheck
   curl https://imss-pension-api.onrender.com/health
   
   # Documentación
   # Abre en navegador: https://imss-pension-api.onrender.com/docs
   ```

---

## 🔄 Paso 7: Configurar Auto-Deploy

1. En tu Web Service en Render, ve a "Settings"
2. En "Auto-Deploy", asegúrate que esté **Yes**
3. Configura:
   - **Branch:** `main`
   - **Auto-Deploy:** Yes

Ahora cada vez que hagas push a `main`, Render automáticamente hará deploy.

---

## 🗂️ Paso 8: Ejecutar Migraciones

Después del primer deploy exitoso, necesitas crear las tablas:

1. En Render, ve a tu Web Service
2. Click en "Shell" (en el menú izquierdo)
3. Ejecuta:
   ```bash
   python -m migrations.add_invitations
   ```

---

## 🎉 ¡Listo!

Tu API está en producción en: `https://imss-pension-api.onrender.com`

### Endpoints disponibles:
- Docs: `https://imss-pension-api.onrender.com/docs`
- Health: `https://imss-pension-api.onrender.com/health`
- Login: `https://imss-pension-api.onrender.com/auth/login/json`

---

## 🐛 Troubleshooting

### Error: "Application failed to start"
1. Revisa los logs en Render
2. Verifica que todas las variables de entorno estén configuradas
3. Verifica que `DATABASE_URL` sea correcta

### Error: "Database connection failed"
1. Asegúrate de usar la "Internal Database URL" de Render
2. Verifica que el formato sea: `postgresql://user:pass@host:5432/dbname`

### Error: "ModuleNotFoundError"
1. Verifica que `requirements.txt` esté actualizado
2. Haz un rebuild manual en Render

---

## 📊 Monitoreo

Render te proporciona:
- **Logs en tiempo real:** Para debuggear
- **Métricas:** CPU, Memoria, Requests
- **Alerts:** Notificaciones por email si algo falla

---

## 💰 Plan Free de Render

El plan gratuito incluye:
- ✅ 750 horas/mes (suficiente para 1 app 24/7)
- ✅ PostgreSQL con 1GB storage
- ✅ Auto-deploy desde GitHub
- ✅ SSL/HTTPS automático
- ⚠️ Se duerme después de 15 min de inactividad (first request toma ~30 seg)

---

## 🔄 Workflow después del setup

```bash
# 1. Hacer cambios en develop
git checkout develop
# ... hacer cambios ...
git add .
git commit -m "feat: nueva funcionalidad"
git push origin develop

# 2. Cuando esté listo para producción
git checkout main
git merge develop
git push origin main

# 3. Render automáticamente hará deploy 🎉
```

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en Render
2. Verifica las variables de entorno
3. Consulta la documentación de Render: https://render.com/docs

---

**Última actualización:** Octubre 2025


