#!/bin/bash

# Script para ejecutar tests del TFG
set -e

echo "🧪 Script de ejecución de tests del TFG"
echo "======================================"

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [opción]"
    echo ""
    echo "Opciones:"
    echo "  all        Ejecutar todos los tests (unitarios + funcionales)"
    echo "  unit       Ejecutar solo tests unitarios"
    echo "  functional Ejecutar solo tests funcionales"
    echo "  interactive Iniciar contenedor interactivo para tests manuales"
    echo "  clean      Limpiar contenedores e imágenes de test"
    echo "  help       Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 all         # Ejecutar todos los tests"
    echo "  $0 unit        # Solo tests unitarios"
    echo "  $0 interactive # Modo interactivo"
}

# Función para limpiar contenedores
clean_containers() {
    echo "🧹 Limpiando contenedores y volúmenes de test..."
    docker compose -f docker-compose.test.yml down --volumes --remove-orphans
    docker image prune -f
    echo "✅ Limpieza completada"
}

# Función para ejecutar todos los tests
run_all_tests() {
    echo "🚀 Ejecutando todos los tests..."
    docker compose -f docker-compose.test.yml up --build test-runner
}

# Función para ejecutar tests unitarios
run_unit_tests() {
    echo "🔬 Ejecutando tests unitarios..."
    docker compose -f docker-compose.test.yml run --rm test-runner bash -c "
        source /venv/bin/activate
        cd /app/test
        python -m unittest test_debugger.py -v
    "
}

# Función para ejecutar tests funcionales
run_functional_tests() {
    echo "⚙️ Ejecutando tests funcionales..."
    docker compose -f docker-compose.test.yml run --rm test-runner bash -c "
        source /venv/bin/activate
        cd /app/test
        python functional_test_debugger.py
    "
}

# Función para modo interactivo
run_interactive() {
    echo "🖥️ Iniciando contenedor interactivo..."
    echo "Puedes ejecutar tests manualmente con:"
    echo "  cd /app/test"
    echo "  source /venv/bin/activate"
    echo "  python -m unittest test_debugger.py -v"
    echo "  python functional_test_debugger.py"
    echo ""
    docker compose -f docker-compose.test.yml --profile interactive up -d test-interactive
    docker exec -it tfg-test-interactive bash
}

# Procesar argumentos
case "${1:-all}" in
    "all")
        run_all_tests
        ;;
    "unit")
        run_unit_tests
        ;;
    "functional")
        run_functional_tests
        ;;
    "interactive")
        run_interactive
        ;;
    "clean")
        clean_containers
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Opción no válida: $1"
        echo ""
        show_help
        exit 1
        ;;
esac