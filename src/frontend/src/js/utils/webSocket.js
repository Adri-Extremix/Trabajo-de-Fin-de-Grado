import $  from "jquery";
import io from "socket.io-client";
import { updateTerminal } from "../editor/outputTerminal";
import { RunColorManager } from "./uiManager.js";
// No importamos directamente para evitar dependencia circular
let debuggerModule = null;

let compiled = false;
let socket;
let editorChangedSinceCompilation = false; // Variable para rastrear cambios en el editor

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
        // Importamos dinámicamente el módulo del depurador
        import("../debugger/debugger.js")
            .then((module) => {
                // Guardamos la referencia al módulo para futuro uso
                debuggerModule = module;
                // Procesamos la respuesta con la función handleDebuggerResponse
                module.handleDebuggerResponse(response);
            })
            .catch((error) => {
                console.error(
                    "Error al cargar el módulo de depuración:",
                    error
                );
                // Si hay un error, al menos quitamos el estado de carga
                $(".ThreadContent")
                    .empty()
                    .append(
                        '<div class="ThreadVisual"><div class="ThreadCount">Error al cargar el depurador</div></div>'
                    );
                $("#CodeShards")
                    .empty()
                    .append(
                        '<div class="CodeShard"><div class="CodeShard-Header">Error</div><div class="CodeShard-Content">No se pudo cargar el depurador.</div></div>'
                    );
            });
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

// Función auxiliar para cargar el módulo del depurador y mostrar el estado de carga
function showLoadingState() {
    // Si ya tenemos el módulo cargado, lo usamos directamente
    if (debuggerModule) {
        debuggerModule.showDebuggingStatus();
        return;
    }

    // Si no, importamos el módulo dinámicamente
    import("../debugger/debugger.js")
        .then((module) => {
            debuggerModule = module;
            module.showDebuggingStatus();
        })
        .catch((error) => {
            console.error("Error al cargar el módulo de depuración:", error);
            // Fallback manual si falla la importación
            $(".ThreadContent").empty().append(`
                <div class="ThreadVisual loading">
                    <div class="ThreadCount">Procesando...</div>
                    <div class="ThreadList">
                        <div class="LoadingIndicator">
                            <div class="LoadingSpinner"></div>
                            <div class="LoadingMessage">Depurando...</div>
                        </div>
                    </div>
                </div>
            `);

            $("#CodeShards")
                .empty()
                .append(
                    '<div class="CodeShard loading">' +
                        '<div class="CodeShard-Header">Depurando...</div>' +
                        '<div class="CodeShard-Content LoadingContent">' +
                        '<div class="LoadingSpinner"></div>' +
                        "<div>Esperando respuesta del depurador...</div>" +
                        "</div>" +
                        "</div>"
                );
        });
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
    socket.emit("step_over", { thread_id: null });
}

function reverseStepOverExecution() {
    showLoadingState();
    socket.emit("reverse_step_over", { thread_id: null });
}

function stepIntoExecution() {
    showLoadingState();
    socket.emit("step_into", { thread_id: null });
}

function reverseStepIntoExecution() {
    showLoadingState();
    socket.emit("reverse_step_into", { thread_id: null });
}

function stepOutExecution() {
    showLoadingState();
    socket.emit("step_out", { thread_id: null });
}

function reverseStepOutExecution() {
    showLoadingState();
    socket.emit("reverse_step_out", { thread_id: null });
}