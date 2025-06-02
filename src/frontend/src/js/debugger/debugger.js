import $ from "jquery";
// Importaciones de CodeMirror de forma directa
import { EditorState, StateField } from "@codemirror/state";
import { EditorView, Decoration, lineNumbers } from "@codemirror/view";
import { basicSetup } from "codemirror";
import { cpp } from "@codemirror/lang-cpp";
import { oneDark } from "@codemirror/theme-one-dark";

// Función para generar los CodeShards dinámicamente basados en la respuesta del debugger
export function handleDebuggerResponse(response) {
    // Verificar que haya resultado en la respuesta
    if (!response || !response.result) {
        console.error("Respuesta de depuración inválida:", response);

        // Mostrar mensaje de error en los contenedores
        $("#CodeShards").empty().append(`
                <div class="ThreadItem error">
                    <div class="ThreadItemHeader">
                        <div class="ThreadInfo">
                            <div class="ThreadStateIcon">⚠️</div>
                            <div class="ThreadName">Error de depuración</div>
                        </div>
                    </div>
                    <div class="ThreadVariables">
                        <p>No se pudo obtener información de los hilos. La ejecución ha terminado o ha ocurrido un error.</p>
                    </div>
                </div>
            `);

        // Actualizar la vista de variables con un mensaje de error
        updateThreadVisual({});
        return;
    }

    const threads = response.result;
    const threadCount = Object.keys(threads).length;

    console.log(`Procesando respuesta de depuración con ${threadCount} hilos`);

    // Limpiar contenedor de CodeShards
    $("#CodeShards").empty();

    // Si no hay hilos activos, mostrar un mensaje
    if (threadCount === 0) {
        $("#CodeShards").append(`
            <div class="ThreadVisual">
                <div class="ThreadCount">No hay hilos activos</div>
                <div class="ThreadList empty">
                    <div class="EmptyThreadMessage">La ejecución ha terminado o no se ha iniciado.</div>
                </div>
            </div>
        `);

        // También actualizar el contenido de hilos en la vista visual para el caso de 0 hilos
        updateThreadVisual({});
        return;
    }

    // Crear un CodeShard por cada hilo
    Object.keys(threads).forEach((threadId, index) => {
        const thread = threads[threadId];

        // Crear el elemento CodeShard con estilo de ThreadItem
        const codeShard = $(
            `<div class="ThreadItem" data-thread-id="${threadId}"></div>`
        );

        // Generar información para el título del hilo
        let threadTitle = `Hilo ${index + 1}`;
        let threadInfo = "";

        if (thread.function) {
            threadInfo = `${thread.function}`;
        }
        if (thread.line) {
            threadInfo += ` (línea ${thread.line})`;
        }

        // Determinar el icono basado en el estado del hilo (si existe)
        let threadIcon = "⟲"; // Icono por defecto para hilos en ejecución
        if (thread.state) {
            if (
                thread.state.toLowerCase().includes("blocked") ||
                thread.state.toLowerCase().includes("waiting")
            ) {
                threadIcon = "⏸";
            } else if (thread.state.toLowerCase().includes("terminated")) {
                threadIcon = "⏹";
            }

            if (!threadInfo.includes(thread.state)) {
                threadInfo += ` - ${thread.state}`;
            }
        }

        // Añadir encabezado con estilo de ThreadItem
        codeShard.append(`
            <div class="ThreadItemHeader">
                <div class="ThreadIcon">${threadIcon}</div>
                <div class="ThreadInfo">
                    <div class="ThreadName">${threadTitle}</div>
                    <div class="ThreadFunction">${
                        threadInfo || "Sin información disponible"
                    }</div>
                </div>
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
                        `<pre class="CodeShard-Content-Fallback">${escapeHtml(
                            thread.code
                        )}</pre>`
                    );

                    // Para el fallback también ajustamos los números de línea
                    if (thread.code) {
                        const codeLines = thread.code.split("\n");
                        const fallbackContent = $("<div></div>");

                        codeLines.forEach((line, index) => {
                            const actualLineNumber = index + lineOffset;
                            const isCurrentLine =
                                actualLineNumber === currentLine;
                            fallbackContent.append(`
                                <div class="CodeLine${
                                    isCurrentLine ? " CurrentLine" : ""
                                }">
                                    <span class="LineNumber">${actualLineNumber}</span>
                                    ${escapeHtml(line)}
                                </div>
                            `);
                        });

                        $(`#${editorId}`).html(fallbackContent);
                    }
                }
            }, 100);
        } else {
            codeShard.append(
                '<div class="ThreadVariables"><p>No hay código disponible para mostrar</p></div>'
            );
        }

        // Ya no añadimos variables aquí, solo el código

        // Añadir el CodeShard al contenedor
        $("#CodeShards").append(codeShard);
    });

    // También actualizar el contenido de hilos en la vista visual
    updateThreadVisual(threads);
}

