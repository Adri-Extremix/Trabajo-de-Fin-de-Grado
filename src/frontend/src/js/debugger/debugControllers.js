import $ from "jquery";
import { getLastCompiledDebugMode } from "../utils/webSocket.js";

/**
 * Actualiza la visibilidad de los botones de control de depuración según el modo seleccionado
 */
export function updateDebuggerControls() {
    const debugMode = getLastCompiledDebugMode();
    console.log("Actualizando controles de depuración para modo:", debugMode);

    // Para GDB (Estándar), mostrar solo los botones Run y Continue en la parte superior
    // y mostrar los controles de hilo en cada thread
    if (debugMode === "gdb") {
        // Ocultar botones de reverse y step en la parte superior
        $(".Reverse-Button").hide();
        $("#Debug-Step-Over, #Debug-Step-Out, #Debug-Step-Into").hide();
        
        // Mostrar controles por hilo
        $(".ThreadControls").show();
    } else {
        // Para RR (grabación), mostrar todos los botones en la parte superior
        // y ocultar los controles de hilo
        $(".Buttons button").show();
        
        // Ocultar controles por hilo
        $(".ThreadControls").hide();
    }
}

// La función createThreadControls ya no es necesaria ya que los controles están en el HTML

/**
 * Configura los event listeners para los botones de control de hilo
 */
export function setupThreadControlEvents() {
    console.log("Configurando eventos para botones de control de hilo");
    
    // Verificar que existen botones en el DOM antes de configurar eventos
    const stepOverButtons = $(".thread-step-over");
    const stepOutButtons = $(".thread-step-out");
    const stepIntoButtons = $(".thread-step-into");
    
    console.log(`Encontrados ${stepOverButtons.length} botones step-over`);
    console.log(`Encontrados ${stepOutButtons.length} botones step-out`);
    console.log(`Encontrados ${stepIntoButtons.length} botones step-into`);
    
    // Primero eliminamos cualquier evento previo para evitar duplicados
    $(document).off("click", ".thread-step-over");
    $(document).off("click", ".thread-step-out");
    $(document).off("click", ".thread-step-into");
    
    // Event listener para botón step over de hilo
    $(document).on("click", ".thread-step-over", function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const threadId = $(this).data("thread-id");
        console.log("Thread Step Over para hilo:", threadId);
        
        // Resaltamos visualmente que el botón ha sido pulsado
        $(this).addClass("active");
        setTimeout(() => $(this).removeClass("active"), 300);
        
        // Verificar que el socket está disponible
        const socket = window.socket;
        if (socket && socket.connected) {
            console.log("Emitiendo evento step_over con thread_id:", threadId);
            socket.emit("step_over", { thread_id: threadId });
        } else {
            console.error("El socket no está disponible o no está conectado");
        }
    });
    
    // Event listener para botón step out de hilo
    $(document).on("click", ".thread-step-out", function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const threadId = $(this).data("thread-id");
        console.log("Thread Step Out para hilo:", threadId);
        
        // Resaltamos visualmente que el botón ha sido pulsado
        $(this).addClass("active");
        setTimeout(() => $(this).removeClass("active"), 300);
        
        const socket = window.socket;
        if (socket && socket.connected) {
            console.log("Emitiendo evento step_out con thread_id:", threadId);
            socket.emit("step_out", { thread_id: threadId });
        } else {
            console.error("El socket no está disponible o no está conectado");
        }
    });
    
    // Event listener para botón step into de hilo
    $(document).on("click", ".thread-step-into", function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const threadId = $(this).data("thread-id");
        console.log("Thread Step Into para hilo:", threadId);
        
        // Resaltamos visualmente que el botón ha sido pulsado
        $(this).addClass("active");
        setTimeout(() => $(this).removeClass("active"), 300);
        
        const socket = window.socket;
        if (socket && socket.connected) {
            console.log("Emitiendo evento step_into con thread_id:", threadId);
            socket.emit("step_into", { thread_id: threadId });
        } else {
            console.error("El socket no está disponible o no está conectado");
        }
    });

    console.log("Eventos de control de hilos configurados correctamente");
}
