#!/bin/bash

# Función para detener ambos procesos
cleanup() {
    echo ""
    echo "Deteniendo backend y frontend..."
    docker stop $CONTAINER_ID > /dev/null
    docker wait $CONTAINER_ID > /dev/null
    echo ""
    echo "Contenedor Docker detenido."
}

# Atrapar SIGINT (Ctrl + C) para ejecutar la limpieza
trap cleanup SIGINT

cd ./src

# Inicia el backend en segundo plano
echo "Iniciando backend..."
docker build -t backend-image .
CONTAINER_ID=$(docker run -d -p 8080:8080 --cpus="4" --memory=1g --memory-swap=2g backend-image &)

docker logs -f $CONTAINER_ID &

# Inicia el frontend en segundo plano
echo "Iniciando frontend..."
cd ./front
nohup npm start > /dev/null 2>&1 &
FRONTEND_PID=$!

# Espera a que los procesos terminen
wait $FRONTEND_PID