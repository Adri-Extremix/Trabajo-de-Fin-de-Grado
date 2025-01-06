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
        self.app.add_url_rule("/CC/debug/run", "run", self.run, methods=["POST"])


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

    def run(self):
        self.app.run(debug=True, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    backend = Backend()
    backend.run()
