from flask import Flask, request, jsonify
from flask_cors import CORS
from compiler import Compiler
from debugger import Debugger

class Backend:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app, resources={r"/CC/*": {"origins": "*"}})
        self.compiler = Compiler()
        self.debugger = None # Inicializamos el debugger como None
        
        self.setup_routes()

    def setup_routes(self):
        self.app.add_url_rule("/CC/compile", "compile_code", self.compile_code, methods=["POST"])
        self.app.add_url_rule("/CC/run", "run_code", self.run_code, methods=["POST"])
        self.app.add_url_rule("/CC/debug/add_breakpoint", "add_breakpoint", self.add_breakpoint, methods=["POST"])
        self.app.add_url_rule("/CC/debug/step_over", "step_over", self.step_over, methods=["POST"])
        self.app.add_url_rule("/CC/debug/step_into", "step_into", self.step_into, methods=["POST"])
        self.app.add_url_rule("/CC/debug/step_out", "step_out", self.step_out, methods=["POST"])
        self.app.add_url_rule("/CC/debug/continue", "continue_execution", self.continue_execution, methods=["POST"])
        self.app.add_url_rule("/CC/debug/run", "run_execution", self.run_execution, methods=["POST"])


    def compile_code(self):
        data = request.get_json()
        code = data.get("code", "")
        result = self.compiler.compile_code(code)

        if result["success"]:
            self.debugger = Debugger(self.compiler.code_file_path ,self.compiler.compiled_file_path)
            return jsonify({"output": result["output"]}), 200
        else:
            return jsonify({"error": result["error"]}), 400
    
    def run_code(self):
        result = self.compiler.run_code()
        if result["success"]:
            return jsonify({"output": result["output"]}), 200
        else:
            return jsonify({"error": result["error"]}), 400

    def add_breakpoint(self):
        if not self.debugger:
            return jsonify({"error": "Debugger no inicializado. Compila primero el código."}), 400
        
        data = request.get_json()
        line_number = data.get("line", -1)
        
        result = self.debugger.add_breakpoint(line_number)

        if result:
            return jsonify({"message": result}), 200
        else:
            return jsonify({"error": "No se ha obtenido resultado"}), 400
    
    def step_over(self):
        return self._execute_debug_step("step_over")
    
    def step_into(self):
        return self._execute_debug_step("step_into")
    
    def step_out(self):
        return self._execute_debug_step("step_out")

    def _execute_debug_step(self, step_method):
        """Método auxiliar para ejecutar operaciones de paso en el debugger"""
        if not self.debugger:
            return jsonify({"error": "Debugger no inicializado. Compila primero el código."}), 400
        
        data = request.get_json()
        thread_id = data.get("thread_id", -1)
        
        method = getattr(self.debugger, step_method)
        result = method(thread_id=thread_id)
        return jsonify(result), 200
    
    def continue_execution(self):
        if not self.debugger:
            return jsonify({"error": "Debugger no inicializado. Compila primero el código."}), 400
        
        result = self.debugger.continue_execution()
        return jsonify(result), 200
    
    def run_execution(self):
        if not self.debugger:
            return jsonify({"error": "Debugger no inicializado. Compila primero el código."}), 400
        
        result = self.debugger.start_debugging()
        return jsonify(result), 200

    def run(self):
        self.app.run(debug=True, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    backend = Backend()
    backend.run()
