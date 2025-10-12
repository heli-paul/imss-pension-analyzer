#!/bin/bash
echo "=== DIAGNÓSTICO MÓDULO 3 ==="
echo ""

# Verificar estructura
echo "📁 ESTRUCTURA DE ARCHIVOS:"
find modules/modulo3 -name "*.py" | sort

echo ""
echo "📄 ARCHIVOS VACÍOS (requieren código):"

# Función para verificar archivos vacíos
check_file() {
    local file=$1
    if [ -f "$file" ]; then
        local size=$(wc -l < "$file")
        local has_class=$(grep -c "^class\|^def " "$file" 2>/dev/null || echo 0)
        if [ $size -lt 5 ] || [ $has_class -eq 0 ]; then
            echo "❌ $file (${size} líneas, ${has_class} clases/funciones)"
        else
            echo "✅ $file (${size} líneas, ${has_class} clases/funciones)"
        fi
    else
        echo "❌ $file (NO EXISTE)"
    fi
}

# Verificar cada archivo crítico
files=(
    "modules/modulo3/pension_processor.py"
    "modules/modulo3/core/quality_validator.py" 
    "modules/modulo3/core/overlap_resolver.py"
    "modules/modulo3/calculators/promedio_250.py"
    "modules/modulo3/calculators/conservacion_derechos.py"
    "modules/modulo3/validators/cross_validator.py"
    "modules/modulo3/validators/final_quality.py"
    "modules/modulo3/utils/uma_topes.py"
)

for file in "${files[@]}"; do
    check_file "$file"
done
