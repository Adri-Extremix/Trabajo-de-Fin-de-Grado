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
    gdb \
    rr \
    iputils-ping \
    dnsutils \
    net-tools \
    curl \
    pypy3 \
    pypy3-dev \
    pypy3-venv \
    && apt-get clean \ 
    && rm -rf /var/lib/apt/lists/*

# Cambiar al directorio de la aplicación
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Copiar archivos necesarios
COPY docker/compiler.py docker/debugger.py docker/watchpoint.py docker/requirements.txt docker/webSocket.py ./
COPY ../frontend/dist ./frontend/dist

# Crear entorno virtual con PyPy directamente (sin instalar pip globalmente)
RUN pypy3 -m venv pypy_venv && \
    ./pypy_venv/bin/pip install --upgrade pip && \
    ./pypy_venv/bin/pip install -r requirements.txt

# Exponer el puerto 5000 para la comunicación
EXPOSE 5000

# Comando por defecto al iniciar el contenedor usando el venv de PyPy
CMD ["./pypy_venv/bin/pypy3", "webSocket.py"]