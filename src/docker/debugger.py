from concurrent.futures import thread
from doctest import debug
import pygdbmi.constants
from pygdbmi.gdbcontroller import GdbController
from pprint import pprint
import re
import subprocess
import time
import os


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
        
        # Configurar GDB para depuración de hilos
        if not rr:
            # Configurar scheduler-locking para controlar la ejecución de hilos
            self.gdb.write("set scheduler-locking step")  # Solo el hilo seleccionado ejecuta durante step
            # Configurar para mostrar información detallada de hilos
            self.gdb.write("set print thread-events on")
            # Configurar modo all-stop (todos los hilos se detienen cuando uno se detiene)
            self.gdb.write("set non-stop off")
        
        with open(self.code_path, "r") as file:
            self.code = file.read()
        self.functions = self.parse_code()
        self.threads = {}
        self.correspondence = {}
        
        
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
    
    def _update_thread_functions(self):
        """Actualiza la información de hilos optimizando consultas a GDB"""
        # No limpiar completamente self.threads para preservar correspondencias
        old_threads = dict(self.threads)
        self.threads.clear()
        
        # Obtenemos toda la información necesaria en una sola consulta
        threads_info = self.get_thread_info()[-1]["payload"]
        current_thread_id = str(threads_info.get("current-thread-id"))
        
        # Procesamiento por lotes de los hilos
        threads_batch = []
        for thread in threads_info["threads"]:
            thread_id = str(thread["id"])
            thread_target = thread["target-id"]
            thread_state = thread.get("state", "unknown")
            threads_batch.append((thread_id, thread_target))
        
        # Procesamiento paralelizable (usando ThreadPool si es posible)
        for thread_id, thread_name in threads_batch:
            result = self._process_thread(thread_id, thread_name)
            if result is None:
                continue
        
        self.select_thread(current_thread_id)
        self.get_all_thread_local_variables()
        
        # Mostrar cambios en hilos
        new_thread_ids = set(self.threads.keys())
        old_thread_ids = set(old_threads.keys())
        
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

    def _process_single_thread_optimized(self, thread_id):
        """Procesa un solo hilo de manera optimizada, actualizando solo sus datos"""
        # Asegurar que thread_id sea string para consistencia
        thread_id = str(thread_id)
        
        # Verificar que el hilo existe en nuestro registro
        if thread_id not in self.threads:
            return False
        
        old_data = dict(self.threads[thread_id])
        
        # Seleccionar el hilo
        try:
            self.select_thread(thread_id)
            
            # Verificar que la selección fue exitosa
            current_thread_info = self.get_thread_info()[-1]["payload"]
            current_thread = current_thread_info.get("current-thread-id")
            
            if str(current_thread) != str(thread_id):
                return False
        except Exception as e:
            return False
        
        # Obtener información del frame actual
        try:
            frame_info_response = self.info_frame()
            
            if not frame_info_response:
                return False
                
            if "frame" not in frame_info_response[0]["payload"]:
                return False
                
            frame_info = frame_info_response[0]["payload"]["frame"]
            
        except Exception as e:
            return False
        
        # Verificar que estamos en código del usuario
        if frame_info.get("fullname") != self.code_path:
            return False
        
        # Buscar el nombre del hilo en correspondence
        thread_name = None
        for name, id in self.correspondence.items():
            if str(id) == str(thread_id):
                thread_name = name
                break
        
        if not thread_name:
            return False
        
        # Actualizar datos del hilo
        try:
            self._update_thread_data(thread_id, thread_name, frame_info)
        except Exception as e:
            return False
        
        # Actualizar variables del hilo
        try:
            self._update_thread_variables(thread_id)
        except Exception as e:
            return False
        
        return True

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

    def run(self):
        """Method to run the program"""
        exec_run = self._gdb_write("-exec-run")
        self._gdb_write("-thread-info",timeout_sec=5)
        
        for response in exec_run:
            
            if response.get("message") == "thread-exited":
                self.threads.pop(response["payload"]["id"], None)

        if self.enable_rr:
            # Run with rr doesn't arrive to a breakpoint, so we need to continue the execution
            return self.continue_execution()


        return self._update_thread_functions()
                    
    def continue_execution(self):
        """Method to continue the execution of the program"""
        
        exec_continue = self._gdb_write("-exec-continue")
        
        for response in exec_continue:
            
            if response.get("message") == "thread-exited":
                self.threads.pop(response["payload"]["id"], None)
                
        return self._update_thread_functions()
    
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

        # Capturar estado inicial para comparación
        initial_threads = dict(self.threads)
        
        # En modo GDB (no RR), configurar scheduler para controlar hilos
        if not self.enable_rr and thread_id is not None:
            # Asegurar que solo el hilo seleccionado ejecute
            selection_success = self.select_thread(thread_id)
            
            # Verificar que el hilo está seleccionado correctamente
            try:
                current_thread_info = self.get_thread_info()[-1]["payload"]
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
        except Exception as e:
            return self.threads
        
        # Solo procesar hilo específico si se proporciona thread_id y no estamos en modo RR
        if thread_id is not None and not self.enable_rr:
            # Usar la función optimizada para actualizar un solo hilo
            success = self._process_single_thread_optimized(thread_id)
            
            if success:
                return self.threads
        
        # Si no se proporciona thread_id específico o estamos en modo RR, actualizar todos los hilos
        result = self._update_thread_functions()
        
        return result

    def _update_thread_variables(self, thread_id):
        """Actualiza las variables de un hilo específico para optimizar rendimiento"""
        # Asegurar que thread_id sea string para consistencia
        thread_id = str(thread_id)
        
        if thread_id not in self.threads:
            return
            
        self.select_thread(thread_id)
        
        frames_info = self.get_frames()
        if not frames_info or "stack" not in frames_info[0]["payload"]:
            return
            
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

    def step_over(self, thread_id = None):
        if thread_id is not None:
            thread_id = str(thread_id)
            
        if self.enable_rr:
            # Para modo RR, no necesitamos thread_id específico
            self.generic_step("step_over", None)
            # En modo RR necesitamos actualizar todos los hilos porque no sabemos cuál cambió
            return self._update_thread_functions()
        elif thread_id is not None:
            # Para modo GDB, necesitamos thread_id específico
            self.generic_step("step_over", thread_id)
            # En modo GDB solo actualizamos el hilo específico (ya se hace en generic_step)
            return self.threads
            
        return self.threads

    def step_into(self, thread_id = None):
        if thread_id is not None:
            thread_id = str(thread_id)
            
        if self.enable_rr:
            # Para modo RR, no necesitamos thread_id específico
            self.generic_step("step_into", None)
            # En modo RR necesitamos actualizar todos los hilos porque no sabemos cuál cambió
            return self._update_thread_functions()
        elif thread_id is not None:
            # Para modo GDB, necesitamos thread_id específico
            self.generic_step("step_into", thread_id)
            
            # Verificar si estamos en el código del usuario después del step
            frame_info = self.info_frame()[0]["payload"]
            if frame_info["frame"]["fullname"] != self.code_path:
                self.generic_step("step_out", thread_id)
            
            # En modo GDB solo actualizamos el hilo específico (ya se hace en generic_step)
            return self.threads
        
        return self.threads

    def step_out(self, thread_id = None):
        if self.enable_rr:
            # Para modo RR, no necesitamos thread_id específico
            self.generic_step("step_out", None)
            # En modo RR necesitamos actualizar todos los hilos porque no sabemos cuál cambió
            return self._update_thread_functions()
        elif thread_id is not None:
            # Para modo GDB, necesitamos thread_id específico
            # Agregamos código para conocer el frame superior al actual
            upper_frame = None
            frames_response = self.get_frames()
            if frames_response:
                stack = frames_response[0]["payload"].get("stack", [])
                if len(stack) > 1:
                    upper_frame = stack[1]
            # Con el frame superior podemos saber si es un hilo recien creado y por lo tanto 
            # no es necesario hacer un step out
            if upper_frame and upper_frame["func"] == "start_thread":
                self.generic_step("step_over", thread_id)
                # En este caso especial sí necesitamos actualizar todos para verificar el estado
                return self.threads
            
            self.generic_step("step_out", thread_id)
            # En modo GDB solo actualizamos el hilo específico (ya se hace en generic_step)
            return self.threads
        
        return self.threads
    

    def generic_reverse_step(self, step_type):
        correspondece_step = {
            "step_over": "reverse-next",
            "step_into": "reverse-step",
            "step_out": "reverse-finish"
        }

        if step_type == "step_out":
            frame_depth = self.get_stack_depth()
            if frame_depth == 1:
                step_type = "step_over"
        
        self._gdb_write(correspondece_step[step_type])

    def reverse_step_over(self):
        if self.enable_rr:
            self.generic_reverse_step("step_over")

        return self._update_thread_functions()

    def reverse_step_into(self):
        """Method to reverse step into the current function"""
        if self.enable_rr:
                
            self.generic_reverse_step("step_into")

            stack = self.get_frames()[0]["payload"].get("stack", [])
            
            # Si la anterior llamada fue la creación del hilo no se puede hacer reverse step_out 
            if len(stack) > 1 and stack[1]["func"] == "start_thread":
                self.generic_reverse_step("step_over")
                
            # Si al volver hacia atrás nos hemos metido en un función que no es nuestra, salimos     
            depth = 0
            while depth < len(stack) and stack[depth]["fullname"] != self.code_path:
                depth += 1
                self.generic_reverse_step("step_out")
                if depth >= len(stack):
                    break
        
        return self._update_thread_functions()

    def reverse_step_out(self):
        if self.enable_rr:
                
            self.generic_reverse_step("step_out")
            frame_info = self.info_frame()[-1]["payload"]
            if frame_info["frame"]["fullname"] != self.code_path:
                self.generic_reverse_step("step_into")
                frame_info = self.info_frame()[-1]["payload"]
        return self._update_thread_functions()

    def set_breakpoint(self, line):
        try:
            if line == None:
                return True 
            self._gdb_write(f"-break-insert {line}")
            return True
        except Exception as e:
            return False
        
    def select_thread(self, thread_id):
        """Selecciona un hilo específico para depuración"""
        # Asegurar que thread_id sea string para consistencia
        thread_id = str(thread_id)
        
        # Verificar estado antes de la selección
        try:
            before_info = self.get_thread_info()[-1]["payload"]
            current_before = before_info.get("current-thread-id")
            available_threads = [t['id'] for t in before_info.get('threads', [])]
            
            # Verificar que el hilo solicitado existe
            if str(thread_id) not in [str(t) for t in available_threads]:
                return False
                
        except Exception as e:
            return False
        
        # Ejecutar el comando de selección
        try:
            self._gdb_write(f"-thread-select {thread_id}")
        except Exception as e:
            return False
        
        # Verificar estado después de la selección
        try:
            after_info = self.get_thread_info()[-1]["payload"]
            current_after = after_info.get("current-thread-id")
            
            if str(current_after) == str(thread_id):
                return True
            else:
                return False
                
        except Exception as e:
            return False

    def get_thread_info(self):
        info = self._gdb_write("-thread-info")
        return info

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

    def get_scheduler_config(self):
        """Método para verificar la configuración actual del scheduler de GDB"""
        if not self.enable_rr:
            scheduler_info = self._gdb_write("show scheduler-locking")
            non_stop_info = self._gdb_write("show non-stop")
            return scheduler_info, non_stop_info
        else:
            return None, None

    def set_scheduler_mode(self, mode="step"):
        """
        Configura el modo de scheduler de GDB
        Modos disponibles:
        - 'off': Todos los hilos pueden ejecutarse (por defecto)
        - 'on': Solo el hilo actual puede ejecutarse
        - 'step': Solo el hilo actual ejecuta durante operaciones de paso
        """
        if not self.enable_rr:
            valid_modes = ["off", "on", "step"]
            if mode not in valid_modes:
                return False
            
            self._gdb_write(f"set scheduler-locking {mode}")
            return True
        else:
            return False

    def __del__(self):
        if hasattr(self,"gdb") and self.gdb:
            self._gdb_write("-gdb-exit")
            self.gdb.exit()
            self.gdb = None

    


if __name__ == "__main__":
    start_time = time.time()


    debugger = Debugger("../../examples/prueba1.c", "../../examples/prueba1.o", rr=True)

    print("Colocando breakpoint")
    debugger.set_breakpoint(22)
    print("Colocando breakkpoint")
    debugger.set_breakpoint(33)
    print("Ejecutando el programa")
    pprint(debugger.run())
    pprint(debugger.correspondence)
    print("Continuando la ejecución")
    pprint(debugger.continue_execution())
    print("Volviendo al anterior breakpoint")
    pprint(debugger.reverse_continue())

    elapsed_time = time.time() - start_time
    print(f"La ejecución tardó {elapsed_time:.4f} segundos")