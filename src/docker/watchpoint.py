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
        """Inicializar variables globales desde GDB"""
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
                                
        except Exception as e:
            print(f"Error inicializando variables globales: {e}")

    def update_global_variables(self, thread_info=None):
        """Actualizar valores y detectar cambios para el historial"""
        try:
            for var_name in self.global_variables:
                # Obtener valor actual
                value_response = self.debugger._gdb_write(f"-data-evaluate-expression {var_name}")
                if value_response and value_response[0].get("message") == "done":
                    new_value = value_response[0]["payload"].get("value")
                    old_value = self.global_variables[var_name]["current_value"]
                    
                    # Si cambió, agregar al historial
                    if new_value != old_value:
                        if thread_info:
                            current_thread = thread_info.get("current-thread-id", "1")
                        else:
                            # Obtener thread info si no se proporciona usando el método centralizado
                            thread_response = self.debugger.get_thread_info()
                            if thread_response and thread_response[-1].get("message") == "done":
                                current_thread = thread_response[-1]["payload"].get("current-thread-id", "1")
                            else:
                                current_thread = "1"
                        
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
            print(f"Error actualizando variables: {e}")

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
                

                if has_breakpoint and has_watchpoint:
                    print("Watchpoint + Breakpoint simultáneos → Priorizar breakpoint del usuario")
                    return False  # No hacer auto-continue
                
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