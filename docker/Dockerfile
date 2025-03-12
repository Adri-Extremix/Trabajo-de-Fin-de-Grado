# Dockerfile para RR (Record and Replay) en Ubuntu
FROM ubuntu:latest

# Configuración inicial
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependencias principales
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y \
        git \
        cmake \
        gcc \
        g++ \
        gdb \
        pkg-config \
        capnproto \
        libcapnp-dev \
        zlib1g-dev \
        libzstd-dev \
        ninja-build \
        gcc-multilib \
        g++-multilib \
        libc6-dev-i386 \
        libc6-dev:i386 \  
        python3-pexpect \
        sudo \
        curl \
        rr \
    && rm -rf /var/lib/apt/lists/*

# Configura parámetros del kernel (se necesitan permisos --privileged al ejecutar el contenedor)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN ./entrypoint.sh
CMD ["bash"]  # Shell interactiva como proceso principal
# Directorio de trabajo
WORKDIR /app