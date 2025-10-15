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
   - **Region:** Oregon (US West)
   - **Plan:** Free
4. Click en "Create Database"
5. **IMPORTANTE:** Guarda la "Internal Database URL"

---

## 🌐 Paso 3: Crear Web Service

1. En el dashboard, click en "New +" → "Web Service"
2. Conecta tu repositorio: `heli-paul/imss-pension-analyzer`
3. Configuración:

**Name:** imss-pension-api
**Branch:** main
**Runtime:** Docker
**Start Command:** uvicorn src.api.main:app --host 0.0.0.0 --port $PORT

---

## 🔐 Paso 4: Variables de Entorno

Genera claves secretas:

\`\`\`bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
\`\`\`

Configura en Render:
- SECRET_KEY
- JWT_SECRET_KEY
- DATABASE_URL (desde PostgreSQL)
- SENDGRID_API_KEY
- SENDGRID_FROM_EMAIL
- FRONTEND_URL
- BACKEND_URL

---

## ✅ Paso 5: Deploy

1. Click en "Create Web Service"
2. Espera ~5 minutos
3. Tu API estará en: `https://imss-pension-api.onrender.com`

---

## 🔄 Auto-Deploy

Cada push a `main` desplegará automáticamente.

---

**Última actualización:** Octubre 2025
