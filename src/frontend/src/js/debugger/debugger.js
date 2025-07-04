import $ from "jquery";
import { EditorState, StateField } from "@codemirror/state";
import { EditorView, Decoration, lineNumbers } from "@codemirror/view";
import { basicSetup } from "codemirror";
import { cpp } from "@codemirror/lang-cpp";
import { oneDark } from "@codemirror/theme-one-dark";
import { setActiveThreadId } from "../utils/webSocket.js";

// CORRECCIÓN: Usar el prefijo url: para forzar URLs como strings
import stepOverIcon from "url:../../../images/arrow-trend-up-solid.svg";
import stepOutIcon from "url:../../../images/arrow-turn-up-solid.svg";
import stepIntoIcon from "url:../../../images/arrow-turn-down-solid.svg";

// Función para mostrar un mensaje de error en los contenedores
function showDebuggerError(
    message = "No se pudo obtener información de los hilos. La ejecución ha terminado o ha ocurrido un error."
) {
    // Mostrar mensaje de error en el contenedor de código
    $("#CodeShards").empty().append(`
        <div class="ThreadItem error">
            <div class="ThreadItemHeader">
                <div class="ThreadInfo">
                    <div class="ThreadName">Error de depuración</div>
                </div>
            </div>
            <div class="ThreadVariables">
                <p>${message}</p>
            </div>
        </div>
    `);

    // Actualizar la vista de variables con un mensaje de error
    updateThreadVisual({});
    updateCodeShards({});
}

// Importamos las funciones para crear y configurar los controles de hilo
import { setupThreadControlEvents } from "./debugControllers.js";

// Importar la función para obtener el modo de debug
import { getLastCompiledDebugMode } from "../utils/webSocket.js";

