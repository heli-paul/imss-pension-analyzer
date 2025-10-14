"""
FastAPI main application con sistema de invitaciones.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routes import auth, analysis, admin
from .config import get_settings
from .database import engine, Base

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Obtener configuración
settings = get_settings()

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)
logger.info("✅ Base de datos inicializada")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para análisis de constancias IMSS con sistema de invitaciones"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(admin.router)

logger.info("✅ Routers registrados: auth, analysis, admin")


@app.get("/")
async def root():
    """
    Endpoint raíz de la API.
    """
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.on_event("startup")
async def startup_event():
    """
    Eventos al iniciar la aplicación.
    """
    logger.info(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📊 Base de datos: {settings.DATABASE_URL}")
    logger.info(f"🌐 CORS origins: {settings.CORS_ORIGINS}")
    
    if settings.SENDGRID_API_KEY:
        logger.info("✅ SendGrid configurado")
    else:
        logger.warning("⚠️  SendGrid NO configurado - Los emails no se enviarán")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Eventos al cerrar la aplicación.
    """
    logger.info(f"👋 Cerrando {settings.APP_NAME}")


