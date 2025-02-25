from doctest import debug
import pygdbmi.constants
from pygdbmi.gdbcontroller import GdbController
import pygdbmi
from pprint import pprint
import re
import subprocess
import time
import os
import sys


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
        
        #print(f"Thread {thread_id} no encontrado en código compilado")
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

    def generic_step(self, thread_id, step_type):

        correspondece_step = {
            "step_over": "-exec-next",
            "step_into": "-exec-step",
            "step_out": "-exec-finish"
        }

        self.select_thread(thread_id)

        if step_type == "step_out":
            frame_depth = self.get_stack_depth()
            if frame_depth == 1:
                step_type = "step_over"
        print("Step type: ", step_type)
        self._gdb_write(correspondece_step[step_type])
        for name, id in self.correspondence.items():
            if id == thread_id:
                self._process_thread(thread_id, name)
                break


    def step_over(self, thread_id = None):
        
        if not self.enable_rr and thread_id:
            self.generic_step(thread_id, "step_over")
        
        else:
            pass

        return self.threads
   

    def step_into(self, thread_id = None):
        #TODO: Si se está en una función que no esté en el código fuente, se realizará un step out para salir de la función

        if not self.enable_rr and thread_id:
            self.generic_step(thread_id, "step_into")

            frame_info = self.info_frame()[0]["payload"]


            if frame_info["frame"]["fullname"] != self.code_path:
                self.step_out(thread_id) 
                frame_info = self.info_frame()[0]["payload"]
        
        else:
            pass 

        return self.threads

    def step_out(self, thread_id = None):

        # Agregamos código para conocer el frame superior al actual
        upper_frame = None
        frames_response = self.get_frames()
        if frames_response:
            stack = frames_response[0]["payload"].get("stack", [])
            if len(stack) > 1:
                upper_frame = stack[1]

        if upper_frame and upper_frame["func"] == "start_thread":
            self.step_over(thread_id)
            return self.threads

        
        if not self.enable_rr and thread_id:

            self.generic_step(thread_id, "step_out")


            frame_info = self.info_frame()[0]["payload"]

            while frame_info["frame"]["fullname"] != self.code_path:
                self.step_into(thread_id)

        else:
            pass

        return self.threads

        
    def set_breakpoint(self, line):
        self._gdb_write(f"-break-insert {line}")

    def select_thread(self, thread_id):
        self._gdb_write(f"-thread-select {thread_id}")

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

    


if __name__ == "__main__":
    start_time = time.time()


    debugger = Debugger("../../examples/prueba1.c", "../../examples/prueba1.o", rr=False)

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
