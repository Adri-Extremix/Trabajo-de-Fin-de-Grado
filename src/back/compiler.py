import subprocess
import os
import tempfile

class Compiler:
    def __init__(self):
        self.compiled_file_path = None
        self.code_file_path = None
    
    def compile_code(self, code):
        """Método que se encarga de compilar el código C recibido por parámetro"""
        """ data = request.get_json()
        code = data.get("code", "") """

        # Crear un archivo temporal para el código C
        with tempfile.NamedTemporaryFile(delete=False, suffix=".c") as tmp_file:
            tmp_file.write(code.encode("utf-8"))
            self.code_file_path = tmp_file.name

        # Compilar el código C
        exe_file_path = self.code_file_path.replace(".c", "")
        compile_cmd = f"gcc -g -o {exe_file_path} {self.code_file_path} -pthread"
        compile_process = subprocess.run(compile_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if compile_process.returncode != 0:
            stderr_output = compile_process.stderr.replace(self.code_file_path, "code.c")
            return {"success": False, "error": f"Error: La compilación ha fallado \n{stderr_output}"}
        
        self.compiled_file_path = exe_file_path
        return {"success": True, "output": "Compilación terminada con éxito"}
    
    def run_code(self):
        if not self.compiled_file_path or not os.path.exists(self.compiled_file_path):
            return {"success": False, "error": "Executable file not found"}
        
        run_cmd = f"{self.compiled_file_path}"
        run_process = subprocess.run(run_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if run_process.returncode != 0:
            return {"success": False, "error": run_process.stderr}
        
        output = run_process.stdout if run_process.stdout else "Ejecución completada"
        return {"success": True, "output": output}