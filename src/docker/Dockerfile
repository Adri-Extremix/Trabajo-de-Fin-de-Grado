# Dockerfile para RR (Record and Replay) en Ubuntu
FROM ubuntu:latest

# Configuración inicial
ENV DEBIAN_FRONTEND=noninteractive


# Actualizar e instalar dependencias básicas
RUN apt-get update && apt-get install -y \
    git \
    wget \
    apt-utils \
    build-essential \
    python3.12 \
    python3.12-dev \
    python3-pip \
    python3-venv \
    python3.12-venv \
    python3-full \
    pkg-config \
    zlib1g-dev \
    libcapstone-dev \
    libdw-dev \
    rr \
    iputils-ping \
    dnsutils \
    net-tools \
    curl \
    && apt-get clean \ 
    && rm -rf /var/lib/apt/lists/*

# Cambiar al directorio de la aplicación
WORKDIR /app

# Copiar archivos necesarios
COPY compiler.py debugger.py requirements.txt webSocket.py ./

# Configurar Python e instalar dependencias en un entorno virtual
RUN python3.12 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Exponer el puerto 5000 para la comunicación
EXPOSE 5000

# Comando por defecto al iniciar el contenedor
CMD ["/app/venv/bin/python3", "webSocket.py"]