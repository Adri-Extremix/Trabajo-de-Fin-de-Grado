# Trabajo-de-Fin-de-Grado

Este proyecto corresponde a mi Trabajo de Fin de Grado para la Universidad Carlos III de Madrid, desarrollado para facilitar la enseñanza y el aprendizaje de la programación concurrente.

La herramienta permite ejecutar y depurar código C con múltiples hilos, visualizando en tiempo real el comportamiento de los mismos, lo que facilita el entendimiento de conceptos complejos relacionados con la concurrencia.

Para más información consulte la [Memoria del TFG](doc/build/report.pdf)

## Arquitectura

El proyecto implementa una arquitectura distribuida con los siguientes componentes:

- **Frontend**: Aplicación web desarrollada con HTML, CSS y JavaScript
- **Backend/Proxy**: Servidor Python que gestiona la comunicación y redirección
- **Contenedores Docker**: Entornos aislados que ejecutan el código del usuario con depuradores GDB/RR

## Prerequisitos


Para ejecutar este proyecto necesitas:

- [Docker](https://www.docker.com/get-started) (y Docker Compose)
- [Node.js](https://nodejs.org/) (versión 14 o superior)

## Instalación y ejecución

1. Clona el repositorio:

    ```sh
    git clone https://github.com/Adri-Extremix/Trabajo-de-Fin-de-Grado
    ```

2. Prepara el script de inicio:

    ```sh
    cd Trabajo-de-Fin-de-Grado
    chmod +x start_proyect.sh
    chmod +x close_proyect.sh
    ```

3. Inicia la aplicación:

    ```sh
    ./start_proyect.sh
    ```

4. Al terminar la ejecución, el navegador se abrirá automáticamente mostrando la interfaz de la aplicación (o visita `http://<IP_LOCAL>:8080`).

5. Para detener todos los servicios cuando termines:

    ```sh
    ./close_proyect.sh
    ```
    
## Uso

1. Escribe tu código C en el editor de la interfaz web.
2. Añade los puntos de interrupción (breakpoints) donde desees.
3. Compila el código y asegurate de que no haya errores de compilación.

A partir de aquí, puedes ejecutar el código directamente o desplazarte a la sección de depuración para iniciar una sesión de depuración interactiva.
4. Cambia a la sección de depuración
5. Comienza la depuración con el botón de "*Run*"
6. Utiliza los controles de depuración para avanzar paso a paso, observar variables y el estado de los hilos.
7. Puedes detener la depuración en cualquier momento y volver a la edición del código.

> [!IMPORTANT] Cada vez que realices cambios en el código o en los puntos de interrupción, debes recompilar el código para que los cambios surtan efecto.

## Estructura del Proyecto

```
├── src/                     # Código fuente principal
│   ├── frontend/            # Interfaz web (HTML/CSS/JS)
│   ├── proxy/               # Servidor proxy (Python)
│   └── docker/              # Entornos de depuración (Docker)
├── examples/                # Ejemplos de programas C para probar
├── test/                    # Pruebas unitarias y funcionales
├── doc/                     # Documentación y memoria del proyecto
├── start_proyect.sh         # Script para iniciar todos los servicios
└── close_proyect.sh         # Script para detener todos los servicios
```

## Características principales

- **Ejecución de código C**: Compila y ejecuta programas C con múltiples hilos
- **Depuración interactiva**: Utiliza comandos de depuración como step-in, step-over, y breakpoints
- **Visualización en tiempo real**: Observa el estado y la evolución de los hilos durante la ejecución
- **Entorno seguro**: El código se ejecuta en contenedores Docker aislados
- **Arquitectura escalable**: Múltiples contenedores Docker pueden servir a diferentes usuarios
- **Comunicación WebSockets**: Actualización en tiempo real del estado de la depuración

## Tecnologías utilizadas

- Frontend: HTML5, CSS3, JavaScript
- Backend: Python, WebSockets
- Contenedores: Docker, Docker Compose
- Depuración: GDB, RR (Record and Replay)
