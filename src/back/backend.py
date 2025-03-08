from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from compiler import Compiler
from debugger import Debugger

class Backend:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.compiler = Compiler()
        self.debugger = None # Inicializamos el debugger como None
        
        self.setup_routes()

    def setup_routes(self):

        # Rutas para servir el frontend
        self.app.add_url_rule("/", "serve_index", self.serve_index)
        self.app.add_url_rule("/<path:filename>", "serve_static", self.serve_static)


        self.app.add_url_rule("/CC/compile", "compile_code", self.compile_code, methods=["POST"])
        self.app.add_url_rule("/CC/run", "run_code", self.run_code, methods=["POST"])
        self.app.add_url_rule("/CC/debug/add_breakpoint", "add_breakpoint", self.add_breakpoint, methods=["POST"])
        self.app.add_url_rule("/CC/debug/step_over", "step_over", self.step_over, methods=["GET"])
        self.app.add_url_rule("/CC/debug/step_into", "step_into", self.step_into, methods=["GET"])
        self.app.add_url_rule("/CC/debug/step_out", "step_out", self.step_out, methods=["GET"])
        self.app.add_url_rule("/CC/debug/continue", "continue_execution", self.continue_execution, methods=["GET"])
        self.app.add_url_rule("/CC/debug/run", "run_execution", self.run_execution, methods=["GET"])

    def serve_index(self):
        return send_from_directory("../front/dist", "index.html")

    def serve_static(self, filename):
        import os
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "front", "dist")
        return send_from_directory(static_dir, filename)


    def compile_code(self):
        data = request.get_json()
        code = data.get("code", "")
        result = self.compiler.compile_code(code)

        if result["success"]:
            self.debugger = Debugger(self.compiler.code_file_path, self.compiler.compiled_file_path)
            response = jsonify({"output": result["output"]})
            print({"output": result["output"]})
            return response, 200
        else:
            response = jsonify({"error": result["error"]})
            print({"error": result["error"]})
            return response, 400
    
    def run_code(self):
        result = self.compiler.run_code()
        if result["success"]:
            response = jsonify({"output": result["output"]})
            print({"output": result["output"]})
            return response, 200
        else:
            response = jsonify({"error": result["error"]})
            print({"error": result["error"]})
            return response, 400

    def add_breakpoint(self):
        if not self.debugger:
            response = jsonify({"error": "Debugger no inicializado. Compila primero el código."})
            print({"error": "Debugger no inicializado. Compila primero el código."})
            return response, 400
        
        data = request.get_json()
        print(data)
        breakpoints = data.get("breakpoints", [])
        result = True
        for breakpoint in breakpoints:
            result_breakpoint = self.debugger.set_breakpoint(breakpoint)
            if not result_breakpoint:
                result = False
                break

        if result:
            response = jsonify({"message": result})
            print({"message": result})
            return response, 200
        else:
            response = jsonify({"error": "No se ha obtenido resultado"})
            print({"error": "No se ha obtenido resultado"})
            return response, 400
    
    def step_over(self):
        return self._execute_debug_step("step_over")
    
    def step_into(self):
        return self._execute_debug_step("step_into")
    
    def step_out(self):
        return self._execute_debug_step("step_out")

    def _execute_debug_step(self, step_method):
        """Método auxiliar para ejecutar operaciones de paso en el debugger"""
        if not self.debugger:
            response = jsonify({"error": "Debugger no inicializado. Compila primero el código."})
            print({"error": "Debugger no inicializado. Compila primero el código."})
            return response, 400
        
        data = request.get_json()
        thread_id = data.get("thread_id", -1)
        
        method = getattr(self.debugger, step_method)
        result = method(thread_id=thread_id)
        response = jsonify(result)
        print(result)
        return response, 200
    
    def continue_execution(self):
        if not self.debugger:
            response = jsonify({"error": "Debugger no inicializado. Compila primero el código."})
            print({"error": "Debugger no inicializado. Compila primero el código."})
            return response, 400
        
        result = self.debugger.continue_execution()
        response = jsonify(result)
        print(result)
        return response, 200
    
    def run_execution(self):
        if not self.debugger:
            response = jsonify({"error": "Debugger no inicializado. Compila primero el código."})
            print({"error": "Debugger no inicializado. Compila primero el código."})
            return response, 400
        
        result = self.debugger.run()
        response = jsonify(result)
        print(result)
        return response, 200

    def run(self):
        self.app.run(debug=True, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    backend = Backend()
    backend.run()
