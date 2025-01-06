from pygdbmi.gdbcontroller import GdbController
from pprint import pprint

#TODO: Devolver solo lo necesario en los métodos
class Debugger:
    def __init__(self, code_path, compiled_path):
        self.code_path = code_path
        self.compiled_path = compiled_path
        self.gdb = GdbController()
        self.gdb.write(f"file {compiled_path}")

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
    
    def get_actual_code(self):
        #TODO: Función que parsea el fichero de código y devuelva el fragmento de código que se está ejecutando
        pass

debugger = Debugger("./codigo")
debugger.set_breakpoint("16")
debugger.run()
pprint("Continue ")
print("")
print("")
