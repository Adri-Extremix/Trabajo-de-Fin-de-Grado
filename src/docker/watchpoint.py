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
        
        # ✅ NUEVO: Registro de breakpoints activos
        self.active_breakpoints = {}

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
        
        print(f"Variables globales detectadas: {list(self.global_variables.keys())}")

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
                r'^\s*(?:extern\s+)?(?:static\s+)?(?:const\s+)?(?:volatile\s+)?((?:int|float|double|char|long|short|unsigned|struct\s+\w+|enum\s+\w+)\s*\*?\s*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=\s*[^;]+)?\s*;',
            
            # Arrays unidimensionales: tipo nombre[tamaño];
                r'^\s*(?:extern\s+)?(?:static\s+)?(?:const\s+)?(?:volatile\s+)?((?:int|float|double|char|long|short|unsigned|struct\s+\w+)\s*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\[[^\]]*\]\s*(?:=\s*[^;]+)?\s*;',
            
            # Arrays multidimensionales: tipo nombre[M][N] = {...};
                r'^\s*(?:extern\s+)?(?:static\s+)?(?:const\s+)?(?:volatile\s+)?((?:int|float|double|char|long|short|unsigned|struct\s+\w+)\s*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\[[^\]]*\]){2,}\s*(?:=\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}\s*)?;',
            
            # Variables de tipos struct definidos: struct NombreStruct nombre = {...};
                r'^\s*(?:extern\s+)?(?:static\s+)?(?:const\s+)?(?:volatile\s+)?struct\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=\s*\{[^}]*\})?\s*;',
            
            # Tipos definidos con typedef: MiTipo nombre = valor;
                r'^\s*(?:extern\s+)?(?:static\s+)?(?:const\s+)?(?:volatile\s+)?([A-Z][a-zA-Z0-9_]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=\s*[^;]+)?\s*;'
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

    def update_global_variables(self, thread_info=None, is_reverse_operation=False):
        """Actualizar valores optimizado para RR y GDB con soporte para reversión"""
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
                    
                    # Si cambió el valor
                    if new_value != old_value:
                        # 🔧 OBTENER THREAD ID CONSISTENTE usando correspondence
                        current_thread = self._get_consistent_thread_id(thread_info)
                        
                        if is_reverse_operation:
                            # 🔙 MODO REVERSIÓN: Quitar entradas del historial
                            self._handle_reverse_variable_change(var_name, new_value, current_thread)
                        else:
                            # ➡️ MODO NORMAL: Agregar al historial
                            self._handle_forward_variable_change(var_name, new_value, current_thread)
                
                # Actualizar valor actual
                self.global_variables[var_name]["current_value"] = new_value
                
        except Exception as e:
            print(f"Error actualizando variables: {e}")

    def _get_consistent_thread_id(self, thread_info=None):
        """Obtiene el ID de thread consistente usando el mapeo de correspondence"""
        try:
            # Obtener información de hilos si no se proporciona
            if thread_info is None:
                thread_info = self.debugger.get_thread_info()
            
            # ID del thread actual según GDB
            gdb_thread_id = str(thread_info.get("current-thread-id", "1"))
            
            # Buscar el thread actual en la lista de threads
            current_thread_name = None
            for thread in thread_info.get("threads", []):
                if str(thread["id"]) == gdb_thread_id:
                    current_thread_name = thread["target-id"]
                    break
            
            if current_thread_name:
                # 🔧 USAR EL MAPEO CONSISTENTE DE CORRESPONDENCE
                consistent_id = self.debugger.correspondence.get(current_thread_name, gdb_thread_id)
                print(f"Thread mapping: GDB-{gdb_thread_id} ({current_thread_name}) → App-{consistent_id}")
                return str(consistent_id)
            
            # Fallback al ID de GDB si no hay mapeo
            return gdb_thread_id
            
        except Exception as e:
            print(f"Error obteniendo thread ID consistente: {e}")
            return "1"  # Fallback al thread principal

    def _handle_forward_variable_change(self, var_name, new_value, current_thread):
        """Maneja cambios de variables en operaciones normales (hacia adelante)"""
        # 🔧 USAR THREAD ID CONSISTENTE PARA LAMPORT CLOCKS
        self.lamport_clocks[current_thread] = self.lamport_clocks.get(current_thread, 0) + 1

        # Agregar evento al historial
        event = {
            "value": new_value,
            "lamport_time": self.lamport_clocks[current_thread],
            "thread_id": str(current_thread),  # Ya es consistente
            "timestamp": datetime.datetime.now().isoformat(),
            "operation_type": "forward"
        }
        self.global_variables[var_name]["history"].append(event)
        print(f"Historial agregado: {var_name} = {new_value} (thread: {current_thread}, lamport: {self.lamport_clocks[current_thread]})")

    def _handle_reverse_variable_change(self, var_name, new_value, current_thread):
        """Maneja cambios de variables en operaciones de reversión"""
        history = self.global_variables[var_name]["history"]
        
        if history:
            removed_entries = []
            
            # 🔧 BUSCAR POR THREAD ID CONSISTENTE
            for i in range(len(history) - 1, -1, -1):
                entry = history[i]
                
                # Si encontramos una entrada que corresponde al thread consistente
                if entry["thread_id"] == str(current_thread):
                    removed_entry = history.pop(i)
                    removed_entries.append(removed_entry)
                    print(f"🔙 ⬅️ Historial revertido: {var_name} removió entrada de thread {current_thread}, lamport: {removed_entry['lamport_time']}")
                    
                    # Decrementar el reloj de Lamport para este thread
                    if self.lamport_clocks.get(current_thread, 0) > 0:
                        self.lamport_clocks[current_thread] -= 1
                    
                    break  # Solo remover una entrada por cambio
            
            # Si no encontramos entradas del thread actual, remover la más reciente
            if not removed_entries and history:
                removed_entry = history.pop()
                removed_entries.append(removed_entry)
                print(f"🔙 ⬅️ Historial revertido (general): {var_name} removió entrada de thread {removed_entry['thread_id']}, lamport: {removed_entry['lamport_time']}")
                
                # Decrementar el reloj del thread que hizo el cambio
                thread_of_removed = removed_entry["thread_id"]
                if self.lamport_clocks.get(thread_of_removed, 0) > 0:
                    self.lamport_clocks[thread_of_removed] -= 1

    def get_lamport_globals_structure_with_reverse_info(self):
        """Genera la estructura de globals para el diagrama de Lamport con información de reversión"""
        result = {}
        
        for var_name, var_data in self.global_variables.items():
            result[var_name] = {
                "current_type": var_data["current_type"],
                "current_value": var_data["current_value"],
                "history": var_data["history"],
                "total_changes": len(var_data["history"]),
                "threads_involved": list(set(entry["thread_id"] for entry in var_data["history"])),
                "last_change_time": var_data["history"][-1]["timestamp"] if var_data["history"] else None
            }
        
        return result
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

    def register_user_breakpoint(self, breakpoint_number, line, file_path):
        """Registra un breakpoint de usuario para distinguirlo de watchpoints"""
        self.active_breakpoints[str(breakpoint_number)] = {
            "type": "user_breakpoint",
            "line": line,
            "file": file_path,
            "timestamp": datetime.datetime.now().isoformat()
        }
        print(f"📍 Breakpoint de usuario registrado: #{breakpoint_number} en {file_path}:{line}")

    def register_watchpoint(self, breakpoint_number, variable_name):
        """Registra un watchpoint transparente"""
        self.active_breakpoints[str(breakpoint_number)] = {
            "type": "transparent_watchpoint",
            "variable": variable_name,
            "timestamp": datetime.datetime.now().isoformat()
        }
        print(f"👁️ Watchpoint transparente registrado: #{breakpoint_number} para variable '{variable_name}'")

    def unregister_breakpoint(self, breakpoint_number):
        """Elimina el registro de un breakpoint"""
        removed = self.active_breakpoints.pop(str(breakpoint_number), None)
        if removed:
            print(f"🗑️ Breakpoint #{breakpoint_number} eliminado del registro ({removed['type']})")

    def setup_transparent_watchpoints(self, variable_names=None):
        """Configura watchpoints para variables globales con registro mejorado"""
        if variable_names is None:
            variable_names = list(self.global_variables.keys())
            
        print(f"Configurando watchpoints para: {variable_names}")
        
        for var_name in variable_names:
            try:
                response = self.debugger._gdb_write(f"watch {var_name}")
                
                if response and any(resp.get("message") == "done" for resp in response):
                    self.lamport_watchpoints.add(var_name)
                    
                    # ✅ NUEVO: Extraer número de breakpoint y registrarlo
                    bkpt_number = self._extract_breakpoint_number_from_response(response)
                    if bkpt_number:
                        self.register_watchpoint(bkpt_number, var_name)
                    
                    print(f"Watchpoint configurado para '{var_name}' (#{bkpt_number})")
                    
            except Exception as e:
                print(f"Error configurando watchpoint para {var_name}: {e}")

    def _extract_breakpoint_number_from_response(self, response):
        """Extrae el número de breakpoint de la respuesta de GDB"""
        try:
            for resp in response:
                if resp.get("message") == "done" and "payload" in resp:
                    bkpt_info = resp["payload"].get("bkpt", {})
                    return bkpt_info.get("number")
                elif resp.get("type") == "console":
                    # Para respuestas de consola como "Watchpoint 1: variable"
                    import re
                    payload = resp.get("payload", "")
                    match = re.search(r'Watchpoint (\d+):', payload)
                    if match:
                        return match.group(1)
        except Exception as e:
            print(f"Error extrayendo número de breakpoint: {e}")
        return None

    def get_breakpoint_status(self):
        """Devuelve el estado actual de todos los breakpoints"""
        return {
            "user_breakpoints": {k: v for k, v in self.active_breakpoints.items() if v["type"] == "user_breakpoint"},
            "transparent_watchpoints": {k: v for k, v in self.active_breakpoints.items() if v["type"] == "transparent_watchpoint"},
            "total_count": len(self.active_breakpoints)
        }

    def _is_lamport_watchpoint_hit(self, stop_reason):
        """Determina si la parada fue SOLO por nuestro watchpoint"""
        try:
            # ✅ NUEVO: Manejar información detallada de breakpoint
            if isinstance(stop_reason, dict):
                reason = stop_reason.get("reason", "")
                breakpoint_info = stop_reason.get("breakpoint", {})
                
                # Si hay información de breakpoint específica
                if breakpoint_info:
                    bkpt_number = breakpoint_info.get("number")
                    print(f"🔍 Breakpoint #{bkpt_number} detectado")
                    
                    # Verificar si es uno de nuestros watchpoints transparentes
                    return self._is_transparent_watchpoint(bkpt_number)
                
                # Solo watchpoint sin breakpoint de usuario
                return "watchpoint" in reason.lower() and "breakpoint" not in reason.lower()
                
            elif isinstance(stop_reason, list):
                has_watchpoint = any("watchpoint" in reason.lower() for reason in stop_reason if isinstance(reason, str))
                has_breakpoint = any("breakpoint" in reason.lower() for reason in stop_reason if isinstance(reason, str))
                
                # Si hay breakpoint del usuario, NO es transparente
                if has_breakpoint and has_watchpoint:
                    return False  # No hacer auto-continue
                
                return has_watchpoint and not has_breakpoint
                
            elif isinstance(stop_reason, str):
                # Solo watchpoint, sin breakpoint
                return "watchpoint" in stop_reason.lower() and "breakpoint" not in stop_reason.lower()
                
            return False
        except:
            return False

    def _is_transparent_watchpoint(self, breakpoint_number):
        """Verifica si un breakpoint específico es uno de nuestros watchpoints transparentes"""
        try:
            if not breakpoint_number:
                return False
                
            # Obtener información del breakpoint
            bkpt_info = self.debugger.get_breakpoint_info(breakpoint_number)
            
            if bkpt_info and "BreakpointTable" in bkpt_info:
                breakpoints = bkpt_info["BreakpointTable"].get("body", [])
                
                for bkpt in breakpoints:
                    bkpt_data = bkpt.get("bkpt", {})
                    if bkpt_data.get("number") == str(breakpoint_number):
                        bkpt_type = bkpt_data.get("type", "")
                        what = bkpt_data.get("what", "")
                        
                        # Es nuestro watchpoint si es tipo "watchpoint" y vigila una de nuestras variables
                        if bkpt_type == "watchpoint" and any(var_name in what for var_name in self.global_variables):
                            print(f"✅ Watchpoint transparente confirmado: #{breakpoint_number} para '{what}'")
                            return True
                        
                        print(f"🔴 Breakpoint de usuario: #{breakpoint_number} (tipo: {bkpt_type})")
                        return False
            
            return False
            
        except Exception as e:
            print(f"Error verificando watchpoint transparente: {e}")
            return False

    def get_lamport_globals_structure(self):
        """Genera la estructura de globals para el diagrama de Lamport"""
        return self.global_variables