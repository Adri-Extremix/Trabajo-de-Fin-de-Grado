from flask import Flask, request, jsonify, redirect, make_response
import time
import threading
import logging
import os
import uuid

# Silenciar logs de Werkzeug
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Solo muestra errores, no requests

# Configuración de logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
numeric_level = getattr(logging, log_level.upper(), None)
if not isinstance(numeric_level, int):
    numeric_level = logging.INFO

logging.basicConfig(level=numeric_level, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('proxy')

class DockerManager:
    def __init__(self, heartbeat_timeout=None):
        self.app = Flask(__name__)
        self.available_dockers = {}  # {docker_id: {url, last_heartbeat}}
        self.client_mappings = {}    # {client_id: docker_id}
        
        # Obtener valor del timeout de variables de entorno o usar valor predeterminado
        self.heartbeat_timeout = heartbeat_timeout or int(os.environ.get('HEARTBEAT_TIMEOUT', 30))
        logger.info(f"Configurado timeout de heartbeat: {self.heartbeat_timeout} segundos")
        
        self.lock = threading.Lock()
        
        # Iniciar el hilo para limpiar contenedores inactivos
        self.cleanup_thread = threading.Thread(target=self._cleanup_inactive_dockers, daemon=True)
        self.cleanup_thread.start()
        
        # Configurar rutas de Flask
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura las rutas de Flask dentro del DockerManager"""
        
        @self.app.route('/heartbeat', methods=['POST'])
        def heartbeat():
            # Este está bien, sin cambios
            data = request.get_json()
            if not data or 'docker_id' not in data or 'url' not in data:
                return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
            self.register_heartbeat(data['docker_id'], data['url'])
            return jsonify({'success': True})

        @self.app.route('/')
        def connect_client():
            # Obtener o generar client_id desde cookie
            client_id = request.cookies.get('client_id')
            if not client_id:
                client_id = str(uuid.uuid4())
            # Asignar Docker al cliente
            docker_url = self.get_available_docker(client_id)
            if not docker_url:
                return jsonify({'success': False, 'error': 'No Docker available'}), 503
            # Redirigir y establecer cookie para futuras peticiones
            resp = make_response(redirect(docker_url))
            resp.set_cookie('client_id', client_id, max_age=300)
            return resp

        @self.app.route('/disconnect')
        def disconnect_client():
            # Obtener client_id desde la cookie
            client_id = request.cookies.get('client_id')
            if not client_id:
                return jsonify({'success': False, 'error': 'Missing client_id cookie'}), 400

            # Liberar Docker asignado
            success = self.release_docker(client_id)
            # Eliminar cookie para cerrar la sesión
            resp = make_response(jsonify({'success': success}))
            resp.set_cookie('client_id', '', expires=0)
            return resp

        @self.app.route('/status')
        def status():
            return jsonify(self.get_status())
    
    def run(self, host=None, port=None):
        """Inicia el servidor Flask utilizando variables de entorno"""
        host = host or os.environ.get('HOST', '0.0.0.0')
        port = port or int(os.environ.get('PORT', 8080))
        logger.info(f"Iniciando servidor en {host}:{port}")
        self.app.run(host=host, port=port)
    
    def register_heartbeat(self, docker_id, docker_url):
        """Registra un latido de un contenedor Docker"""
        with self.lock:
            self.available_dockers[docker_id] = {
                'url': docker_url,
                'last_heartbeat': time.time()
            }
        logger.info(f"Registrado latido de Docker {docker_id} en {docker_url}")
        return True
    
    def get_available_docker(self, client_id):
        """Obtiene un Docker disponible y lo asigna al cliente"""
        with self.lock:
            # Si el cliente ya tiene un Docker asignado, retornar ese
            if (client_id in self.client_mappings):
                docker_id = self.client_mappings[client_id]
                if docker_id in self.available_dockers:
                    return self.available_dockers[docker_id]['url']
            
            # Buscar un Docker disponible (no asignado a ningún cliente)
            available_ids = [docker_id for docker_id in self.available_dockers.keys() 
                             if docker_id not in self.client_mappings.values()]
            
            if not available_ids:
                return None
            
            # Asignar el primer Docker disponible
            assigned_docker_id = available_ids[0]
            self.client_mappings[client_id] = assigned_docker_id
            
            return self.available_dockers[assigned_docker_id]['url']
    
    def release_docker(self, client_id):
        """Libera el Docker asignado a un cliente"""
        with self.lock:
            if client_id in self.client_mappings:
                docker_id = self.client_mappings[client_id]
                del self.client_mappings[client_id]
                logger.info(f"Docker {docker_id} liberado por el cliente {client_id}")
                return True
        return False
    
    def _cleanup_inactive_dockers(self):
        """Elimina los Docker que no han enviado latidos en un tiempo determinado"""
        while True:
            time.sleep(10)  # Verificar cada 10 segundos
            current_time = time.time()
            with self.lock:
                inactive_dockers = []
                for docker_id, info in self.available_dockers.items():
                    if current_time - info['last_heartbeat'] > self.heartbeat_timeout:
                        inactive_dockers.append(docker_id)
                
                # Eliminar Docker inactivos
                for docker_id in inactive_dockers:
                    del self.available_dockers[docker_id]
                    logger.warning(f"Docker {docker_id} eliminado por inactividad")
                
                # Eliminar asignaciones a Docker inactivos
                for client_id, docker_id in list(self.client_mappings.items()):
                    if docker_id not in self.available_dockers:
                        del self.client_mappings[client_id]
                        logger.warning(f"Asignación del cliente {client_id} eliminada porque Docker {docker_id} está inactivo")
    
    def get_status(self):
        """Retorna el estado actual del gestor de Docker"""
        with self.lock:
            return {
                'available_dockers': len(self.available_dockers),
                'active_clients': len(self.client_mappings),
                'docker_list': list(self.available_dockers.keys()),
                'mappings': self.client_mappings
            }


if __name__ == '__main__':
    # Crear instancia del gestor de Docker y ejecutar el servidor
    docker_manager = DockerManager()
    docker_manager.run()
