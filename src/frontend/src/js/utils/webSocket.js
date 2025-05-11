import $  from "jquery";
import io from "socket.io-client";
import { updateTerminal } from "../editor/outputTerminal";
import { RunColorManager } from "./uiManager.js";

let compiled = false;
let socket;

export const getSocket = () => {
    return socket;
}

export const getCompiled = () => {
    return compiled;
}

// Inicializar Socket.IO
export function initializeSocket() {
    // Conectar al WebSocket usando la URL actual (para que funcione con el proxy)
    const currentUrl = window.location.origin; // Obtiene http(s)://hostname:port
    console.log("Conectando a WebSocket en:", currentUrl);
    
    socket = io(currentUrl); // Esto conectará al mismo host/puerto donde se está sirviendo la página
    
    // Manejar la conexión exitosa
    socket.on("connect", () => {
        console.log("Conectado al servidor WebSocket");
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
            updateTerminal(response.result);
            compiled = true;
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
        // Aquí procesarías la respuesta según el tipo de acción
        // Por ejemplo, actualizar UI, mostrar variables, etc.
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

function runExecution() {
    console.log("Ejecutando con depurador...");
    socket.emit("run_debug");
}

function continueExecution() {
    socket.emit("continue_debug");
}

function reverseContinueExecution() {
    socket.emit("reverse_debug");
}

function stepOverExecution() {
    socket.emit("step_over", { thread_id: null });
}

function reverseStepOverExecution() {
    socket.emit("reverse_step_over", { thread_id: null });
}

function stepIntoExecution() {
    socket.emit("step_into", { thread_id: null });
}

function reverseStepIntoExecution() {
    socket.emit("reverse_step_into", { thread_id: null });
}

function stepOutExecution() {
    socket.emit("step_out", { thread_id: null });
}

function reverseStepOutExecution() {
    socket.emit("reverse_step_out", { thread_id: null });
}