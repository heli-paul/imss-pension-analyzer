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

## 🏗️ Arquitectura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Next.js   │─────▶│   FastAPI   │─────▶│ PostgreSQL  │
│  Frontend   │      │   Backend   │      │  Database   │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │  SendGrid   │
                     │   Emails    │
                     └─────────────┘
```

---

## 🚀 Inicio Rápido

### Prerrequisitos
- Python 3.11+
- pip
- virtualenv
- Cuenta SendGrid (para emails)

### Instalación Local

```bash
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
```

La API estará disponible en: `http://localhost:8001`
Documentación interactiva: `http://localhost:8001/docs`

---

## 📁 Estructura del Proyecto

```
imss-pension-analyzer/
├── src/
│   ├── api/
│   │   ├── main.py                    # Aplicación FastAPI principal
│   │   ├── config.py                  # Configuración y variables de entorno
│   │   ├── database.py                # Setup SQLAlchemy
│   │   ├── models/                    # Modelos de base de datos
│   │   │   ├── user.py
│   │   │   └── invitation.py
│   │   ├── routes/                    # Endpoints de API
│   │   │   ├── auth.py                # Autenticación y registro
│   │   │   ├── admin.py               # Gestión de invitaciones
│   │   │   └── analysis.py            # Análisis de PDFs
│   │   ├── schemas/                   # Schemas Pydantic
│   │   │   ├── user.py
│   │   │   └── invitation.py
│   │   └── services/                  # Lógica de negocio
│   │       ├── auth_service.py
│   │       ├── security.py
│   │       ├── invitation_service.py
│   │       └── email_service.py
│   ├── parser/                        # Parser de constancias IMSS
│   └── frontend/                      # Next.js (parcial)
├── migrations/                        # Scripts de migración
├── tests/                            # Tests
├── requirements.txt                   # Dependencias Python
├── Dockerfile                        # Configuración Docker
├── .env.example                      # Variables de entorno template
└── README.md                         # Este archivo
```

---

## 🔑 Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Seguridad
SECRET_KEY=tu_clave_secreta_aqui
JWT_SECRET_KEY=tu_jwt_secret_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Base de datos
DATABASE_URL=sqlite:///./imss_pension.db  # Desarrollo
# DATABASE_URL=postgresql://user:pass@host:5432/dbname  # Producción

# SendGrid
SENDGRID_API_KEY=SG.tu_api_key_aqui
SENDGRID_FROM_EMAIL=contacto@pensionasoft.com
SENDGRID_FROM_NAME=Pensionasoft

# URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8001
```

---

## 📡 API Endpoints

### Autenticación
- `POST /auth/register` - Registro con token de invitación
- `POST /auth/login/json` - Login con email/password
- `POST /auth/validate-token` - Validar token de invitación

### Administración
- `POST /admin/invitations` - Crear nueva invitación
- `GET /admin/invitations` - Listar invitaciones
- `GET /admin/invitations/stats/summary` - Estadísticas

### Análisis (requiere autenticación)
- `POST /analysis/upload` - Subir constancia IMSS
- `GET /analysis/history` - Historial de análisis

**Documentación completa:** `http://localhost:8001/docs`

---

## 🧪 Testing

```bash
# Ejecutar tests
python test_api_invitations.py

# Tests unitarios (TODO)
pytest tests/
```

---

## 🚢 Deployment

### Desarrollo Local
```bash
uvicorn src.api.main:app --reload --port 8001
```

### Producción (Render/Railway)
```bash
# Asegúrate de configurar variables de entorno en el servicio
# El Procfile y Dockerfile están listos para deployment
```

**Estado actual:** Migración pendiente de Railway a Render debido a problemas con dependencias.

---

## 🔄 Workflow de Git

### Branches
- `main` - Producción (stable)
- `staging` - Testing pre-producción
- `develop` - Desarrollo activo

### Contribuir
```bash
# 1. Crear rama desde develop
git checkout develop
git pull origin develop
git checkout -b feature/nombre-feature

# 2. Hacer cambios y commit
git add .
git commit -m "feat: descripción del cambio"

# 3. Push y crear PR
git push origin feature/nombre-feature
# Crear Pull Request a develop en GitHub
```

---

## 📦 Dependencias Principales

- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Pydantic** - Validación de datos
- **SendGrid** - Envío de emails
- **python-jose** - JWT tokens
- **passlib** - Hashing de passwords
- **psycopg2-binary** - PostgreSQL driver

Ver `requirements.txt` para la lista completa.

---

## 🐛 Troubleshooting

### Error: "Module not found sendgrid"
```bash
pip install -r requirements.txt --force-reinstall
```

### Error: "Database not found"
```bash
python -m migrations.add_invitations
```

### Error: "Port already in use"
```bash
# Cambiar puerto
uvicorn src.api.main:app --reload --port 8002
```

---

## 📝 Roadmap

- [ ] Completar frontend Next.js
- [ ] Migrar deployment a Render
- [ ] Implementar tests automatizados
- [ ] Dashboard de administración
- [ ] Soporte para múltiples tipos de constancias
- [ ] API rate limiting
- [ ] Documentación de API con ejemplos

---

## 👥 Equipo

**Desarrollador Principal:** [Tu Nombre]

---

## 📄 Licencia

[Especificar licencia]

---

## 🤝 Soporte

Para soporte o preguntas:
- Email: contacto@pensionasoft.com
- GitHub Issues: [Crear issue](https://github.com/heli-paul/imss-pension-analyzer/issues)

---

**Nota:** Este proyecto está en desarrollo activo. La funcionalidad puede cambiar sin previo aviso.