// Función para actualizar la visualización de código (CodeShards)
function updateCodeShards(threads) {
    const codeShardsContainer = $("#CodeShards");
    codeShardsContainer.empty();

    const threadCount = Object.keys(threads).length;

    // Si no hay hilos, mostrar mensaje informativo
    if (threadCount === 0) {
        codeShardsContainer.append(showNoThreadsMessage());
        return;
    }

    // ✅ OBTENER EL MODO DE DEBUG
    const debugMode = getLastCompiledDebugMode();

    // Crear un CodeShard por cada hilo
    Object.keys(threads).forEach((threadId, index) => {
        const thread = threads[threadId];

        // Crear el elemento CodeShard con estilo de ThreadItem
        const codeShard = $(
            `<div class="ThreadItem" data-thread-id="${threadId}"></div>`
        );

        // Generar información para el título del hilo (usar threadId real)
        let threadTitle = `Hilo ${threadId}`;
        let threadInfo = "";

        if (thread.function) {
            threadInfo = `${thread.function}`;
        }
        if (thread.line) {
            threadInfo += ` (línea ${thread.line})`;
        }

        // ✅ CONTROLES DE THREAD SOLO EN MODO GDB
        let threadControlsHtml = "";
        if (debugMode === "gdb") {
            threadControlsHtml = `
                <div class="ThreadControls">
                    <button class="ThreadButton thread-step-over" data-thread-id="${threadId}" title="Step Over">
                        <img src="${stepOverIcon}" alt="Step Over">
                    </button>
                    <button class="ThreadButton thread-step-out" data-thread-id="${threadId}" title="Step Out">
                        <img src="${stepOutIcon}" alt="Step Out">
                    </button>
                    <button class="ThreadButton thread-step-into" data-thread-id="${threadId}" title="Step Into">
                        <img src="${stepIntoIcon}" alt="Step Into">
                    </button>
                </div>
            `;
        }

        // Añadir encabezado con estilo de ThreadItem
        codeShard.append(`
            <div class="ThreadItemHeader">
                <div class="ThreadInfo">
                    <div class="ThreadName">${threadTitle}</div>
                    <div class="ThreadFunction">${
                        threadInfo || "Sin información disponible"
                    }</div>
                </div>
                ${threadControlsHtml}
            </div>
        `);

        // Añadir el código con formato y resaltar la línea actual usando CodeMirror
        if (thread.code) {
            const currentLine = parseInt(thread.line || 1);

            // Crear un contenedor para el editor CodeMirror
            const codeContainer = $('<div class="CodeShard-Content"></div>');
            codeShard.append(codeContainer);

            // Crear un ID único para este editor
            const editorId = `codemirror-${threadId}`;
            codeContainer.attr("id", editorId);

            // Obtener el número de línea inicial del fragmento de código
            let lineOffset = 1; // Valor predeterminado
            if (thread.start_line) {
                lineOffset = parseInt(thread.start_line);
            }

            // Calcular la línea relativa dentro del fragmento de código
            const relativeLineNumber = currentLine - lineOffset + 1;

            setTimeout(() => {
                try {
                    // Crear una decoración para la línea actual (ajustada al offset)
                    const currentLineHighlight = Decoration.line({
                        attributes: { class: "cm-breakpointLine" },
                    });

                    // Definir el campo de estado para la línea actual
                    const currentLineField = StateField.define({
                        create() {
                            return Decoration.none;
                        },
                        update(decorations, tr) {
                            const doc = tr.state.doc;

                            // Solo aplicar si la línea está dentro del rango del fragmento
                            if (
                                relativeLineNumber > 0 &&
                                relativeLineNumber <= doc.lines
                            ) {
                                const linePos =
                                    doc.line(relativeLineNumber).from;
                                return Decoration.set([
                                    currentLineHighlight.range(linePos),
                                ]);
                            }
                            return Decoration.none;
                        },
                        provide: (f) => EditorView.decorations.from(f),
                    });

                    // Crear el editor
                    const view = new EditorView({
                        state: EditorState.create({
                            doc: thread.code,
                            extensions: [
                                basicSetup,
                                cpp(),
                                oneDark,
                                currentLineField,
                                EditorView.editable.of(false),
                                lineNumbers({
                                    // Personalizar los números de línea para mostrar los números reales
                                    formatNumber: (lineNo) =>
                                        String(lineNo + lineOffset - 1),
                                }),
                                EditorView.theme({
                                    // No aplicamos ningún estilo especial a la línea actual
                                    // para que se muestre igual que las demás
                                }),
                            ],
                        }),
                        parent: document.getElementById(editorId),
                    });

                    // Scroll a la línea actual
                    if (relativeLineNumber > 0) {
                        try {
                            const line =
                                view.state.doc.line(relativeLineNumber);
                            view.dispatch({
                                effects: EditorView.scrollIntoView(line.from, {
                                    y: "center",
                                }),
                            });
                        } catch (e) {
                            console.warn(
                                "No se pudo hacer scroll a la línea actual:",
                                e
                            );
                        }
                    }
                } catch (error) {
                    console.error(
                        "Error al crear el editor CodeMirror:",
                        error
                    );
                    $(`#${editorId}`).html(
                        `<div class="CodeShard-Content-Error">No se pudo cargar el editor de código. Revise la consola para más detalles.</div>`
                    );
                }
            }, 100);
        } else {
            codeShard.append(
                '<div class="ThreadVariables"><p>No hay código disponible para mostrar</p></div>'
            );
        }

        codeShardsContainer.append(codeShard);
    });

    // ✅ SOLO configurar eventos de thread si estamos en modo GDB
    setupThreadControlEvents();

    // Añadir event listener para hacer clic en CodeShards y actualizar el thread activo
    $(".CodeShard").on("click", function () {
        const threadId = $(this).data("thread-id");
        if (threadId) {
            setActiveThreadId(threadId);
            console.log(
                "Thread activo actualizado por selección de CodeShard:",
                threadId
            );

            // Resaltar visualmente el CodeShard seleccionado
            $(".CodeShard").removeClass("highlighted");
            $(".ThreadItem").removeClass("highlighted");

            $(this).addClass("highlighted");
            $(`.ThreadItem[data-thread-id="${threadId}"]`).addClass(
                "highlighted"
            );
        }
    });
}

// Función para manejar la respuesta del depurador
export function handleDebuggerResponse(response) {
    // Verificar que haya resultado en la respuesta
    if (!response || !response.result) {
        console.error("Respuesta de depuración inválida:", response);
        showDebuggerError();
        return;
    }

    const result = response.result;

    // ✅ NUEVO FORMATO: Extraer threads y globals del resultado
    const threads = result.threads || {};
    const globals = result.globals || {};

    const threadCount = Object.keys(threads).length;

    console.log(`Procesando respuesta de depuración con ${threadCount} hilos`);
    console.log("Variables globales recibidas:", globals);

    // Actualizar el thread activo si hay hilos disponibles
    if (threadCount > 0) {
        const threadIds = Object.keys(threads);
        // Priorizar el primer hilo disponible como thread activo si no hay uno establecido
        const firstThreadId = threadIds[0];
        setActiveThreadId(firstThreadId);
        console.log(
            "Thread activo establecido automáticamente:",
            firstThreadId
        );
    }

    // Actualizar primero la visualización de hilos
    updateThreadVisual(threads);

    // Actualizar la visualización del código
    updateCodeShards(threads);

    // ✅ NUEVO: Actualizar visualización de variables globales
    updateGlobalVariables(globals);

    // Inicializar los eventos para los botones de control de hilo
    // Esto garantiza que los botones funcionen después de cada actualización
    setTimeout(() => {
        setupThreadControlEvents();
    }, 100);
}

