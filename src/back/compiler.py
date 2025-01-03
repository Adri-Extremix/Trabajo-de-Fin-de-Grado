from flask import request, jsonify
import subprocess
import os
import tempfile

class Compiler:
    def __init__(self):
        self.compiled_file_path = None
    
    def compile_code(self):
        data = request.get_json()
        code = data.get("code","")

        # Crear un archivo temporal para el código C
        with tempfile.NamedTemporaryFile(delete=False, suffix=".c") as tmp_file:
            tmp_file.write(code.encode("utf-8"))
            tmp_file_path = tmp_file.name

        tmp_file.close()

        # Compilar el código C
        exe_file_path = tmp_file_path.replace(".c", "")
        compile_cmd = f"gcc -g -o {exe_file_path} {tmp_file_path} -pthread"
        compile_process = subprocess.run(compile_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        #Eliminar el archivo temporal después de la compilación
        os.remove(tmp_file_path)

        if compile_process.returncode != 0:
            stderr_output = compile_process.stderr.replace(tmp_file_path, "code.c")
            return jsonify({"output": "Error: La compilación ha fallado \n" + stderr_output})
        
        self.compiled_file_path = exe_file_path

        return jsonify({"output": "Compilación terminada con éxito"})
    
    def run_code(self):
        if not self.compiled_file_path or not os.path.exists(self.compiled_file_path):
            return jsonify({"error": "Executable file not found"}),400
        
        run_cmd = f"{self.compiled_file_path}"
        run_process = subprocess.run(run_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if run_process.returncode != 0:
            return jsonify({"error": run_process.stderr}), 400
        
        if run_process.stdout == "":
            run_process.stdout = "Ejecución completada"

        return jsonify({"output": run_process.stdout})