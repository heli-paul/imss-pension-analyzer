#!/bin/bash
echo "🚀 Iniciando Sistema IMSS..."

cd ~/imss-pension-analyzer

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Entorno virtual activado"
else
    echo "⚠️ Entorno virtual no encontrado. Creando..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r config/requirements.txt
fi

# Matar procesos previos
pkill -f "uvicorn.*8001" 2>/dev/null
pkill -f "uvicorn.*8000" 2>/dev/null

# Parser (puerto 8001)
if [ -f "src/parser/main.py" ]; then
    echo "Iniciando parser..."
    cd src/parser
    python -m uvicorn main:app --port 8001 --reload &
    cd ../..
fi

# Backend (puerto 8000)  
if [ -f "src/backend/main.py" ]; then
    echo "Iniciando backend..."
    cd src/backend
    export PARSER_URL="http://localhost:8001/parse"
    export SHEETS_CREDS_PATH="/home/heli_paul/secrets/gsa-imss.json"
    export GDRIVE_SHEET_ID="1GjEPZ1L-N0RXLxQYDXJXaMjamuu8cn7Uz2uFXdoX_dk"
    python -m uvicorn main:app --port 8000 --reload &
    cd ../..
fi

echo ""
echo "✅ Servicios iniciados"
echo "Parser: http://localhost:8001"
echo "Backend: http://localhost:8000"
echo ""
echo "Para probar:"
echo "curl http://localhost:8001/health"
echo "curl http://localhost:8000/health"
