import $  from "jquery";
import io from "socket.io-client";
import { updateTerminal } from "../editor/outputTerminal";
import { RunColorManager } from "./uiManager.js";
// Importación estática en lugar de dinámica
import { handleDebuggerResponse, showDebuggingStatus } from "../debugger/debugger.js";

let compiled = false;
let socket;
let editorChangedSinceCompilation = false; // Variable para rastrear cambios en el editor
let lastCompiledDebugMode = null; // Variable para almacenar el último modo de depuración compilado
// Almacenar información del hilo activo para optimizar operaciones de step
let activeThreadId = null;

export const getSocket = () => {
    return socket;
};

export const getCompiled = () => {
    return compiled;
};

export const getEditorChanged = () => {
    return editorChangedSinceCompilation;
};

export const setEditorChanged = (value) => {
    editorChangedSinceCompilation = value;
};

export const getLastCompiledDebugMode = () => {
    return lastCompiledDebugMode;
};

export const setLastCompiledDebugMode = (mode) => {
    lastCompiledDebugMode = mode;
};

export const getActiveThreadId = () => {
    return activeThreadId;
};

export const setActiveThreadId = (threadId) => {
    activeThreadId = threadId;
    console.log("Thread activo actualizado a:", threadId);
};

// Inicializar Socket.IO
export function initializeSocket() {
    // Conectar al WebSocket usando la URL actual (para que funcione con el proxy)
    const currentUrl = window.location.origin; // Obtiene http(s)://hostname:port
    console.log("Conectando a WebSocket en:", currentUrl);

    socket = io(currentUrl); // Esto conectará al mismo host/puerto donde se está sirviendo la página

    // Inicializar el valor de lastCompiledDebugMode con el valor que tenga el selector
    // Lo hacemos con setTimeout para asegurar que el DOM esté cargado
    setTimeout(() => {
        if (document.getElementById("debugMode")) {
            lastCompiledDebugMode = document.getElementById("debugMode").value;
            console.log("Modo de depuración inicial:", lastCompiledDebugMode);
        }
    }, 100);

    // Manejar la conexión exitosa
    socket.on("connect", () => {
        console.log("Conectado al servidor WebSocket");

        // Hacer el socket disponible globalmente para los controladores de depuración
        window.socket = socket;
    });

    // Manejar desconexiones
    socket.on("disconnect", () => {
        console.log("Desconectado del servidor WebSocket");
    });

    // Escuchar mensajes generales
    socket.on("message", (data) => {
        console.log("Mensaje recibido:", data);
    });

    // Escuchar respuestas de compilación
    socket.on("compile_response", (response) => {
        console.log("Respuesta de compilación:", response);
        if (response.error) {
            updateTerminal("Error: " + response.error);
            compiled = false;
        } else {
            // Limpiar terminal para mostrar claramente que hay una nueva compilación
            updateTerminal("Compilación completada con éxito.\n");
            // Añadir pequeña pausa para mostrar la transición
            setTimeout(() => {
                // Esta función continúa después de un breve delay
            }, 300);
            // Mostrar resultado de la compilación si existe
            if (response.result && response.result.trim()) {
                updateTerminal(response.result);
            }
            compiled = true;
            editorChangedSinceCompilation = false; // Resetear el indicador de cambios

            // Guardar el modo de depuración actual
            lastCompiledDebugMode = document.getElementById("debugMode").value;
            console.log("Modo de depuración guardado:", lastCompiledDebugMode);
        }

        // Actualizamos botones y slicer
        RunColorManager();
        $("#slicerToggle").prop("disabled", !compiled);
    });

    // Escuchar respuestas de ejecución
    socket.on("run_response", (response) => {
        console.log("Respuesta de ejecución:", response);
        if (response.error) {
            updateTerminal("Error: " + response.error);
        } else {
            updateTerminal(response.result);
        }
    });

    // Escuchar respuestas de depuración
    socket.on("debug_response", (response) => {
        console.log("Respuesta de depuración:", response);
        // Usar la función importada directamente
        handleDebuggerResponse(response);
    });

    // Registro de eventos para depurar problemas con los controles de hilo
    socket.on("connect", () => {
        console.log(
            "Socket conectado. Configurando event listeners de depuración."
        );
    });

    socket.on("debug_step_over_response", (response) => {
        console.log("Respuesta a debug_step_over:", response);
    });

    socket.on("debug_step_into_response", (response) => {
        console.log("Respuesta a debug_step_into:", response);
    });

    socket.on("debug_step_out_response", (response) => {
        console.log("Respuesta a debug_step_out:", response);
    });
}

export function bindingComunicactions() {
    $("#Debug-Run").on("click", runExecution);
    $("#Debug-Continue").on("click", continueExecution);
    $("#Debug-Reverse-Continue").on("click", reverseContinueExecution);
    $("#Debug-Step-Over").on("click", stepOverExecution);
    $("#Debug-Reverse-Step-Over").on("click", reverseStepOverExecution);
    $("#Debug-Step-Into").on("click", stepIntoExecution);
    $("#Debug-Reverse-Step-Into").on("click", reverseStepIntoExecution);
    $("#Debug-Step-Out").on("click", stepOutExecution);
    $("#Debug-Reverse-Step-Out").on("click", reverseStepOutExecution);
}

