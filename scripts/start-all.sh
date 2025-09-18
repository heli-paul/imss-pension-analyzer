#!/bin/bash
echo "🚀 Iniciando Sistema IMSS..."

cd ~/imss-pension-analyzer

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
    python -m uvicorn main:app --port 8000 --reload &
    cd ../..
fi

echo "✅ Servicios iniciados"
echo "Parser: http://localhost:8001"
echo "Backend: http://localhost:8000"
