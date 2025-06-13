from concurrent.futures import thread
from doctest import debug
import pygdbmi.constants
from pygdbmi.gdbcontroller import GdbController
from pprint import pprint
import re
import subprocess
import time
import os
from .watchpoint import LamportWatchpointManager

class Debugger:
    def __init__(self, code_path, compiled_path, rr: bool = False):
        self.compiled_path = os.path.abspath(compiled_path)
        self.code_path = os.path.abspath(code_path)
        self.enable_rr = rr
        if rr:
            subprocess.run(["rr", "record", self.compiled_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.gdb = GdbController(command=["rr", "replay", "--interpreter=mi3"])
        else:
            self.gdb = GdbController(command=["gdb", "--interpreter=mi3"])
        self.gdb.write(f"file {self.compiled_path}")
        with open(self.code_path, "r") as file:
            self.code = file.read()
        
        # ✅ Simplificar: solo funciones y threads en debugger
        self.functions = self.parse_code()
        self.threads = {}
        self.correspondence = {}

        # ✅ LamportManager gestiona las variables globales
        self.lamport_manager = LamportWatchpointManager(self)

    def parse_code(self):
        """Method to parse the code and get the functions and their lines"""
        function_pattern = re.compile(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\*?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{')

        functions = {}
        lines = self.code.split('\n')
        current_function = None
        start_line = None
        brace_count = 0

        for i, line in enumerate(lines):
            match = function_pattern.match(line)
            if match:
                current_function = match.group(1)
                start_line = i + 1
            
            if current_function:
                brace_count += len(re.findall(r'\{', line))
                brace_count -= len(re.findall(r'\}', line))
                if brace_count == 0:
                    functions[current_function] = (start_line, i + 1)
                    current_function = None


        return functions

    def get_code_function(self, function):
        """Method to get the code of a function"""
        start_line, end_line = self.functions[function]
        lines = self.code.split('\n')
        code = lines[start_line - 1:end_line]
        code = '\n'.join(code)

        return code, start_line

    def get_stack_depth(self):
        """Method to get the stack depth"""
        response = self._gdb_write("-stack-info-depth")
        if response and response[0].get("message") == "done":
            return int(response[0]["payload"]["depth"])
        return 0
    
    def run(self):
        """Method to run the program"""
        exec_run = self._gdb_write("-exec-run")
        
        for response in exec_run:
            if response.get("message") == "thread-exited":
                self.threads.pop(response["payload"]["id"], None)

        # Get thread information
        threads_info = self.get_thread_info() 

        stop_reason = self._extract_stop_reason(exec_run)
        print(f"Razón de parada: {stop_reason}") 
        
        if hasattr(self, 'lamport_manager') and self.lamport_manager._is_lamport_watchpoint_hit(stop_reason):
            self.lamport_manager.update_global_variables(threads_info)  # ✅ Pasar diccionario
            return self.continue_execution()
        else:
            self.lamport_manager.update_global_variables(threads_info)  # ✅ Pasar diccionario

        if self.enable_rr:
            return self.continue_execution()
        else:
            return self._update_thread_functions(threads_info)

    def _update_thread_functions(self, threads_info=None):
        """Actualiza la información de hilos optimizando consultas a GDB"""
        self.threads.clear()  
        # Obtenemos toda la información necesaria en una sola consulta
        if threads_info is None:
            threads_info = self.get_thread_info()

        current_thread_id = str(threads_info.get("current-thread-id"))

        # Procesamiento por lotes de los hilos
        for thread in threads_info["threads"]:
            thread_id = str(thread["id"])
            thread_name = thread["target-id"]
            if self._process_thread(thread_id, thread_name) is None:
                continue

        self.select_thread(current_thread_id)

        self.get_all_thread_local_variables()

        return self.threads

    def _process_thread(self, thread_id, thread_name):
        """Procesa un hilo optimizando el acceso a frames"""
        self.select_thread(thread_id)
        
        # Obtenemos todos los frames en una sola consulta
        frames_response = self._gdb_write("-stack-list-frames 0 %d" % (self.get_stack_depth() - 1))
        frames = frames_response[0]["payload"].get("stack", []) if frames_response else []
        for frame in frames:
            if frame.get("fullname") == self.code_path:
                self._update_thread_data(thread_id, thread_name, frame)
                return frame
        return None

    def _update_thread_data(self, thread_id, thread_name, frame_info):
        """Actualiza los datos del hilo de forma eficiente"""
        thread_key = self.correspondence.setdefault(thread_name, thread_id)
        code, start_line = self.get_code_function(frame_info["func"])

        self.threads[thread_key] = {
            "function": frame_info["func"],
            "line": frame_info["line"],
            "code": code,
            "start_line": start_line,
        }

    def continue_execution(self):
        """Continue mejorado que maneja watchpoints transparentemente"""
        
        while True:
            exec_continue = self._gdb_write("-exec-continue")
            stop_reason = self._extract_stop_reason(exec_continue)

            if hasattr(self, 'lamport_manager') and self.lamport_manager._is_lamport_watchpoint_hit(stop_reason):
                # ✅ Obtener thread info correctamente
                threads_info = self.get_thread_info()
                self.lamport_manager.update_global_variables(threads_info)
                continue
            else:
                print(f"Razón de parada: {stop_reason}")
                break
        
        # Limpiar threads que hayan terminado
        for response in exec_continue:
            if response.get("message") == "thread-exited":
                self.threads.pop(response["payload"]["id"], None)

        # ✅ Actualizar al final
        threads_info = self.get_thread_info()
        self.lamport_manager.update_global_variables(threads_info)

        return self._update_thread_functions(threads_info)
    
    def reverse_continue(self):
        """Method to reverse continue the execution of the program"""

        if self.enable_rr:

            self._gdb_write("reverse-continue")

        return self._update_thread_functions()

    def generic_step(self, step_type, thread_id=None):
        correspondece_step = {
            "step_over": "-exec-next",
            "step_into": "-exec-step", 
            "step_out": "-exec-finish"
        }

        # Asegurar consistencia de tipos para thread_id
        if thread_id is not None:
            thread_id = str(thread_id)

        # Configuración inicial del hilo...
        if not self.enable_rr and thread_id is not None:
            selection_success = self.select_thread(thread_id)
            try:
                current_thread_info = self.get_thread_info()
                current_thread = current_thread_info.get("current-thread-id")
                if str(current_thread) != str(thread_id):
                    return self.threads
            except Exception as e:
                return self.threads
        elif thread_id is not None:
            selection_success = self.select_thread(thread_id)

        if step_type == "step_out":
            frame_depth = self.get_stack_depth()
            if frame_depth == 1:
                step_type = "step_over"
    
        # Ejecutar el comando de step
        step_command = correspondece_step[step_type]
        
        try:
            step_result = self._gdb_write(step_command)
            
            # 🚀 NUEVA FUNCIONALIDAD: Manejar watchpoints transparentemente
            return self._handle_step_stop_transparently(step_type, thread_id)
            
        except Exception as e:
            return self.threads

    def _handle_step_stop_transparently(self, step_type, thread_id):
        """Maneja la parada después de un step, continuando si es por watchpoint"""
        
        # Verificar si hay manager de Lamport configurado
        if not hasattr(self, 'lamport_manager'):
            return self._finalize_step_update(thread_id)
        
        # Loop para manejar múltiples watchpoints en una sola línea
        max_watchpoint_hits = 10  # Evitar loops infinitos
        watchpoint_count = 0
        
        while watchpoint_count < max_watchpoint_hits:
            try:
                # Obtener razón de la parada
                stop_reason = self._get_current_stop_reason()
                location_info = self._get_current_location_info()
                
                # Verificar si fue nuestro watchpoint
                if self.lamport_manager._is_lamport_watchpoint_hit(stop_reason):
                    watchpoint_count += 1
                    print(f"📊 Step se paró en watchpoint transparente ({watchpoint_count}), continuando...")
                    
                    # Capturar evento
                    event = self.lamport_manager._capture_lamport_event(location_info)
                    self.lamport_manager.lamport_events.append(event)
                    
                    if self.lamport_manager.is_transparent_mode:
                        # Continuar el step transparentemente
                        step_command = {
                            "step_over": "-exec-next",
                            "step_into": "-exec-step",
                            "step_out": "-exec-finish"
                        }[step_type]
                        
                        self._gdb_write(step_command)
                        continue  # Verificar de nuevo si hay más watchpoints
                    else:
                        # Modo no transparente - parar aquí
                        break
                else:
                    # No es nuestro watchpoint - parada legítima
                    break
                    
            except Exception as e:
                print(f"❌ Error manejando transparencia en step: {e}")
                break
    
        # Finalizar actualización normalmente
        return self._finalize_step_update(thread_id)

    def _finalize_step_update(self, thread_id):
        """Finaliza la actualización después de un step"""
        # Solo procesar hilo específico si se proporciona thread_id
        if thread_id is not None and not self.enable_rr:
            # Usar la función optimizada para actualizar un solo hilo
            success = self._process_single_thread_optimized(thread_id)
            if success:
                # Actualizar variables globales después del step
                self.global_variables = self.get_global_variable_values()
                return self.threads
    
        # Si no se proporciona thread_id específico o estamos en modo RR, actualizar todos los hilos
        result = self._update_thread_functions()
        # Actualizar variables globales
        self.global_variables = self.get_global_variable_values()
        
        return result

    def step_over(self, thread_id=None):
        if thread_id is not None:
            thread_id = str(thread_id)
        
        if self.enable_rr:
            # Para modo RR, no necesitamos thread_id específico
            return self.generic_step("step_over", None)
        elif thread_id is not None:
            # Para modo GDB, usar generic_step que ya maneja transparencia
            return self.generic_step("step_over", thread_id)
        
        return self.threads

    def step_into(self, thread_id=None):
        if thread_id is not None:
            thread_id = str(thread_id)
        
        if self.enable_rr:
            return self.generic_step("step_into", None)
        elif thread_id is not None:
            # Ejecutar step con transparencia
            result = self.generic_step("step_into", thread_id)
            
            # Verificar si estamos en el código del usuario después del step
            try:
                frame_info = self.info_frame()[0]["payload"]
                if frame_info["frame"]["fullname"] != self.code_path:
                    # Si salimos del código del usuario, hacer step_out
                    result = self.generic_step("step_out", thread_id)
            except:
                pass
            
            return result
        
        return self.threads

    def step_out(self, thread_id=None):
        if self.enable_rr:
            return self.generic_step("step_out", None)
        elif thread_id is not None:
            # Verificar frame superior
            upper_frame = None
            try:
                frames_response = self.get_frames()
                if frames_response:
                    stack = frames_response[0]["payload"].get("stack", [])
                    if len(stack) > 1:
                        upper_frame = stack[1]
            except:
                pass
            
            # Si es hilo recién creado, hacer step_over en su lugar
            if upper_frame and upper_frame["func"] == "start_thread":
                return self.generic_step("step_over", thread_id)
            
            return self.generic_step("step_out", thread_id)
        
        return self.threads
    

    def generic_reverse_step(self, step_type):
        correspondece_step = {
            "step_over": "-exec-next",
            "step_into": "-exec-step",
            "step_out": "-exec-finish"
        }

        if step_type == "step_out":
            frame_depth = self.get_stack_depth()
            if frame_depth == 1:
                step_type = "step_over"
        
        self._gdb_write(correspondece_step[step_type])

    def reverse_step_over(self):
        if self.enable_rr:
           
            self.generic_reverse_step("step_over")

        return self.threads

    def reverse_step_into(self):
        """Method to reverse step into the current function"""
        if self.enable_rr:

            self.generic_reverse_step("step_into")

            stack = self.get_frames()[0]["payload"].get("stack", [])
            
            # Si la anterior llamada fue la creación del hilo no se puede hacer reverse step_out 
            if stack[1] and stack[1]["func"] == "start_thread":
                self.generic_reverse_step("step_over")
                
            # Si al volver hacia atrás nos hemos metido en un función que no es nuestra, salimos     
            depth = 0
            while stack[depth]["fullname"] != self.code_path:
                depth += 1
                self.generic_reverse_step("step_out")
                if depth >= len(stack):
                    print("Error: No se pudo volver a la función")
        
        return self.threads

        
    def reverse_step_out(self):
        
        if self.enable_rr:
            self.generic_reverse_step("step_out")

            frame_info = self.info_frame()[0]["payload"]

            if frame_info["frame"]["fullname"] != self.code_path:
                self.generic_reverse_step("step_into")
                frame_info = self.info_frame()[0]["payload"]
        
        return self.threads

    def set_breakpoint(self, line):
        try:
            if line == None:
                return True 
            self._gdb_write(f"-break-insert {line}")
            print(f"Breakpoint en la línea {line}")
            return True
        except Exception as e:
            print(e)
            return False
        
    def select_thread(self, thread_id):
        self._gdb_write(f"-thread-select {thread_id}")

    def get_thread_info(self):
        """Obtiene información de hilos de forma consistente"""
        threads_info = self._gdb_write("-thread-info")
        if threads_info[-1].get("message") == "done":
            return threads_info[-1]["payload"]
        # Buscar la respuesta con message='done'
        for response in threads_info:
            if isinstance(response, dict) and response.get("message") == "done":
                return response["payload"]

        for i in range(3):
            print("No se encontró thread info válido, reintentando...")
            threads_info = self._gdb_write("-thread-info")
            for response in threads_info:
                if isinstance(response, dict) and response.get("message") == "done":
                    return response["payload"]
            time.sleep(1)

        raise RuntimeError("No se pudo obtener información de hilos después de varios intentos")

    def info_frame(self):
        info = self._gdb_write("-stack-info-frame")
        return info

    def get_frames(self):
        return self._gdb_write("-stack-list-frames")

    def select_frame(self, frame):
        self._gdb_write(f"-stack-select-frame {frame}")

    def _gdb_write(self, command, timeout_sec=5):
        if not self.gdb:
            raise RuntimeError("GDB controller is not initialized")
        return self.gdb.write(command, timeout_sec=timeout_sec)
    
    def get_all_thread_local_variables(self):
        """Method to get all the variables of all the threads except the ones in the exclude_vars list"""

        for thread_id in self.threads.keys():
            self.select_thread(thread_id)

            frames_info = self.get_frames()
            if not frames_info or "stack" not in frames_info[0]["payload"]:
                print(f"No se encontraron frames para el thread {thread_id}.")
                continue

            frames = frames_info[0]["payload"]["stack"]
            thread_variables = {}

            for frame in frames:
                frame_level = frame["level"]
                frame_func = frame["func"]
                frame_file = frame.get("fullname", "")

                variable_info = self._gdb_write(f'-stack-list-variables --thread {thread_id} --frame {frame_level} 1')
                if variable_info and "variables" in variable_info[0]["payload"]:
                    variables = variable_info[0]["payload"]["variables"]
                    
                    for var in variables:
                        name = var.get('name') + "@" + frame_func
                        value = var.get('value')
                        if frame_file == self.code_path:
                            thread_variables[name] = value
                        

            self.threads[thread_id]["variables"] = thread_variables

    def __del__(self):
        if hasattr(self,"gdb") and self.gdb:
            self._gdb_write("-gdb-exit")
            self.gdb.exit()
            self.gdb = None

    def get_current_state_for_frontend(self):
        """Obtiene el estado completo para el frontend"""
        return {
            "threads": self.threads,
            "globals": self.lamport_manager.get_lamport_globals_structure()
        }

    def _extract_stop_reason(self, exec_response):
        """Extrae la razón de parada de la respuesta de exec-run/exec-continue"""
        try:
            for response in exec_response:
                if response.get("message") == "stopped":
                    payload = response.get("payload", {})
                    return payload.get("reason", "breakpoint-hit")  # Default común
                # También verificar en el tipo de respuesta
                elif response.get("type") == "notify" and "stopped" in str(response):
                    return "breakpoint-hit"
        except:
            pass
        return "breakpoint-hit"  # Asumir breakpoint por defecto

    def _extract_location_info(self, exec_response):
        """Extrae información de ubicación de la respuesta"""
        try:
            for response in exec_response:
                if response.get("message") == "stopped":
                    payload = response.get("payload", {})
                    return {
                        "line": payload.get("line"),
                        "file": payload.get("file"),
                        "function": payload.get("func"),
                        "address": payload.get("addr")
                    }
        except Exception as e:
            print(f"Error extrayendo información de ubicación: {e}")
            
        return {}

