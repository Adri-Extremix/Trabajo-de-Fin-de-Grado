import pygdbmi.constants
from pygdbmi.gdbcontroller import GdbController
import pygdbmi
from pprint import pprint
import re
import subprocess
import time


class Debugger:
    def __init__(self, code_path, compiled_path, rr: bool = False):
        self.compiled_path = compiled_path
        self.code_path = code_path
        print(self.code_path)
        self.enable_rr = rr
        if rr:
            subprocess.run(["rr", "record", compiled_path])
            self.gdb = GdbController(command=["rr", "replay", "--interpreter=mi3"])
        else:
            self.gdb = GdbController(command=["gdb", "--interpreter=mi3"])

        self.gdb.write(f"file {compiled_path}")
        with open(self.code_path, "r") as file:
            self.code = file.read()
        self.functions = self.parse_code()
        print(self.functions)
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

        return code

    def get_stack_depth(self):
        """Method to get the stack depth"""
        response = self._gdb_write("-stack-info-depth")
        if response and response[0].get("message") == "done":
            return int(response[0]["payload"]["depth"])
        return 0
    
    def _update_thread_functions(self):
        """Actualiza la información de hilos optimizando consultas a GDB"""
        self.threads.clear()  # Limpieza más eficiente
        # Obtenemos toda la información necesaria en una sola consulta
        threads_info = self.get_thread_info()[-1]["payload"]
        current_thread_id = threads_info.get("current-thread-id")
        
        # Procesamiento por lotes de los hilos
        threads_batch = []
        for thread in threads_info["threads"]:
            thread_id = str(thread["id"])
            threads_batch.append((thread_id, thread["target-id"]))
        
        # Procesamiento paralelizable (usando ThreadPool si es posible)
        for thread_id, thread_name in threads_batch:
            if self._process_thread(thread_id, thread_name) is None:
                continue
        
        
        self.select_thread(current_thread_id)
        
        self.get_all_thread_variables()
        
        return self.threads

    def _process_thread(self, thread_id, thread_name):
        """Procesa un hilo optimizando el acceso a frames"""
        self.select_thread(thread_id)
        
        # Obtenemos todos los frames en una sola consulta
        frames_response = self._gdb_write("-stack-list-frames 0 %d" % (self.get_stack_depth() - 1))
        frames = frames_response[0]["payload"].get("stack", []) if frames_response else []
        
        for frame in frames:
            
            if frame.get("file") == self.code_path:
                self._update_thread_data(thread_id, thread_name, frame)
                return frame
        
        print(f"Thread {thread_id} no encontrado en código compilado")
        return None

    def _update_thread_data(self, thread_id, thread_name, frame_info):
        """Actualiza los datos del hilo de forma eficiente"""
        thread_key = self.correspondence.setdefault(thread_name, thread_id)
        
        self.threads[thread_key] = {
            "function": frame_info["func"],
            "line": frame_info["line"],
            "code": self.get_code_function(frame_info["func"])
        }

    def run(self):
        """Method to run the program"""
        exec_run = self._gdb_write("-exec-run")
        self.gdb.write("-thread-info",timeout_sec=5)
        
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

#TODO: Devolver solo lo necesario en los métodos
    def step_over(self):
        pprint(self._gdb_write("-exec-next"))

    def step_into(self):
        #TODO: Si se está en una función que no esté en el código fuente, se realizará un step out para salir de la función
        pprint(self._gdb_write("-exec-step"))
    
    def step_out(self):
        pprint(self._gdb_write("-exec-finish"))
    
    def set_breakpoint(self, line):
        self._gdb_write(f"-break-insert {line}")

    def select_thread(self, thread_id):
        self._gdb_write(f"-thread-select {thread_id}")

    def get_thread_info(self):
        info = self._gdb_write("-thread-info")
        return info

    def get_frames(self):
        return self._gdb_write("-stack-list-frames")

    def select_frame(self, frame):
        self._gdb_write(f"-stack-select-frame {frame}")

    def _gdb_write(self, command):
        if not self.gdb:
            raise RuntimeError("GDB controller is not initialized")
        return self.gdb.write(command)
    
    def get_all_thread_variables(self):
        #TODO: Alternativa: Obtener las funciones a las que pertence cada variable y solo obtener las variables de las funciones del usuario
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
                frame_file = frame.get("file", "")

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

start_time = time.time()

# Aquí pones el código cuya ejecución quieres medir

debugger = Debugger("prueba.c","./prueba", rr=True)
print("Colocando breakpoint")
debugger.set_breakpoint(22)
print("Colocando breakkpoint")
debugger.set_breakpoint(50)
print("Ejecutando el programa")
pprint(debugger.run())



print("Continuando la ejecución")
pprint(debugger.continue_execution())
print("Volviendo al anterior breakpoint")
pprint(debugger.reverse_continue())


elapsed_time = time.time() - start_time
print(f"La ejecución tardó {elapsed_time:.4f} segundos")


""" print("Ejecutando la siguiente línea")
debugger.step_into()
print("Ejecutando la siguiente línea")
debugger.step_into()
print("Ejecutando la siguiente línea")
debugger.step_into()
print("Ejecutando la siguiente línea")
debugger.step_into()
print("Ejecutando la siguiente línea")
debugger.step_into() """