// Función auxiliar para mostrar el estado de carga
function showLoadingState() {
    // Usar la función importada directamente
    showDebuggingStatus();
}

function runExecution() {
    console.log("Ejecutando con depurador...");
    showLoadingState();
    socket.emit("run_debug");
}

function continueExecution() {
    showLoadingState();
    socket.emit("continue_debug");
}

function reverseContinueExecution() {
    showLoadingState();
    socket.emit("reverse_debug");
}

function stepOverExecution() {
    showLoadingState();
    // Obtener el modo de depuración actual
    const debugMode = getLastCompiledDebugMode();
    let thread_id = null;

    // Para modo GDB, usar el thread activo o el primer hilo disponible
    if (debugMode === "gdb") {
        // Priorizar el thread activo almacenado
        thread_id = activeThreadId;

        // Si no hay thread activo, usar el primer hilo disponible
        if (!thread_id) {
            const firstThread = $(".ThreadItem").first().data("thread-id");
            if (firstThread) {
                thread_id = firstThread;
                // Actualizar el thread activo para futuras operaciones
                setActiveThreadId(thread_id);
            }
        }

        console.log("Step Over ejecutándose en thread:", thread_id);
    }

    socket.emit("step_over", { thread_id: thread_id });
}

function reverseStepOverExecution() {
    showLoadingState();
    socket.emit("reverse_step_over", { thread_id: null });
}

function stepIntoExecution() {
    showLoadingState();
    // Obtener el modo de depuración actual
    const debugMode = getLastCompiledDebugMode();
    let thread_id = null;

    // Para modo GDB, usar el thread activo o el primer hilo disponible
    if (debugMode === "gdb") {
        // Priorizar el thread activo almacenado
        thread_id = activeThreadId;

        // Si no hay thread activo, usar el primer hilo disponible
        if (!thread_id) {
            const firstThread = $(".ThreadItem").first().data("thread-id");
            if (firstThread) {
                thread_id = firstThread;
                // Actualizar el thread activo para futuras operaciones
                setActiveThreadId(thread_id);
            }
        }

        console.log("Step Into ejecutándose en thread:", thread_id);
    }

    socket.emit("step_into", { thread_id: thread_id });
}

function reverseStepIntoExecution() {
    showLoadingState();
    socket.emit("reverse_step_into", { thread_id: null });
}

function stepOutExecution() {
    showLoadingState();
    // Obtener el modo de depuración actual
    const debugMode = getLastCompiledDebugMode();
    let thread_id = null;

    // Para modo GDB, usar el thread activo o el primer hilo disponible
    if (debugMode === "gdb") {
        // Priorizar el thread activo almacenado
        thread_id = activeThreadId;

        // Si no hay thread activo, usar el primer hilo disponible
        if (!thread_id) {
            const firstThread = $(".ThreadItem").first().data("thread-id");
            if (firstThread) {
                thread_id = firstThread;
                // Actualizar el thread activo para futuras operaciones
                setActiveThreadId(thread_id);
            }
        }

        console.log("Step Out ejecutándose en thread:", thread_id);
    }

    socket.emit("step_out", { thread_id: thread_id });
}

function reverseStepOutExecution() {
    showLoadingState();
    socket.emit("reverse_step_out", { thread_id: null });
}

// ========== FUNCIONES PARA BOTONES POR HILO ==========

/**
 * Ejecuta step over para un hilo específico
 * @param {string} threadId - ID del hilo
 */
export function threadStepOverExecution(threadId) {
    console.log("Thread Step Over para hilo:", threadId);
    
    if (!socket || !socket.connected) {
        console.error("El socket no está disponible o no está conectado");
        return false;
    }
    
    showLoadingState();
    console.log("Emitiendo evento step_over con thread_id:", threadId);
    socket.emit("step_over", { thread_id: threadId });
    
    // Actualizar el thread activo para futuras operaciones globales
    setActiveThreadId(threadId);
    return true;
}

/**
 * Ejecuta step into para un hilo específico
 * @param {string} threadId - ID del hilo
 */
export function threadStepIntoExecution(threadId) {
    console.log("Thread Step Into para hilo:", threadId);
    
    if (!socket || !socket.connected) {
        console.error("El socket no está disponible o no está conectado");
        return false;
    }
    
    showLoadingState();
    console.log("Emitiendo evento step_into con thread_id:", threadId);
    socket.emit("step_into", { thread_id: threadId });
    
    // Actualizar el thread activo para futuras operaciones globales
    setActiveThreadId(threadId);
    return true;
}

/**
 * Ejecuta step out para un hilo específico
 * @param {string} threadId - ID del hilo
 */
export function threadStepOutExecution(threadId) {
    console.log("Thread Step Out para hilo:", threadId);
    
    if (!socket || !socket.connected) {
        console.error("El socket no está disponible o no está conectado");
        return false;
    }
    
    showLoadingState();
    console.log("Emitiendo evento step_out con thread_id:", threadId);
    socket.emit("step_out", { thread_id: threadId });
    
    // Actualizar el thread activo para futuras operaciones globales
    setActiveThreadId(threadId);
    return true;
}