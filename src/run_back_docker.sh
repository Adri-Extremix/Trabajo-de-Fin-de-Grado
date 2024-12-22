#!/bin/bash

# Construye la imagen Docker
docker build -t backend-image .

# Ejecuta el contenedor en segundo plano
CONTAINER_ID=$(docker run -d -p 8080:8080 --cpus="4" --memory=1g --memory-swap=2g backend-image)

# Función para detener el contenedor al recibir SIGINT
cleanup() {
    echo "Deteniendo contenedor..."
    docker stop $CONTAINER_ID
}

# Atrapa SIGINT y ejecuta la función cleanup
trap cleanup SIGINT

# Espera hasta que el contenedor se detenga
docker logs -f $CONTAINER_ID
