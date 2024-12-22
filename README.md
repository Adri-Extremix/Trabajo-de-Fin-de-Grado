# Trabajo-de-Fin-de-Grado

Este es mi trabajo de fin de grado de la Universidad Carlos III de Madrid, actualmente en desarrollo.

Este proyecto busca ser una herramienta didáctica que facilite la programación paralela. Permite ejecutar código paralelo y observar en tiempo real el comportamiento de los hilos.

El proyecto consta de un **frontend** desarrollado en **React** y un **backend** en **Golang**.

## Prerequisitos

Para ejecutar este proyecto, asegúrate de tener instalados los siguientes programas:

-   [Docker](https://docs.docker.com/desktop/setup/install/linux/)
-   [Node.js](https://nodejs.org/es/download/package-manager)

## Ejecución

Para ejecutar el proyecto, sigue estos pasos:

1. Clona el repositorio:

    ```sh
    git clone https://github.com/Adri-Extremix/Trabajo-de-Fin-de-Grado
    ```

2. Cambia al directorio del proyecto y asegúrate de que el script `start_proyect.sh` tenga permisos de ejecución:

    ```sh
    cd Trabajo-de-Fin-de-Grado
    chmod +x start_proyect.sh
    ```

3. Ejecuta el script para iniciar tanto el frontend como el backend:

    ```sh
    ./start_proyect.sh
    ```

4. Después de ejecutar el script, se abrirá automáticamente una ventana del navegador donde podrás interactuar con la herramienta. El frontend estará accesible en `http://localhost:3000` por defecto.

## Estructura del Proyecto

-   **Frontend**: React (gestionado por npm).
-   **Backend**: Golang (backend REST API).
-   **Docker**: Usado para la ejecución del backend en un entorno aislado.

## Funcionalidades

Este proyecto permite:

-   Escribir y ejecutar código paralelo en C.
-   Observar el comportamiento de los hilos en tiempo real.
-   Depurar y analizar las ejecuciones concurrentes.
