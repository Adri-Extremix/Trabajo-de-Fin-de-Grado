#!/bin/bash

# Verificar si tmux está instalado
if ! command -v tmux &> /dev/null; then
    echo "tmux no está instalado. Instalando..."
    # sudo apt-get update && sudo apt-get install -y tmux
    exit
fi

# Nombre de la sesión
SESSION="desarrollo"

    # Crear una nueva sesión
    tmux new-session -d -s $SESSION

    # Dividir la ventana verticalmente
    tmux split-window -h -t $SESSION:0

    # Ejecutar npm start en el panel izquierdo
    tmux send-keys -t $SESSION:0.0 "cd /home/afern193/Trabajo-de-Fin-de-Grado/src/front && npm start" C-m

    # Ejecutar python3 en el panel derecho
    tmux send-keys -t $SESSION:0.1 "cd /home/afern193/Trabajo-de-Fin-de-Grado/src/back && source venv/bin/activate && python3 backend.py" C-m

# Conectar a la sesión
tmux attach -t $SESSION
