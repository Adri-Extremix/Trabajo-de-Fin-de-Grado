import pygdbmi.constants
from pygdbmi.gdbcontroller import GdbController
import pygdbmi
from pprint import pprint
import re


class Debugger:
    def __init__(self, code_path, compiled_path):
        self.compiled_path = compiled_path
        self.gdb = GdbController()
        self.gdb.write(f"file {compiled_path}")
        with open(code_path, "r") as file:
            self.code = file.read()
        self.functions = self.parse_code()
        print(self.functions)
        self.functions_threads = {}

    def parse_code(self):
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

    def get_stack_depth(self):
        # Obtener la profundidad del stack del hilo actual
        response = self.gdb.write("-stack-info-depth")
        if response and response[0].get("message") == "done":
            return int(response[0]["payload"]["depth"])
        return 0

    def _search_original_function(self, thread_id):
        self.select_thread(thread_id)
        depth = self.get_stack_depth()
        current_frame = 0

        while current_frame < depth:
            self.select_frame(current_frame)
            frame_info = self.gdb.write("-stack-info-frame")[0]["payload"]

            if frame_info["frame"]["file"] == "codigo.c":
                self.functions_threads[thread_id] = (
                    frame_info["frame"]["func"], frame_info["frame"]["line"]
                )
                break

            current_frame += 1

        if current_frame >= depth:
            print(f"Thread {thread_id} origin not found in compiled file")

    def _update_thread_functions(self):
        try:
            info_threads = self.get_thread_info()[0]
            # To recover the current thread                
            if info_threads.get("payload").get("current-thread-id"):      
                selected_thread = info_threads["payload"]["current-thread-id"]

            for thread in info_threads["payload"]["threads"]:
                thread_id = thread["id"]

                # To know the threads that are not in the compiled file
                thread_file = thread["frame"]["file"] 
                if thread_file != self.compiled_path:
                    print(f"Thread {thread_id} is not in the compiled file")

                    self._search_original_function(thread_id)
                else:
                    self.functions_threads[thread_id] = (thread["frame"]["func"],thread["frame"]["line"])
            if info_threads.get("payload").get("current-thread-id"):
                self.select_thread(selected_thread)
        except pygdbmi.constants.GdbTimeoutError:
            print("Timeout")
            self.functions_threads = {}

        return self.functions_threads

#TODO: Devolver solo lo necesario en los métodos
    def run(self):
        exec_run = self.gdb.write("-exec-run")
        for response in exec_run:
            if response.get("message") == "thread-created":
                self.functions_threads[response["payload"]["id"]] = None
            elif response.get("message") == "thread-exited":
                self.functions_threads.pop(response["payload"]["id"], None)
        return self._update_thread_functions()
                
    def continue_execution(self):
        exec_continue = self.gdb.write("-exec-continue")
        pprint(exec_continue)
        for response in exec_continue:
            if response.get("message") == "thread-created":
                self.functions_threads[response["payload"]["id"]] = None
            elif response.get("message") == "thread-exited":
                self.functions_threads.pop(response["payload"]["id"], None)

        return self._update_thread_functions()
    
    def step_over(self):
        pprint(self.gdb.write("-exec-next"))

    def step_into(self):
        #TODO: Si se está en una función que no esté en el código fuente, se realizará un step out para salir de la función
        pprint(self.gdb.write("-exec-step"))
    
    def step_out(self):
        pprint(self.gdb.write("-exec-finish"))
    
    def set_breakpoint(self, line):
        self.gdb.write(f"-break-insert {line}")

    def select_thread(self, thread_id):
        self.gdb.write(f"-thread-select {thread_id}")

    def get_thread_info(self):
        info = self.gdb.write("-thread-info")
        print("Thread info:")
        pprint(info)
        return info

    def get_frames(self):
        return self.gdb.write("-stack-list-frames")

    def select_frame(self, frame):
        self.gdb.write(f"-stack-select-frame {frame}")
    
    def get_all_thread_variables(self):
        """Method to get all the variables of all the threads except the ones in the exclude_vars list"""

        exclude_vars = {
            "sc_cancel_oldtype", "sc_ret", "unwind_buf", "not_first_call", 
            "save_errno", "ret", "r", "pd", "clock_id", "clock_id@entry", 
            "flags", "flags@entry", "rem", "rem@entry", "req", "req@entry", 
            "ts"
        }

        threads_info = self.get_thread_info()
        if not threads_info or "threads" not in threads_info[0]["payload"]:
            print("No se encontraron threads.")
            return []
        
        all_variables = {}
        threads = threads_info[0]["payload"]["threads"]

        for thread in threads:
            thread_id = thread["id"]
            self.select_thread(thread_id)

            frames_info = self.get_frames()
            if not frames_info or "stack" not in frames_info[0]["payload"]:
                print(f"No se encontraron frames para el thread {thread_id}.")
                continue

            frames = frames_info[0]["payload"]["stack"]
            thread_variables = {}

            for frame in frames:
                frame_level = frame["level"]
                self.select_frame(frame_level)

                variable_info = self.gdb.write("-stack-list-variables 1")
                if variable_info and "variables" in variable_info[0]["payload"]:
                    variables = variable_info[0]["payload"]["variables"]
                    for var in variables:
                        name = var.get('name')
                        value = var.get('value')
                        if name not in exclude_vars:
                            thread_variables[name] = value

            all_variables[thread_id] = thread_variables

        return all_variables
            
    def get_code_function(self, function):
        start_line, end_line = self.functions[function]
        lines = self.code.split('\n')
        code = lines[start_line - 1:end_line]
        code = '\n'.join(code)

        return code
        

        
            

debugger = Debugger("codigo.c","./codigo")
print("Colocando breakpoint")
debugger.set_breakpoint(50)
print("Ejecutando el programa")
debugger.set_breakpoint(76)
print("Ejecutando el programa")
print(debugger.run())
print("Continuando la ejecución")
print(debugger.continue_execution())
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