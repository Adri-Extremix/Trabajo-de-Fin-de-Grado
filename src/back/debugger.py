from pygdbmi.gdbcontroller import GdbController
from pprint import pprint
import re

#TODO: Devolver solo lo necesario en los métodos
class Debugger:
    def __init__(self, code_path, compiled_path):
        self.compiled_path = compiled_path
        self.gdb = GdbController()
        self.gdb.write(f"file {compiled_path}")
        with open(code_path, "r") as file:
            self.code = file.read()
        self.functions = self.parse_code()

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

    def get_variables(self):
        #TODO: Ver diferencias entre ambos comandos
        output_locals = self.gdb.write("-stack-list-locals --all-values")
        output_variables = self.gdb.write("-stack-list-variables 1")

        def process_output(output, key):
            if output and 'payload' in output[0] and key in output[0]['payload']:
                variables = output[0]['payload'][key]
                for var in variables:
                    name = var.get('name')
                    value = var.get('value')
                    var_type = var.get('type')
                    print(f"Variable: {name}, Type: {var_type}, Value: {value}")
            else:
                print(f"No se encontraron variables en {key}.")

        process_output(output_locals, 'locals')
        process_output(output_variables, 'variables')
    
    def set_breakpoint(self, line):
        pprint(self.gdb.write(f"-break-insert {line}"))

    def select_thread(self, thread_id):
        pprint(self.gdb.write(f"-thread-select {thread_id}"))

    def get_thread_info(self):
        pprint(self.gdb.write("-thread-info"))
    
    def get_code_function(self, function):
        start_line, end_line = self.functions[function]
        lines = self.code.split('\n')
        code = lines[start_line - 1:end_line]
        code = '\n'.join(code)

        return code
        

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
        
            

debugger = Debugger("codigo.c","./codigo")
print("Colocando breakpoint en línea 11")
debugger.set_breakpoint("11")
print("Ejecutando hasta el breakpoint")
debugger.run()
print("Funcion actual")
debugger.get_code_function("main")
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