from flask import Flask
from flask_cors import CORS
from compiler import Compiler

class Backend:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app, resources={r"/CC/*": {"origins": "*"}})
        self.compiler = Compiler()
        self.setup_routes()
    
    def setup_routes(self):
        self.app.add_url_rule("/CC/compile", "compile_code", self.compiler.compile_code, methods=["POST"])
        self.app.add_url_rule("/CC/run", "run_code", self.compiler.run_code, methods=["POST"])

    def run(self):
        self.app.run(debug=True, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    backend = Backend()
    backend.run()
