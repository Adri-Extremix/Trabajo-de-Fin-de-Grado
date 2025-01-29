import pygdbmi.constants
from pygdbmi.gdbcontroller import GdbController
import pygdbmi
from pprint import pprint
import re
import subprocess


class Debugger:
    def __init__(self, code_path, compiled_path, rr: bool = False):
        self.compiled_path = compiled_path
        self.enable_rr = rr
        if rr:
            subprocess.run(["rr", "record", compiled_path])
            self.gdb = GdbController(command=["rr", "replay", "--interpreter=mi3"])
        else:
            self.gdb = GdbController(command=["gdb", "--interpreter=mi3"])

        self.gdb.write(f"file {compiled_path}")
        with open(code_path, "r") as file:
            self.code = file.read()
        self.functions = self.parse_code()
        print(self.functions)
        self.threads = {}
        self.correspondence = {}
        self.gdb.write("set scheduler-locking off")  # Permitir planificación normal de hilos

        self.position_pc_counter = None # In order to know the position of the pc counter in the arquitecure

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
        response = self.gdb.write("-stack-info-depth")
        if response and response[0].get("message") == "done":
            return int(response[0]["payload"]["depth"])
        return 0
    
    def _update_thread_functions(self):
        """Method to update the functions of the threads"""
        try:
            info_threads = self.get_thread_info()[-1]
            # To recover the current thread                
            if info_threads.get("payload").get("current-thread-id"):      
                selected_thread = info_threads["payload"]["current-thread-id"]

            for thread in info_threads["payload"]["threads"]:
                thread_id = thread["id"]
                thread_name = thread["target-id"]

                # To know the threads that are not in the compiled file
                thread_file = thread["frame"].get("file") 
                if thread_file != self.compiled_path:
                    print(f"Thread {thread_id} is not in the compiled file")
                    # TODO: Siempre se podría usar esta función
                    self._search_original_function(thread_name,thread_id)
                else:
                    #pprint(pc_counter)
                    print(self.threads)
                    if not self.correspondence.get(thread_name):
                        self.correspondence[thread_name] = thread_id
                    else:
                        self.threads[self.correspondence[thread_name]] = {
                            "function": thread["frame"]["func"],
                            "line": thread["frame"]["line"]
                        }
            if info_threads.get("payload").get("current-thread-id"):
                self.select_thread(selected_thread)
        except pygdbmi.constants.GdbTimeoutError:
            print("Timeout")
            self.threads = {}

        return self.threads

    def _search_original_function(self, thread_name, thread_id):
        #TODO: Cambiar para que use thread_name
        """Method to search the function in the original code if the thread is not in a function of the compiled file"""
        self.select_thread(thread_id)
        depth = self.get_stack_depth()
        current_frame = 0

        while current_frame < depth:
            self.select_frame(current_frame)
            frame_info = self.gdb.write("-stack-info-frame")[0]["payload"]
            #pprint(self.gdb.write("-stack-info-frame"))
            if frame_info["frame"].get("file") == "codigo.c":

                if not self.correspondence.get(thread_name):
                        self.correspondence[thread_name] = thread_id
                else:
                    self.threads[self.correspondence[thread_name]] = {
                        "function": frame_info["frame"]["func"],
                        "line": frame_info["frame"]["line"]
                    }
                 
                break

            current_frame += 1

        if current_frame >= depth:
            print(f"Thread {thread_id} origin not found in compiled file")
            if thread_id in self.threads.keys():
                self.threads.pop(thread_id, None)

    def run(self):
        """Method to run the program"""
        exec_run = self.gdb.write("-exec-run")
        
        
        for response in exec_run:
            
            if response.get("message") == "thread-exited":
                self.threads.pop(response["payload"]["id"], None)

        if self.enable_rr:
            # Run with rr doesn't arrive to a breakpoint, so we need to continue the execution
            return self.continue_execution()

        return self._update_thread_functions()
                    
    def continue_execution(self):
        """Method to continue the execution of the program"""
        
        exec_continue = self.gdb.write("-exec-continue")
        
        pprint(exec_continue)
        for response in exec_continue:
            
            if response.get("message") == "thread-exited":
                self.threads.pop(response["payload"]["id"], None)
                
        return self._update_thread_functions()
    
    def reverse_continue(self):
        """Method to reverse continue the execution of the program"""

        if self.enable_rr:

            self.gdb.write("reverse-continue")
            


        return self._update_thread_functions()

#TODO: Devolver solo lo necesario en los métodos
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
            
        

        
            

debugger = Debugger("codigo.c","./codigo", rr=True)
print("Colocando breakpoint")
debugger.set_breakpoint(50)
print("Colocando breakkpoint")
debugger.set_breakpoint(70)
print("Ejecutando el programa")
pprint(debugger.run())
print("Continuando la ejecución")
pprint(debugger.continue_execution())
print("Volviendo al anterior breakpoint")
pprint(debugger.reverse_continue())
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