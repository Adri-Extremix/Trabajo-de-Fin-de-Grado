#!/bin/bash
# filepath: /home/adrian/Documents/Trabajo-de-Fin-de-Grado/start_proyect.sh

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # Sin Color

echo -e "${GREEN}Iniciando el proyecto...${NC}"

# Obtener la IP local de forma compatible con macOS y Linux
get_ip() {
    # Intenta primero con macOS
    if command -v ipconfig &> /dev/null; then
        IP_LOCAL=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
    fi

    # Si no se encontró la IP en macOS, intenta con Linux
    if [ -z "$IP_LOCAL" ] && command -v hostname &> /dev/null; then
        IP_LOCAL=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi

    # Si aún no hay IP, intenta con ifconfig (presente en ambos sistemas)
    if [ -z "$IP_LOCAL" ] && command -v ifconfig &> /dev/null; then
        IP_LOCAL=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n 1)
    fi

    # Si todo lo demás falla
    if [ -z "$IP_LOCAL" ]; then
        IP_LOCAL="localhost"
    fi

    echo "$IP_LOCAL"
}

# Llamar a la función y asignar el resultado
IP_LOCAL=$(get_ip)

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

# Ejecutando el lado del cliente
cd src/frontend  
npm install
npm run build
# npm run start
echo -e "${GREEN}Cliente iniciado correctamente.${NC}"


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

# Start the proxy
cd ../proxy
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

for i in {1..12}; do
    echo -n "."
    sleep 0.5
done

# Abrir el navegador predeterminado con la URL del proxy
echo -e "${YELLOW}Abriendo navegador en la URL del proxy...${NC}"

# URL del proxy
PROXY_URL="http://${PROXY_IP}:${PROXY_PORT}"

# Detectar el sistema operativo y abrir el navegador
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$PROXY_URL"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - intentar los comandos más comunes
    xdg-open "$PROXY_URL" 2>/dev/null 
    echo -e "${RED}No se pudo abrir el navegador automáticamente. Por favor, visita $PROXY_URL manualmente.${NC}"
else
    echo -e "${RED}Sistema operativo no reconocido. Por favor, visita $PROXY_URL manualmente.${NC}"
fi

echo -e "${GREEN}¡Listo para trabajar!${NC}"
