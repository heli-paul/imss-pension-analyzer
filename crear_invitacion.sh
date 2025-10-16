#!/bin/bash

EMAIL=$1
NOMBRE=$2
PLAN=${3:-"free"}
CUOTA=${4:-30}

if [ -z "$EMAIL" ]; then
    echo "❌ Error: Debes proporcionar un email"
    exit 1
fi

echo "📧 Creando invitación para: $EMAIL"

RESPONSE=$(curl -s -X POST https://imss-pension-api.onrender.com/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=contacto@pensionasoft.com&password=Admin2024!")

TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Error de autenticación"
    exit 1
fi

RESPONSE=$(curl -s -X POST https://imss-pension-api.onrender.com/admin/invitations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"email\": \"$EMAIL\", \"plan\": \"$PLAN\", \"cuota_analisis\": $CUOTA, \"notes\": \"$NOMBRE\"}")

INV_TOKEN=$(echo $RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$INV_TOKEN" ]; then
    echo "❌ Error al crear invitación"
    exit 1
fi

echo "✅ ¡Invitación creada!"
echo ""
echo "🔗 Link de registro:"
echo "https://pensionasoft.com/invite?token=$INV_TOKEN"
echo ""
echo "📧 Email enviado automáticamente a $EMAIL"
