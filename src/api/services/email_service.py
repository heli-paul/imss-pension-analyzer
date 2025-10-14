"""
Servicio de envío de emails usando SendGrid.
"""

import os
from typing import Optional, Tuple
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Template

from ..config import get_settings


class EmailService:
    """
    Servicio para envío de emails con SendGrid.
    """
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.SENDGRID_API_KEY
        self.from_email = settings.SENDGRID_FROM_EMAIL
        self.from_name = settings.SENDGRID_FROM_NAME
        self.frontend_url = settings.FRONTEND_URL
        
        if self.api_key:
            self.client = SendGridAPIClient(self.api_key)
        else:
            self.client = None
            print("⚠️  ADVERTENCIA: SENDGRID_API_KEY no configurada.")
    
    def send_invitation_email(
        self,
        to_email: str,
        to_name: str,
        invitation_token: str,
        plan: str,
        cuota_analisis: int,
        admin_name: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Envía email de invitación a un nuevo usuario.
        """
        if not self.client:
            return False, "SendGrid no está configurado"
        
        registration_url = f"{self.frontend_url}/register?token={invitation_token}"
        
        html_content = self._render_invitation_template(
            to_name=to_name,
            registration_url=registration_url,
            plan=plan,
            cuota_analisis=cuota_analisis,
            admin_name=admin_name
        )
        
        message = Mail(
            from_email=Email(self.from_email, self.from_name),
            to_emails=To(to_email, to_name),
            subject="🎉 Has sido invitado a Pensionasoft - Análisis de Constancias IMSS",
            html_content=Content("text/html", html_content)
        )
        
        try:
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                return True, None
            else:
                return False, f"SendGrid respondió con código {response.status_code}"
                
        except Exception as e:
            return False, f"Error al enviar email: {str(e)}"
    
    def send_welcome_email(
        self,
        to_email: str,
        to_name: str,
        plan: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Envía email de bienvenida después del registro.
        """
        if not self.client:
            return False, "SendGrid no está configurado"
        
        html_content = self._render_welcome_template(
            to_name=to_name,
            plan=plan
        )
        
        message = Mail(
            from_email=Email(self.from_email, self.from_name),
            to_emails=To(to_email, to_name),
            subject="✅ ¡Bienvenido a Pensionasoft!",
            html_content=Content("text/html", html_content)
        )
        
        try:
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                return True, None
            else:
                return False, f"SendGrid respondió con código {response.status_code}"
                
        except Exception as e:
            return False, f"Error al enviar email: {str(e)}"
    
    def _render_invitation_template(
        self,
        to_name: str,
        registration_url: str,
        plan: str,
        cuota_analisis: int,
        admin_name: Optional[str] = None
    ) -> str:
        """
        Renderiza el template HTML de invitación.
        """
        template_str = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            color: #2563eb;
            margin: 0;
            font-size: 32px;
        }
        .button {
            display: inline-block;
            background-color: #2563eb;
            color: white;
            text-decoration: none;
            padding: 15px 40px;
            border-radius: 8px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
        .plan-info {
            background-color: #f0f9ff;
            border-left: 4px solid #2563eb;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .footer {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>📊 Pensionasoft</h1>
            <p style="color: #666;">Análisis de Constancias IMSS</p>
        </div>
        
        <h2>¡Hola {{ to_name }}! 👋</h2>
        
        {% if admin_name %}
        <p><strong>{{ admin_name }}</strong> te ha invitado a Pensionasoft.</p>
        {% else %}
        <p>Has sido invitado a Pensionasoft.</p>
        {% endif %}
        
        <div class="plan-info">
            <h3 style="margin-top: 0; color: #2563eb;">Tu Plan: {{ plan|upper }}</h3>
            <p style="margin-bottom: 0;">
                ✅ <strong>{{ cuota_analisis }}</strong> análisis mensuales<br>
                ✅ Extracción automática de datos<br>
                ✅ Exportación a Google Sheets
            </p>
        </div>
        
        <p>Para completar tu registro, haz clic aquí:</p>
        
        <div style="text-align: center;">
            <a href="{{ registration_url }}" class="button">
                Completar Registro
            </a>
        </div>
        
        <p style="font-size: 14px; color: #666;">
            O copia este enlace: {{ registration_url }}
        </p>
        
        <p style="font-size: 14px; color: #666;">
            ⏰ Este enlace expira en 7 días.
        </p>
        
        <div class="footer">
            <p><strong>Pensionasoft</strong></p>
            <p style="font-size: 12px;">Si no solicitaste esta invitación, ignora este correo.</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(
            to_name=to_name,
            registration_url=registration_url,
            plan=plan,
            cuota_analisis=cuota_analisis,
            admin_name=admin_name
        )
    
    def _render_welcome_template(self, to_name: str, plan: str) -> str:
        """
        Renderiza el template HTML de bienvenida.
        """
        template_str = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 10px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .button {
            display: inline-block;
            background-color: #2563eb;
            color: white;
            text-decoration: none;
            padding: 15px 40px;
            border-radius: 8px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 style="color: #2563eb;">📊 Pensionasoft</h1>
        <h2>¡Bienvenido {{ to_name }}! 🎉</h2>
        
        <p>Tu cuenta ha sido creada exitosamente.</p>
        
        <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2563eb;">Primeros pasos:</h3>
            <ol>
                <li><strong>Sube tu constancia PDF</strong></li>
                <li><strong>Revisa los datos extraídos</strong></li>
                <li><strong>Exporta a Google Sheets</strong></li>
            </ol>
        </div>
        
        <div style="text-align: center;">
            <a href="{{ frontend_url }}/upload" class="button">
                Comenzar Ahora
            </a>
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 14px;"><strong>Pensionasoft</strong><br>contacto@pensionasoft.com</p>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(
            to_name=to_name,
            plan=plan,
            frontend_url=self.frontend_url
        )