// Función para mostrar un mensaje cuando no hay hilos activos
function showNoThreadsMessage() {
    const noThreadsMessage = `
        <div class="ThreadVisual">
            <div class="ThreadCount">No hay hilos activos</div>
            <div class="ThreadList empty">
                    <div class="ThreadVariables">
                        <p>La ejecución ha terminado o no se ha iniciado.</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    return noThreadsMessage;
}

// Función para actualizar la visualización de hilos en el panel de variables
function updateThreadVisual(threads) {
    const threadContent = $(".ThreadContent");
    threadContent.empty();

    const threadCount = Object.keys(threads).length;

    // Si no hay hilos, mostrar mensaje informativo en ambos contenedores
    if (threadCount === 0) {
        // Mensaje para ThreadContent
        threadContent.append(showNoThreadsMessage());
        return;
    }

    const threadVisual = $(`                <div class="ThreadVisual">
        <div class="ThreadCount">Hilos activos: ${threadCount}</div>
    </div>`);

    // Crear representación gráfica de los hilos
    const threadList = $('<div class="ThreadList"></div>');

    // Ordenar los hilos por ID para una visualización consistente
    const sortedThreadIds = Object.keys(threads).sort();

    sortedThreadIds.forEach((threadId, index) => {
        const thread = threads[threadId];

        // Generar información adicional sobre el hilo
        let threadInfo = "";
        if (thread.function) {
            threadInfo = `${thread.function}`;
        }
        if (thread.line) {
            threadInfo += ` (línea ${thread.line})`;
        }

        const threadItem =
            $(`<div class="ThreadItem" data-thread-id="${threadId}">
            <div class="ThreadItemHeader">
                <div class="ThreadInfo">
                    <div class="ThreadName">Hilo ${threadId}</div>
                    <div class="ThreadFunction">${
                        threadInfo || "Sin información disponible"
                    }</div>
                </div>
            </div>
        </div>`);

        // Añadir sección de variables en el área Visual
        if (thread.variables && Object.keys(thread.variables).length > 0) {
            const varsContainer = $('<div class="ThreadVariables"></div>');
            const varTable = $('<table class="VarTable"></table>');

            Object.keys(thread.variables).forEach((varName) => {
                varTable.append(`<tr>
                    <td class="VarName">${varName}</td>
                    <td class="VarValue">${thread.variables[varName]}</td>
                </tr>`);
            });

            varsContainer.append(varTable);
            threadItem.append(varsContainer);
        }

        threadList.append(threadItem);
    });

    threadVisual.append(threadList);
    threadContent.append(threadVisual);

    // Añadir event listener para resaltar el CodeShard correspondiente al hacer clic en un hilo
    $(".ThreadItem").on("click", function () {
        const threadId = $(this).data("thread-id");
        const isAlreadyHighlighted = $(this).hasClass("highlighted");

        // Actualizar el thread activo cuando se selecciona un hilo
        setActiveThreadId(threadId);
        console.log(
            "Thread activo actualizado por selección del usuario:",
            threadId
        );

        // Eliminar resaltado de todos los elementos
        $(".CodeShard").removeClass("highlighted");
        $(".ThreadItem").removeClass("highlighted");

        // Si no estaba resaltado previamente, resaltar elementos
        if (!isAlreadyHighlighted) {
            // Resaltar el CodeShard correspondiente
            $(`.CodeShard[data-thread-id="${threadId}"]`).addClass(
                "highlighted"
            );

            // Resaltar también el elemento de hilo seleccionado
            $(this).addClass("highlighted");

            // Hacer scroll al CodeShard correspondiente
            const targetShard = $(
                `.CodeShard[data-thread-id="${threadId}"]`
            )[0];
            if (targetShard) {
                targetShard.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest",
                });
            }
        }
    });
}

// Función para mostrar el estado "Depurando..." mientras se espera respuesta
export function showDebuggingStatus() {
    console.log("Mostrando estado de depuración...");

    // Primero nos aseguramos de que los contenedores existen
    const threadContainer = $(".ThreadContent");
    const codeContainer = $("#CodeShards");

    if (threadContainer.length === 0 || codeContainer.length === 0) {
        console.error(
            "Error: No se encontraron los contenedores para mostrar el estado de depuración"
        );
        return;
    }

    // Actualizar la vista de hilos con un mensaje de carga
    threadContainer.empty().html(`
        <div class="LoadingContainer">
            <div class="LoadingHeader">Depurando...</div>
            <div class="LoadingWrapper">
                <div class="LoadingIndicator">
                    <div class="LoadingSpinner"></div>
                    <div class="LoadingMessage">Recolectando datos del depurador...</div>
                </div>
            </div>
        </div>
    `);

    // También mostrar estado de depuración en el contenedor de código
    codeContainer.empty().html(`
        <div class="LoadingContainer">
            <div class="LoadingHeader">Depurando...</div>
            <div class="LoadingWrapper">
                <div class="LoadingIndicator">
                    <div class="LoadingSpinner"></div>
                    <div class="LoadingMessage">Recolectando datos del depurador...</div>
                </div>
            </div>
        </div>
    `);

    console.log("Estado de depuración mostrado correctamente");
}

// ✅ NUEVA FUNCIÓN: Actualizar visualización de variables globales de Lamport
function updateGlobalVariables(globals) {
    console.log("Actualizando variables globales:", globals);

    // ✅ Guardar los datos globales para uso en event listeners
    window.currentGlobalVariablesData = globals;

    // ✅ CORRECTO: Buscar el Visual que contiene ThreadContent
    const threadVisualContainer = $(".ThreadContent").closest(".Visual");

    // Buscar el contenedor de variables globales o crearlo si no existe
    let globalContainer = $("#GlobalVariables");

    if (globalContainer.length === 0) {
        // ✅ CORRECTO: Crear el contenedor DENTRO del Visual, ANTES de ThreadContent
        if (threadVisualContainer.length > 0) {
            // Insertar las variables globales antes de ThreadContent
            $(".ThreadContent").before(`
                <div id="GlobalVariables" class="GlobalVariablesContainer">
                    <div class="GlobalVariablesTitle">Variables Globales</div>
                    <div class="GlobalVariablesList"></div>
                </div>
            `);
            globalContainer = $("#GlobalVariables");
        } else {
            console.warn(
                "No se encontró el Visual que contiene ThreadContent para mostrar variables globales"
            );
            return;
        }
    }

    const variablesList = globalContainer.find(".GlobalVariablesList");
    variablesList.empty();

    const variableCount = Object.keys(globals).length;

    if (variableCount === 0) {
        variablesList.html(`
            <div class="NoGlobalVariables">
                <p>No hay variables globales monitoreadas</p>
            </div>
        `);
        return;
    }

    // Mostrar cada variable global con su historial
    Object.keys(globals).forEach((varName) => {
        const variable = globals[varName];
        const currentValue = variable.current_value || "undefined";
        const currentType = variable.current_type || "unknown";
        const history = variable.history || [];

        const variableItem = $(`
            <div class="GlobalVariableItem" data-variable="${varName}">
                <div class="GlobalVariableHeader">
                    <span class="GlobalVariableName">${varName}</span>
                    <span class="GlobalVariableType">${currentType}</span>
                    <span class="GlobalVariableValue">${currentValue}</span>
                </div>
                <div class="GlobalVariableHistory">
                    <div class="HistoryTitle">Historial de cambios (Lamport):</div>
                    <div class="HistoryList"></div>
                </div>
            </div>
        `);

        const historyList = variableItem.find(".HistoryList");

        if (history.length === 0) {
            historyList.html(
                '<div class="HistoryEmpty">Sin cambios registrados</div>'
            );
        } else {
            // Mostrar los últimos 5 cambios, más recientes primero
            const recentHistory = history.slice(-5).reverse();

            recentHistory.forEach((event, index) => {
                const timestamp = new Date(
                    event.timestamp
                ).toLocaleTimeString();
                const historyItem = $(`
                    <div class="HistoryItem" data-lamport="${event.lamport_time}">
                        <span class="HistoryLamport">T${event.lamport_time}</span>
                        <span class="HistoryThread">Hilo ${event.thread_id}</span>
                        <span class="HistoryValue">${event.value}</span>
                        <span class="HistoryTime">${timestamp}</span>
                    </div>
                `);

                historyList.append(historyItem);
            });

            // Si hay más de 5 eventos, mostrar un indicador clickeable
            if (history.length > 5) {
                historyList.append(`
                    <div class="HistoryMore" data-variable="${varName}" data-total-events="${
                    history.length
                }">
                        <span class="HistoryMoreLink">... y ${
                            history.length - 5
                        } cambios más (click para ver todos)</span>
                    </div>
                `);
            }
        }

        variablesList.append(variableItem);
    });
}

// Función para alternar la visualización del historial de una variable
function toggleVariableHistory(varName) {
    const variableItem = $(`.GlobalVariableItem[data-variable="${varName}"]`);
    const historyDiv = variableItem.find(".GlobalVariableHistory");

    historyDiv.slideToggle(200);
}

// Función para expandir el historial completo de una variable
function expandVariableHistory(varName, globals) {
    const variable = globals[varName];
    if (!variable || !variable.history) return;

    const variableItem = $(`.GlobalVariableItem[data-variable="${varName}"]`);
    const historyList = variableItem.find(".HistoryList");

    // Limpiar el historial actual
    historyList.empty();

    // Mostrar TODOS los eventos, más recientes primero
    const fullHistory = variable.history.slice().reverse();

    fullHistory.forEach((event, index) => {
        const timestamp = new Date(event.timestamp).toLocaleTimeString();
        const historyItem = $(`
            <div class="HistoryItem" data-lamport="${event.lamport_time}">
                <span class="HistoryLamport">T${event.lamport_time}</span>
                <span class="HistoryThread">Hilo ${event.thread_id}</span>
                <span class="HistoryValue">${event.value}</span>
                <span class="HistoryTime">${timestamp}</span>
            </div>
        `);

        historyList.append(historyItem);
    });

    // Agregar botón para colapsar de nuevo
    historyList.append(`
        <div class="HistoryCollapse" data-variable="${varName}">
            <span class="HistoryCollapseLink">⬆ Mostrar solo los últimos 5 cambios</span>
        </div>
    `);
}

// Función para colapsar el historial a solo los últimos 5
function collapseVariableHistory(varName, globals) {
    const variable = globals[varName];
    if (!variable || !variable.history) return;

    const variableItem = $(`.GlobalVariableItem[data-variable="${varName}"]`);
    const historyList = variableItem.find(".HistoryList");

    // Limpiar el historial actual
    historyList.empty();

    const history = variable.history;

    if (history.length === 0) {
        historyList.html(
            '<div class="HistoryEmpty">Sin cambios registrados</div>'
        );
        return;
    }

    // Mostrar solo los últimos 5 cambios, más recientes primero
    const recentHistory = history.slice(-5).reverse();

    recentHistory.forEach((event, index) => {
        const timestamp = new Date(event.timestamp).toLocaleTimeString();
        const historyItem = $(`
            <div class="HistoryItem" data-lamport="${event.lamport_time}">
                <span class="HistoryLamport">T${event.lamport_time}</span>
                <span class="HistoryThread">Hilo ${event.thread_id}</span>
                <span class="HistoryValue">${event.value}</span>
                <span class="HistoryTime">${timestamp}</span>
            </div>
        `);

        historyList.append(historyItem);
    });

    // Si hay más de 5 eventos, mostrar el indicador clickeable de nuevo
    if (history.length > 5) {
        historyList.append(`
            <div class="HistoryMore" data-variable="${varName}" data-total-events="${
            history.length
        }">
                <span class="HistoryMoreLink">... y ${
                    history.length - 5
                } cambios más (click para ver todos)</span>
            </div>
        `);
    }
}

// Event listener para el click en variables globales
$(document).on("click", ".GlobalVariableHeader", function () {
    const varName = $(this).closest(".GlobalVariableItem").data("variable");
    toggleVariableHistory(varName);
});

// ✅ NUEVO: Event listener para expandir historial completo
$(document).on("click", ".HistoryMoreLink", function () {
    const varName = $(this).closest(".HistoryMore").data("variable");

    // Necesitamos acceso a los datos globales actuales
    // Los guardamos temporalmente cuando se actualiza updateGlobalVariables
    const currentGlobals = window.currentGlobalVariablesData || {};

    if (currentGlobals[varName]) {
        expandVariableHistory(varName, currentGlobals);
    }
});

// ✅ NUEVO: Event listener para colapsar historial
$(document).on("click", ".HistoryCollapseLink", function () {
    const varName = $(this).closest(".HistoryCollapse").data("variable");

    // Usar los datos globales actuales
    const currentGlobals = window.currentGlobalVariablesData || {};

    if (currentGlobals[varName]) {
        collapseVariableHistory(varName, currentGlobals);
    }
});
