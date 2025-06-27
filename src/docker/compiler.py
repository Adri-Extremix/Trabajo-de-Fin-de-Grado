import subprocess
import os
import tempfile

class Compiler:
    def __init__(self):
        self.compiled_file_path = None
        self.code_file_path = None
    
    def compile_code(self, code) -> dict:
        """Método que se encarga de compilar el código C recibido por parámetro"""
        """ data = request.get_json()
        code = data.get("code", "") """

        # Crear un archivo temporal para el código C
        with tempfile.NamedTemporaryFile(delete=False, suffix=".c") as tmp_file:
            tmp_file.write(code.encode("utf-8"))
            self.code_file_path = tmp_file.name

        # Compilar el código C
        exe_file_path = self.code_file_path.replace(".c", "")
        compile_cmd = f"gcc -g -O0 -o {exe_file_path} {self.code_file_path} -pthread"
        compile_process = subprocess.run(compile_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


        if compile_process.returncode != 0:
            stderr_output = compile_process.stderr.replace(self.code_file_path, "code.c")
            raise Exception(f"Compilation error: {stderr_output}")
        
        output_helgrind = self.run_helgrind(exe_file_path)

        self.compiled_file_path = exe_file_path
        return {"result":"Compilation successful", "output_helgrind": output_helgrind}

    def run_helgrind(self, exe_file_path) -> str:
        """Realiza un análisis de memoria con helgrind"""
        helgrind_cmd = f"valgrind --tool=helgrind --track-lockorders=yes --read-var-info=yes --history-level=approx {exe_file_path}"
        helgrind_process = subprocess.run(helgrind_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        helgrind_output = helgrind_process.stderr
        print("Helgrind output:", helgrind_output)
        return helgrind_output

    def run_code(self) -> str:
        if not self.compiled_file_path or not os.path.exists(self.compiled_file_path):
            raise Exception("Error: Executable file not found")
        
        run_cmd = f"{self.compiled_file_path}"
        run_process = subprocess.run(run_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if run_process.returncode != 0:
            raise Exception (f"Execution error: {run_process.stderr}")
        
        output = run_process.stdout if run_process.stdout else "Execution completed successfully"
        return output