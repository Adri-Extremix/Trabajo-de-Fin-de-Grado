FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    gdb \
    gcc \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m venv /venv \
    && . /venv/bin/activate \
    && pip install --upgrade pip

# Instalar dependencias de Python
RUN /venv/bin/pip install pygdbmi==0.10.0.1

# Copiar toda la estructura necesaria
COPY src/ ./src/
COPY examples/ ./examples/

# Compilar los ejemplos
WORKDIR /app/examples
RUN gcc -g -pthread -o prueba1 prueba1.c

# Volver al directorio principal
WORKDIR /app/src/docker
CMD ["/venv/bin/python", "debugger.py"]