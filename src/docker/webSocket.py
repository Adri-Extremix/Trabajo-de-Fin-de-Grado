from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
from debugger import Debugger  # Importa el Debugger
from compiler import Compiler
import threading
import time
import uuid
import requests
import os
import logging

# Configurar logging para silenciar Werkzeug
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class WebSocketContainer:
    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        self.debugger = None
        self.compiler = Compiler()
        
        # Configuración de identificación y comunicación
        self.docker_id = str(uuid.uuid4())
        self.proxy_url = os.environ.get('PROXY_URL', 'http://proxy:8080')
        
        # Configurar eventos de socketio
        self.setup_socketio_events()

        self.setup_routes()
        
        # Iniciar el hilo de latidos
        print(f"Iniciando contenedor {self.docker_id} con proxy en {self.proxy_url}")
        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
        self.heartbeat_thread.start()

    
    def setup_routes(self):
            self.app.add_url_rule("/", "serve_index", self.serve_index)
            self.app.add_url_rule("/<path:filename>", "serve_static", self.serve_static)

    def serve_index(self):
        return send_from_directory("frontend/dist", "index.html")

    def serve_static(self, filename):
        # static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
        return send_from_directory("frontend/dist", filename)
    def send_heartbeat(self):
        # Esperar a que el servidor esté completamente iniciado
        time.sleep(5)
        
        while True:
            try:
                # Obtener información de puertos del entorno
                service_host = os.environ.get('HOST', '0.0.0.0')
                service_port = os.environ.get('PORT', '5000')
                
                # Determinar automáticamente el puerto externo basado en el puerto interno
                internal_to_external = {
                    '5000': '5001',  # debugger1
                    '5000': '5002',  # debugger2
                    '5000': '5003'   # debugger3
                }
                
                # Basado en el hostname del contenedor
                container_name = os.environ.get('HOST')
                external_port = None
                if container_name == 'debugger1':
                    external_port = '5001'
                elif container_name == 'debugger2':
                    external_port = '5002'
                elif container_name == 'debugger3':
                    external_port = '5003'
                else:
                    external_port = internal_to_external.get(service_port, service_port)
                
                # Obtener la IP del proxy desde la URL del proxy
                proxy_host = self.proxy_url.split('://')[1].split(':')[0]
                if proxy_host == 'proxy':
                    # Si es el nombre del servicio, asumimos localhost para acceso externo
                    external_host = 'localhost'
                else:
                    # Si ya es una IP, la usamos como está
                    external_host = proxy_host
                
                # URL para redirección externa
                external_url = f"http://{external_host}:{external_port}"
                
                # Enviar latido al proxy con reintentos
                max_retries = 3
                retry_delay = 2
                success = False
                
                for attempt in range(max_retries):
                    try:
                        response = requests.post(
                            f"{self.proxy_url}/heartbeat",
                            json={
                                "docker_id": self.docker_id,
                                "url": external_url
                            },
                            timeout=5  # Timeout para evitar bloqueos
                        )
                        # Añade esta línea para marcar el éxito
                        success = True
                        break  # Salir del bucle de reintentos si tiene éxito
                    except Exception as retry_error:
                        print(f"Error en intento {attempt+1}: {str(retry_error)}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                
                if not success:
                    print(f"Error: No se pudo enviar el latido después de {max_retries} intentos")
                
            except Exception as e:
                print(f"Error: Error general en heartbeat: {str(e)}")
            
            # Esperar antes del próximo latido
            time.sleep(20)  # Enviar latido cada 20 segundos

    def setup_socketio_events(self):

        @self.socketio.on("connect")
        def handle_connect():
            print("Cliente conectado")
            emit('message', {'data': 'Conexión establecida'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Cliente desconectado')
            emit('message', {'data': 'Desconexión establecida'})    
                
        @self.socketio.on('compile')
        def handle_compile(data): 
            try:
                result = self.compiler.compile_code(data["code"])
                if self.compiler.compiled_file_path:
                    # Obtener el modo de depuración del objeto data
                    debug_mode = data.get("debugMode", "gdb")
                    # Configurar el depurador con el modo seleccionado
                    # Usar RR si el debug_mode es "rr", de lo contrario usar GDB estándar
                    if debug_mode == "rr":
                        use_rr = True
                    else:
                        use_rr = False

                    self.debugger = Debugger(self.compiler.code_file_path, self.compiler.compiled_file_path, rr=use_rr)
                    
                    breakpoints = data.get("breakpoints", [])
                    for breakpoint in breakpoints:
                        self.debugger.set_breakpoint(breakpoint)
                    emit('compile_response', {'action': 'compile', 'result': result})
            except Exception as e:
                print(f"Error: {str(e)}")
            #TODO: Acordarse de que el error de compilación debe de aparecer como un error en la consola del cliente
                emit('compile_response', {'action': 'compile', 'error': str(e)})
                return

        @self.socketio.on('run')
        def handle_run():
            try:
                result = self.compiler.run_code()
                print(f"Resultado de la ejecución: {result}")
                emit('run_response', {'action': 'run', 'result': result})
            except Exception as e:

                #TODO: Acordarse de que el error de ejecución debe de aparecer como un error en la consola del cliente
                emit('run_response', {'action': 'run', 'error': str(e)})
                
                return
            

        @self.socketio.on('run_debug')
        def handle_run_debug():
            if self.debugger is None:
                emit('debug_response', {'action': 'run_debug', 'error': 'Debugger not initialized'})
                return
            result = self.debugger.run()
            emit('debug_response', {'action': 'run_debug', 'result': result})

        @self.socketio.on('continue_debug')
        def handle_continue_debug():
            if self.debugger is None:
                emit('debug_response', {'action': 'continue', 'error': 'Debugger not initialized'})
                return
            result = self.debugger.continue_execution()
            emit('debug_response', {'action': 'continue', 'result': result})

        @self.socketio.on('reverse_debug')
        def handle_reverse_debug():
            if self.debugger is None:
                emit('debug_response', {'action': 'reverse_continue', 'error': 'Debugger not initialized'})
                return
            result = self.debugger.reverse_continue()
            emit('debug_response', {'action': 'reverse_continue', 'result': result})

        @self.socketio.on('step_over')
        def handle_step_over(data):
            thread_id = data.get('thread_id', None)
            if self.debugger is None:
                emit('debug_response', {'action': 'step_over', 'error': 'Debugger not initialized'})
                return
            result = self.debugger.step_over(thread_id)
            emit('debug_response', {'action': 'step_over', 'result': result})

        @self.socketio.on('reverse_step_over')
        def handle_reverse_step_over(data):
            thread_id = data.get('thread_id', None)
            if self.debugger is None:
                emit('debug_response', {'action': 'reverse_step_over', 'error': 'Debugger not initialized'})
                return
            result = self.debugger.reverse_step_over()
            emit('debug_response', {'action': 'reverse_step_over', 'result': result})

        @self.socketio.on('step_into')
        def handle_step_into(data):
            thread_id = data.get('thread_id', None)
            if self.debugger is None:
                emit('debug_response', {'action': 'step_into', 'error': 'Debugger not initialized'})
                return
            result = self.debugger.step_into(thread_id)
            emit('debug_response', {'action': 'step_into', 'result': result})

        @self.socketio.on('reverse_step_into')
        def handle_reverse_step_into(data):
            thread_id = data.get('thread_id', None)
            if self.debugger is None:
                emit('debug_response', {'action': 'reverse_step_into', 'error': 'Debugger not initialized'})
                return
            result = self.debugger.reverse_step_into()
            emit('debug_response', {'action': 'reverse_step_into', 'result': result})

        @self.socketio.on('step_out')
        def handle_step_out(data):
            thread_id = data.get('thread_id', None)
            if self.debugger is None:
                emit('debug_response', {'action': 'step_out', 'error': 'Debugger not initialized'})
                return
            result = self.debugger.step_out(thread_id)
            emit('debug_response', {'action': 'step_out', 'result': result})

        @self.socketio.on('reverse_step_out')
        def handle_reverse_step_out(data):
            thread_id = data.get('thread_id', None)
            if self.debugger is None:
                emit('debug_response', {'action': 'reverse_step_out', 'error': 'Debugger not initialized'})
                return
            result = self.debugger.reverse_step_out()
            emit('debug_response', {'action': 'reverse_step_out', 'result': result})

    def run(self):
        port = int(os.environ.get('PORT', 5000))
        self.socketio.run(self.app, host="0.0.0.0", port=port)

if __name__ == '__main__':
    web_socket_container = WebSocketContainer()
    web_socket_container.run()
