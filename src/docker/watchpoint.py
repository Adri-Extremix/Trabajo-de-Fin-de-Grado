import time
import os
import datetime

class LamportWatchpointManager:
    def __init__(self, debugger):
        self.debugger = debugger
        self.lamport_watchpoints = set()
        self.is_transparent_mode = True
        self.lamport_clocks = {}
        
        # Gestión de variables globales
        self.global_variables = {}
        self._initialize_global_variables()
        self.setup_transparent_watchpoints()
        
    def _initialize_global_variables(self):
        """Inicializar variables globales con diferentes estrategias según el modo"""
        print("🔍 Inicializando detección de variables globales...")
        
        if self.debugger.enable_rr:
            # Para RR, usar parsing del código fuente
            print("Modo RR: Usando parsing de código fuente")
            self._parse_globals_from_source_code()
        else:
            # Para GDB normal, intentar símbolos primero, luego parsing si falla
            print("Modo GDB: Intentando detección por símbolos")
            if not self._initialize_from_gdb_symbols():
                print("Símbolos GDB fallaron, usando parsing de código")
                self._parse_globals_from_source_code()
        
        print(f"✅ Variables globales detectadas: {list(self.global_variables.keys())}")

    def _initialize_from_gdb_symbols(self):
        """Método original para GDB normal"""
        try:
            symbols_response = self.debugger._gdb_write("-symbol-info-variables")
            
            if symbols_response and symbols_response[0].get("message") == "done":
                payload = symbols_response[0]["payload"]
                symbols_data = payload.get("symbols", {})
                debug_symbols = symbols_data.get("debug", [])
                
                for file_info in debug_symbols:
                    filename = file_info.get("filename", "")
                    symbols = file_info.get("symbols", [])
                    
                    our_file_name = os.path.basename(self.debugger.code_path)
                    current_file_name = os.path.basename(filename)
                    
                    if our_file_name == current_file_name:
                        for symbol in symbols:
                            var_name = symbol.get("name")
                            var_type = symbol.get("type")
                            
                            if var_name and not var_name.startswith('_'):
                                self.global_variables[var_name] = {
                                    "current_type": var_type,
                                    "current_value": None,
                                    "history": []
                                }
                
                return len(self.global_variables) > 0
                        
        except Exception as e:
            print(f"Error con símbolos GDB: {e}")
            return False

    def _parse_globals_from_source_code(self):
        """Parsea variables globales directamente del código fuente"""
        try:
            import re
            
            lines = self.debugger.code.split('\n')
            
            # Patrones para detectar variables globales
            patterns = [
                # Variables globales simples: tipo nombre = valor;
                r'^\s*(?:extern\s+)?(?:static\s+)?(?:const\s+)?(?:volatile\s+)?((?:int|float|double|char|long|short|unsigned)\s*\*?\s*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=\s*[^;]+)?\s*;',
                # Arrays globales: tipo nombre[tamaño];
                r'^\s*(?:extern\s+)?(?:static\s+)?(?:const\s+)?(?:volatile\s+)?((?:int|float|double|char|long|short|unsigned)\s*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\[[^\]]*\]\s*(?:=\s*[^;]+)?\s*;'
            ]
            
            in_function = False
            brace_count = 0
            
            for line_num, line in enumerate(lines, 1):
                # Detectar inicio/fin de funciones y estructuras
                if re.search(r'^\s*(?:typedef\s+)?(?:struct|union|enum)\s+', line.strip()):
                    continue  # Saltar definiciones de estructuras
                    
                if re.search(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\*?\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)\s*\{', line):
                    in_function = True
                    brace_count = 0
                
                if in_function:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count <= 0:
                        in_function = False
                
                # Solo procesar líneas fuera de funciones (variables globales)
                if not in_function:
                    for pattern in patterns:
                        match = re.match(pattern, line.strip())
                        if match:
                            var_type = match.group(1).strip()
                            var_name = match.group(2).strip()
                            
                            # Excluir declaraciones no deseadas
                            if not re.search(r'\b(typedef|struct|union|enum|void\*|pthread_t)\b', line):
                                self.global_variables[var_name] = {
                                    "current_type": var_type,
                                    "current_value": None,
                                    "history": []
                                }
                                print(f"Variable global detectada: {var_name} (tipo: {var_type}) en línea {line_num}")
            
            # Validar que las variables detectadas sean accesibles en GDB/RR
            self._validate_detected_variables()
            
        except Exception as e:
            print(f"Error parseando código fuente: {e}")

    def _validate_detected_variables(self):
        """Valida que las variables detectadas sean accesibles en GDB/RR"""
        valid_vars = {}
        
        for var_name, var_info in self.global_variables.items():
            try:
                # Intentar acceder a la variable
                if self.debugger.enable_rr:
                    # Para RR, usar comando más simple
                    response = self.debugger._gdb_write(f"print {var_name}")
                else:
                    # Para GDB normal
                    response = self.debugger._gdb_write(f"-var-create - * {var_name}")
                
                if response and any(resp.get("message") == "done" for resp in response):
                    valid_vars[var_name] = var_info
                    print(f"Variable global válida: {var_name}")
                    
                    # Limpiar variable temporal en GDB normal
                    if not self.debugger.enable_rr:
                        try:
                            var_obj = None
                            for resp in response:
                                if resp.get("message") == "done" and "payload" in resp:
                                    var_obj = resp["payload"].get("name")
                                    break
                            if var_obj:
                                self.debugger._gdb_write(f"-var-delete {var_obj}")
                        except:
                            pass
                else:
                    print(f"Variable no accesible: {var_name}")
                    
            except Exception as e:
                print(f"Error validando variable {var_name}: {e}")
        
        self.global_variables = valid_vars

    def update_global_variables(self, thread_info=None):
        """Actualizar valores optimizado para RR y GDB"""
        try:
            for var_name in self.global_variables:
                # Usar comando más simple y compatible con RR
                if self.debugger.enable_rr:
                    value_response = self.debugger._gdb_write(f"print {var_name}")
                    new_value = self._extract_value_from_print_response(value_response)
                else:
                    value_response = self.debugger._gdb_write(f"-data-evaluate-expression {var_name}")
                    new_value = None
                    if value_response and value_response[0].get("message") == "done":
                        new_value = value_response[0]["payload"].get("value")
                
                if new_value is not None:
                    old_value = self.global_variables[var_name]["current_value"]
                    
                    # Si cambió, agregar al historial
                    if new_value != old_value:
                        # Obtener thread actual
                        if thread_info:
                            current_thread = thread_info.get("current-thread-id", "1")
                        else:
                            thread_response = self.debugger.get_thread_info()
                            current_thread = thread_response.get("current-thread-id", "1")
                        
                        self.lamport_clocks[current_thread] = self.lamport_clocks.get(current_thread, 0) + 1

                        # Agregar evento al historial
                        event = {
                            "value": new_value,
                            "lamport_time": self.lamport_clocks[current_thread],
                            "thread_id": str(current_thread),
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                        self.global_variables[var_name]["history"].append(event)
                        print(f"Historial actualizado: {var_name} = {new_value} (lamport: {self.lamport_clocks[current_thread]})")
                    
                    # Actualizar valor actual
                    self.global_variables[var_name]["current_value"] = new_value
                    
        except Exception as e:
            print(f" Error actualizando variables: {e}")

    def _extract_value_from_print_response(self, response):
        """Extrae el valor de una respuesta de 'print' de GDB"""
        try:
            for resp in response:
                if resp.get("type") == "console":
                    payload = resp.get("payload", "")
                    # Buscar patrón como "$1 = 5"
                    import re
                    match = re.search(r'\$\d+\s*=\s*(.+)', payload)
                    if match:
                        return match.group(1).strip()
                elif resp.get("message") == "done" and "payload" in resp:
                    return resp["payload"].get("value")
        except:
            pass
        return None

    def setup_transparent_watchpoints(self, variable_names=None):
        """Configura watchpoints para variables globales"""
        if variable_names is None:
            variable_names = list(self.global_variables.keys())
            
        print(f"Configurando watchpoints para: {variable_names}")
        
        for var_name in variable_names:
            try:
                response = self.debugger._gdb_write(f"watch {var_name}")
                
                if response and any(resp.get("message") == "done" for resp in response):
                    self.lamport_watchpoints.add(var_name)
                    print(f"Watchpoint configurado para '{var_name}'")
                    
            except Exception as e:
                print(f"Error configurando watchpoint para {var_name}: {e}")

    def _is_lamport_watchpoint_hit(self, stop_reason):
        """Determina si la parada fue SOLO por nuestro watchpoint"""
        try:
            if isinstance(stop_reason, list):
                has_watchpoint = any("watchpoint" in reason.lower() for reason in stop_reason if isinstance(reason, str))
                has_breakpoint = any("breakpoint" in reason.lower() for reason in stop_reason if isinstance(reason, str))
                
                #  Si hay breakpoint del usuario, NO es transparente
                if has_breakpoint and has_watchpoint:
                    return False  # No hacer auto-continue
                
                # Solo watchpoint → transparente
                return has_watchpoint and not has_breakpoint
                
            elif isinstance(stop_reason, str):
                # Solo watchpoint, sin breakpoint
                return "watchpoint" in stop_reason.lower() and "breakpoint" not in stop_reason.lower()
                
            return False
        except:
            return False

    def get_lamport_globals_structure(self):
        """Genera la estructura de globals para el diagrama de Lamport"""
        return self.global_variables