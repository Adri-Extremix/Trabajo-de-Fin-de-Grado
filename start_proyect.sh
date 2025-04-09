#!/bin/bash
# filepath: /home/adrian/Documents/Trabajo-de-Fin-de-Grado/start_proyect.sh

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

echo -e "${GREEN}Iniciando el proyecto...${NC}"

# Get local IP address for proxy connection
IP_LOCAL=$(hostname -I | awk '{print $1}')
if [ -z "$IP_LOCAL" ]; then
    IP_LOCAL="localhost"
    echo -e "${YELLOW}No se pudo determinar la IP local, usando localhost${NC}"
else
    echo -e "${GREEN}IP local detectada: ${IP_LOCAL}${NC}"
fi

# Export for Docker Compose to use in PROXY_IP variable
export PROXY_IP=$IP_LOCAL
export PROXY_PORT=8080
export DOCKERS_IP=$IP_LOCAL

echo -e "${BLUE}Dirección IP del proxy:${NC} ${IP_LOCAL}"

# Asegurar que la red Docker exista
if ! docker network inspect debugger_network &>/dev/null; then
    echo -e "${YELLOW}Creando red Docker 'debugger_network'...${NC}"
    docker network create debugger_network
else
    echo -e "${GREEN}Red 'debugger_network' ya existe${NC}"
fi

# Start the proxy
cd ./src/proxy
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml no encontrado en el directorio del proxy.${NC}"
    exit 1
fi
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile no encontrado en el directorio del proxy.${NC}"
    exit 1
fi

echo -e "${GREEN}Iniciando proxy...${NC}"
docker compose up -d --build
echo -e "${GREEN}Proxy iniciado correctamente.${NC}"
echo -e "- Proxy disponible en: ${BLUE}http://${PROXY_IP}:${PROXY_PORT}${NC}"

# Start Docker containers
cd ../docker

if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml no encontrado en el directorio de los debuggers.${NC}"
    exit 1
fi
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}Error: Dockerfile no encontrado en el directorio de los debuggers.${NC}"
    exit 1
fi

echo -e "${GREEN}Iniciando contenedores de Docker...${NC}"
docker compose up -d --build

echo -e "${GREEN}Servicios iniciados correctamente.${NC}"
echo -e "- Debugger1 disponible en: ${BLUE}http://${DOCKERS_IP}:5001${NC}"
echo -e "- Debugger2 disponible en: ${BLUE}http://${DOCKERS_IP}:5002${NC}"
echo -e "- Debugger3 disponible en: ${BLUE}http://${DOCKERS_IP}:5003${NC}"

echo -e "${YELLOW}Verificando estado del sistema...${NC}"
echo -e "Para ver los logs de los contenedores ejecuta: docker logs <container_name>"
echo -e "Para detener todos los servicios ejecuta: docker-compose down en cada directorio"
echo -e "${GREEN}¡Todo listo! Sistema iniciado correctamente${NC}"