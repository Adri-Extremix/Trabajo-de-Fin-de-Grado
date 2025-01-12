from pygdbmi.gdbcontroller import GdbController
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

    def parse_code(self):
        function_pattern = re.compile(r'^\s*(?:int|void|float|double|char|int\*|void\*|float\*|double\*|char\*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{')
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

#TODO: Devolver solo lo necesario en los métodos
    def run(self):
        pprint(self.gdb.write("-exec-run"))

    def continue_execution(self):
        pprint(self.gdb.write("-exec-continue"))

    def step_over(self):
        pprint(self.gdb.write("-exec-next"))

    def step_into(self):
        pprint(self.gdb.write("-exec-step"))
    
    def step_out(self):
        pprint(self.gdb.write("-exec-finish"))
    
    def select_thread(self, thread_id):
        pprint(self.gdb.write(f"-thread-select {thread_id}"))

    def get_thread_info(self):
        info = self.gdb.write("-thread-info")
        print("Thread info:")
        pprint(info)
        return info

    def get_frames(self):
        return self.gdb.write("-stack-list-frames")
    
    def get_all_thread_variables(self):

        system_prefixes = {
        "sc_", "unwind_buf", "not_first_call", "save_errno", "ret", 
        "r", "pd", "clock_id", "ts"
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
                self.gdb.write(f"-stack-select-frame {frame_level}")

                variable_info = self.gdb.write("-stack-list-variables 1")
                if variable_info and "variables" in variable_info[0]["payload"]:
                    variables = variable_info[0]["payload"]["variables"]
                    for var in variables:
                        name = var.get('name')
                        value = var.get('value')
                        if not any(name.startswith(prefix) for prefix in system_prefixes):
                            thread_variables[name] = value

            all_variables[thread_id] = thread_variables

        return all_variables
            

    def set_breakpoint(self, line):
        pprint(self.gdb.write(f"-break-insert {line}"))
    
    def get_code_function(self, function):
        start_line, end_line = self.functions[function]
        lines = self.code.split('\n')
        code = lines[start_line - 1:end_line]
        code = '\n'.join(code)

        return code
        

        
            

debugger = Debugger("codigo.c","./codigo")
print("Colocando breakpoint en línea 11")
debugger.set_breakpoint("34")
print("Ejecutando hasta el breakpoint")
debugger.run()
print("Obteniendo variables")
pprint(debugger.get_all_thread_variables())
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