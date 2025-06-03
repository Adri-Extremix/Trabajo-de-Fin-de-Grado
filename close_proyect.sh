#!/bin/bash
# filepath: /home/adrian/Documents/Trabajo-de-Fin-de-Grado/stop_project.sh

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

echo -e "${YELLOW}Deteniendo el proyecto...${NC}"

# Verificar si hay contenedores en ejecución
RUNNING_CONTAINERS=$(docker ps --format "{{.Names}}" | grep -E 'debugger|proxy')

if [ -z "$RUNNING_CONTAINERS" ]; then
    echo -e "${BLUE}No hay contenedores en ejecución relacionados con el proyecto.${NC}"
    exit 0
fi

# Detener contenedores de debugger
cd ./src/docker
if [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}Deteniendo contenedores de debugger...${NC}"
    docker compose down
    echo -e "${GREEN}✅ Contenedores de debugger detenidos.${NC}"
else
    echo -e "${YELLOW}No se encontró el archivo docker-compose.yml para debugger.${NC}"
    # Intentar detener manualmente los contenedores
    docker stop $(docker ps --filter name=debugger -q) 2>/dev/null
fi

# Detener proxy
cd ../proxy
if [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}Deteniendo el proxy...${NC}"
    docker compose down
    echo -e "${GREEN}✅ Proxy detenido.${NC}"
else
    echo -e "${YELLOW}No se encontró el archivo docker-compose.yml para proxy.${NC}"
    # Intentar detener manualmente el proxy
    docker stop $(docker ps --filter name=proxy -q) 2>/dev/null
fi

# Verificar que todos los contenedores se hayan detenido
STILL_RUNNING=$(docker ps --format "{{.Names}}" | grep -E 'debugger|proxy')
if [ -n "$STILL_RUNNING" ]; then
    echo -e "${RED}Algunos contenedores siguen en ejecución:${NC}"
    echo -e "${RED}${STILL_RUNNING}${NC}"
    echo -e "${YELLOW}Intentando forzar la detención...${NC}"
    docker stop $(docker ps --filter name=debugger -q) 2>/dev/null
    docker stop $(docker ps --filter name=proxy -q) 2>/dev/null
fi

echo -e "${GREEN}Eliminando la red Docker...${NC}"
docker network rm debugger_network 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Red Docker eliminada.${NC}"
else
    echo -e "${YELLOW}No se pudo eliminar la red. Podría estar en uso por otros contenedores.${NC}"
fi

echo -e "${GREEN}¡Proyecto detenido correctamente!${NC}"