class LamportWatchpointManager:
    def __init__(self, debugger):
        self.debugger = debugger
        self.lamport_watchpoints = set()  # IDs de nuestros watchpoints
        self.user_breakpoints = set()     # Breakpoints del usuario
        self.lamport_events = []
        self.is_transparent_mode = True
        
    def setup_transparent_watchpoints(self, variables):
        """Configura watchpoints que no interfieren con el debugging normal"""
        print(f"🔍 Configurando watchpoints transparentes para: {variables}")
        
        for var_name in variables:
            try:
                # Configurar watchpoint
                response = self.debugger._gdb_write(f"watch {var_name}")
                
                if response and len(response) > 0:
                    # Extraer el ID del watchpoint de la respuesta de GDB
                    watchpoint_id = self._extract_watchpoint_id(response)
                    if watchpoint_id:
                        self.lamport_watchpoints.add(watchpoint_id)
                        print(f"✅ Watchpoint transparente {watchpoint_id} para '{var_name}'")
                        
            except Exception as e:
                print(f"❌ Error configurando watchpoint para {var_name}: {e}")
    
    def handle_stop_event(self, stop_reason, location_info):
        """Maneja eventos de parada para determinar si continuar automáticamente"""
        
        if self._is_lamport_watchpoint_hit(stop_reason):
            # Es nuestro watchpoint - capturar evento y continuar transparentemente
            event = self._capture_lamport_event(location_info)
            self.lamport_events.append(event)
            
            print(f"📊 Evento Lamport capturado: {event['variable']} = {event['new_value']}")
            
            if self.is_transparent_mode:
                # Continuar automáticamente sin que el usuario se entere
                print("🏃 Auto-continuando (watchpoint transparente)")
                return self._auto_continue()
            else:
                # Modo manual - parar y notificar al usuario
                return "LAMPORT_WATCHPOINT_HIT"
                
        elif self._is_user_breakpoint(stop_reason):
            # Es breakpoint del usuario - parar normalmente
            print(f"🛑 Breakpoint del usuario alcanzado")
            return "USER_BREAKPOINT_HIT"
            
        else:
            # Otra razón de parada
            return "OTHER_STOP_REASON"
    
    def _is_lamport_watchpoint_hit(self, stop_reason):
        """Determina si la parada fue por nuestro watchpoint"""
        if "watchpoint" in stop_reason.lower():
            # Extraer ID del watchpoint de la razón de parada
            watchpoint_id = self._extract_watchpoint_id_from_stop(stop_reason)
            return watchpoint_id in self.lamport_watchpoints
        return False
    
    def _auto_continue(self):
        """Continúa automáticamente después de capturar evento de watchpoint"""
        try:
            # Continuar sin que el usuario note la parada
            continue_response = self.debugger._gdb_write("-exec-continue")
            return continue_response
        except Exception as e:
            print(f"❌ Error en auto-continue: {e}")
            return None
    
    def _capture_lamport_event(self, location_info):
        """Captura información del evento para el diagrama de Lamport"""
        # Obtener información del hilo actual
        thread_info = self.debugger.get_thread_info()
        current_thread = thread_info[-1]["payload"].get("current-thread-id") if thread_info else "unknown"
        
        # Obtener valor actual de la variable
        # (aquí puedes implementar lógica para extraer el valor exacto)
        
        return {
            "thread_id": str(current_thread),
            "timestamp": time.time(),
            "variable": "extracted_var_name",  # Extraer del contexto
            "old_value": "old_val",           # Valor anterior
            "new_value": "new_val",           # Valor nuevo
            "line": location_info.get("line", "unknown"),
            "file": location_info.get("file", "unknown")
        }
    
    def _get_current_stop_reason(self):
        """Obtiene la razón de la parada actual"""
        try:
            # Obtener información del estado actual
            info_response = self._gdb_write("-exec-interrupt", timeout_sec=1)
            # Analizar respuesta para encontrar razón de parada
            # Implementar parsing específico según formato de respuesta de GDB
            return self._parse_stop_reason(info_response)
        except:
            return "unknown"

    def _get_current_location_info(self):
        """Obtiene información de ubicación actual"""
        try:
            frame_info = self.info_frame()
            if frame_info and "frame" in frame_info[0]["payload"]:
                frame = frame_info[0]["payload"]["frame"]
                return {
                    "line": frame.get("line"),
                    "file": frame.get("fullname"),
                    "function": frame.get("func")
                }
        except:
            pass
        return {"line": "unknown", "file": "unknown", "function": "unknown"}

    def _parse_stop_reason(self, gdb_response):
        """Parsea la respuesta de GDB para extraer razón de parada"""
        if not gdb_response:
            return "unknown"
        
        for response in gdb_response:
            message = response.get("message", "")
            payload = response.get("payload", {})
            
            # Buscar indicadores de watchpoint
            if "watchpoint" in message.lower():
                return f"watchpoint_{payload.get('bkptno', 'unknown')}"
            elif "breakpoint" in message.lower():
                return f"breakpoint_{payload.get('bkptno', 'unknown')}"
            elif "stopped" in message.lower():
                reason = payload.get("reason", "")
                if "watchpoint-trigger" in reason:
                    return f"watchpoint_{payload.get('bkptno', 'unknown')}"
                elif "breakpoint-hit" in reason:
                    return f"breakpoint_{payload.get('bkptno', 'unknown')}"
        
        return "unknown"