// Función para actualizar la visualización de hilos en el panel visual
function updateThreadVisual(threads) {
    const threadContent = $(".ThreadContent");
    threadContent.empty();

    const threadCount = Object.keys(threads).length;

    // Si no hay hilos, mostrar mensaje informativo
    if (threadCount === 0) {
        threadContent.append(`
            <div class="ThreadVisual">
                <div class="ThreadCount">No hay hilos activos</div>
                <div class="ThreadList empty">
                    <div class="EmptyThreadMessage">La ejecución ha terminado o no se ha iniciado.</div>
                </div>
            </div>
        `);
        return;
    }

    const threadVisual = $(`<div class="ThreadVisual">
        <div class="ThreadCount">Hilos activos: ${threadCount}</div>
    </div>`);

    // Crear representación gráfica de los hilos
    const threadList = $('<div class="ThreadList"></div>');

    // Ordenar los hilos por ID para una visualización consistente
    const sortedThreadIds = Object.keys(threads).sort();

    sortedThreadIds.forEach((threadId, index) => {
        const thread = threads[threadId];

        // Determinar el icono basado en el estado del hilo (si existe)
        let threadIcon = "⟲"; // Icono por defecto para hilos en ejecución
        if (thread.state) {
            if (
                thread.state.toLowerCase().includes("blocked") ||
                thread.state.toLowerCase().includes("waiting")
            ) {
                threadIcon = "⏸";
            } else if (thread.state.toLowerCase().includes("terminated")) {
                threadIcon = "⏹";
            }
        }

        // Generar información adicional sobre el hilo
        let threadInfo = "";
        if (thread.function) {
            threadInfo = `${thread.function}`;
        }
        if (thread.line) {
            threadInfo += ` (línea ${thread.line})`;
        }
        if (thread.state && !threadInfo.includes(thread.state)) {
            threadInfo += ` - ${thread.state}`;
        }

        const threadItem =
            $(`<div class="ThreadItem" data-thread-id="${threadId}">
            <div class="ThreadItemHeader">
                <div class="ThreadIcon">${threadIcon}</div>
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
            const varsTitle = $("<h4>Variables</h4>");
            const varTable = $('<table class="VarTable"></table>');

            Object.keys(thread.variables).forEach((varName) => {
                varTable.append(`<tr>
                    <td class="VarName">${varName}</td>
                    <td class="VarValue">${thread.variables[varName]}</td>
                </tr>`);
            });

            varsContainer.append(varsTitle);
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

        // Eliminar resaltado de todos los elementos
        $(".CodeShard").removeClass("highlighted");
        $(".ThreadItem").removeClass("highlighted");

        // Resaltar el CodeShard correspondiente
        $(`.CodeShard[data-thread-id="${threadId}"]`).addClass("highlighted");

        // Resaltar también el elemento de hilo seleccionado
        $(this).addClass("highlighted");

        // Hacer scroll al CodeShard correspondiente
        const targetShard = $(`.CodeShard[data-thread-id="${threadId}"]`)[0];
        if (targetShard) {
            targetShard.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
            });
        }
    });
}

// Inicializar los manejadores de eventos para los botones de depuración
export function initializeDebugger() {
    console.log("Inicializando debugger UI...");

    // Mostrar interfaz vacía inicialmente
    try {
        updateThreadVisual({});

        // Mostrar mensaje inicial en el contenedor de CodeShards
        $("#CodeShards").empty().append(`
            <div class="ThreadItem">
                <div class="ThreadItemHeader">
                    <div class="ThreadInfo">
                        <div class="ThreadName">Depurador Inactivo</div>
                    </div>
                </div>
                <div class="ThreadVariables">
                    <p>Usa el botón <img src="../images/play-solid.svg" alt="Run" style="width: 16px; height: 16px;"> para iniciar la depuración del código.</p>
                    <p>Asegúrate de compilar tu código primero en la sección "Coder".</p>
                    <p><strong>Nota:</strong> El código de los hilos se mostrará aquí, mientras que las variables aparecerán en el panel de <em>Estado de Hilos y Variables</em>.</p>
                </div>
            </div>
        `);

        // Inicializar el área de visualización de hilos con un mensaje informativo
        $(".ThreadContent").empty().append(`
            <div class="ThreadVisual">
                <div class="ThreadCount">No hay hilos activos</div>
                <div class="ThreadList empty">
                    <div class="EmptyThreadMessage">La ejecución no se ha iniciado. Las variables de cada hilo se mostrarán aquí durante la depuración.</div>
                </div>
            </div>
        `);

        console.log("Interfaz del depurador inicializada correctamente");
    } catch (error) {
        console.error("Error al inicializar la interfaz del depurador:", error);
    }
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