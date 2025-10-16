# 🏥 IMSS Pension Analyzer

Sistema de análisis automatizado de constancias de pensión del IMSS con sistema de invitaciones por email.

[![Status](https://img.shields.io/badge/status-development-yellow)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)]()

## 📊 Estado del Proyecto

**Última actualización:** Octubre 2025

### ✅ Funcionalidades Implementadas
- ✅ Backend FastAPI con autenticación JWT
- ✅ Sistema de invitaciones con tokens únicos
- ✅ Envío de emails con SendGrid
- ✅ Parser de constancias IMSS en PDF
- ✅ Base de datos SQLite (desarrollo) / PostgreSQL (producción)
- ✅ API REST completa y documentada
- ✅ Protección de rutas con middleware de autenticación

### 🚧 En Desarrollo
- 🚧 Frontend Next.js (parcial)
- 🚧 Deployment en producción
- 🚧 Dashboard de administración

### ❌ Problemas Conocidos
- ❌ Railway deployment tiene problemas con dependencias
- ❌ Producción actual caída (pensionasoft.com)
- ❌ Migración pendiente a Render u otro servicio

---

## 🚀 Inicio Rápido

### Prerrequisitos
- Python 3.11+
- pip
- virtualenv
- Cuenta SendGrid (para emails)

### Instalación Local

\`\`\`bash
# 1. Clonar repositorio
git clone https://github.com/heli-paul/imss-pension-analyzer.git
cd imss-pension-analyzer

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 5. Ejecutar migraciones
python -m migrations.add_invitations

# 6. Iniciar servidor
uvicorn src.api.main:app --reload --port 8001
\`\`\`

La API estará disponible en: \`http://localhost:8001\`
Documentación interactiva: \`http://localhost:8001/docs\`

---

## 📡 API Endpoints

### Autenticación
- \`POST /auth/register\` - Registro con token de invitación
- \`POST /auth/login/json\` - Login con email/password
- \`POST /auth/validate-token\` - Validar token de invitación

### Administración
- \`POST /admin/invitations\` - Crear nueva invitación
- \`GET /admin/invitations\` - Listar invitaciones
- \`GET /admin/invitations/stats/summary\` - Estadísticas

### Análisis (requiere autenticación)
- \`POST /analysis/upload\` - Subir constancia IMSS
- \`GET /analysis/history\` - Historial de análisis

**Documentación completa:** \`http://localhost:8001/docs\`

---

## 🚢 Deployment

Ver [DEPLOYMENT.md](./DEPLOYMENT.md) para instrucciones detalladas de deployment en Render.

---

## 🔄 Workflow de Git

### Branches
- \`main\` - Producción (stable)
- \`staging\` - Testing pre-producción
- \`develop\` - Desarrollo activo

---

## 📝 Licencia

[Especificar licencia]

---

**Nota:** Este proyecto está en desarrollo activo. Para más información consulta la documentación completa.
# Deploy trigger Thu Oct 16 12:58:57 CST 2025
