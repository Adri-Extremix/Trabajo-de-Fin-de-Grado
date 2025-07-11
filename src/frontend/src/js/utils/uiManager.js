import {
    getCompiled,
    getEditorChanged,
    getLastCompiledDebugMode,
} from "./webSocket.js";
import $ from "jquery";
import { updateDebuggerControls } from "../debugger/debugControllers.js";

// Función para mostrar un modal personalizado
function showModal(title, message, onConfirm, onCancel) {
    // Eliminar el modal anterior si existe
    $(".modal-overlay").remove();

    // Crear elementos del modal
    const modalOverlay = $('<div class="modal-overlay"></div>');
    const modalContent = $(`
        <div class="modal-content">
            <div class="modal-header">
                <h3>${title}</h3>
                <span class="modal-close">&times;</span>
            </div>
            <div class="modal-body">
                <p>${message}</p>
            </div>
            <div class="modal-footer">
                <button class="modal-btn modal-cancel">Cancelar</button>
                <button class="modal-btn modal-confirm">Continuar</button>
            </div>
        </div>
    `);

    // Añadir el modal al cuerpo del documento
    modalOverlay.append(modalContent);
    $("body").append(modalOverlay);

    // Mostrar modal con animación
    setTimeout(() => {
        modalOverlay.addClass("show");
    }, 10);

    // Event handlers
    $(".modal-close, .modal-cancel").click(() => {
        modalOverlay.removeClass("show");
        setTimeout(() => {
            modalOverlay.remove();
        }, 300);
        if (onCancel) onCancel();
    });

    $(".modal-confirm").click(() => {
        modalOverlay.removeClass("show");
        setTimeout(() => {
            modalOverlay.remove();
        }, 300);
        if (onConfirm) onConfirm();
    });
}

export function RunColorManager() {
    if (getCompiled()) {
        $("#Ejecutar").prop("disabled", false);
    } else {
        $("#Ejecutar").prop("disabled", true);
    }

    // También actualizamos el estado del slicer
    $("#slicerToggle").prop("disabled", !getCompiled());
}

export function updateSlicer() {
    $("#Debugger").hide();
    // Inicialmente deshabilitar el slicer si no se ha compilado
    $("#slicerToggle").prop("disabled", !getCompiled());

    // Función para verificar y mostrar el estado de los cambios en la consola
    function debugChangeState() {
        const currentDebugMode = document.getElementById("debugMode").value;
        const lastDebugMode = getLastCompiledDebugMode();
        const debugModeChanged =
            lastDebugMode !== null && currentDebugMode !== lastDebugMode;
        console.log("Estado actual de cambios:", {
            editorChanged: getEditorChanged(),
            debugModeChanged: debugModeChanged,
            currentDebugMode: currentDebugMode,
            lastCompiledDebugMode: lastDebugMode,
            compiled: getCompiled(),
        });
    }

    // Llamamos a esta función inicialmente y también la asociamos al cambio del modo
    debugChangeState();
    $(document).on("change", "#debugMode", debugChangeState);

    // Evento del slicer para cambiar entre Coder y Debugger
    $("#slicerToggle").on("change", function () {
        const isChecked = $(this).is(":checked");

        if (isChecked) {
            // Verificar si hay cambios en el editor desde la última compilación
            const currentDebugMode = document.getElementById("debugMode").value;
            const lastDebugMode = getLastCompiledDebugMode();
            const debugModeChanged =
                lastDebugMode !== null && currentDebugMode !== lastDebugMode;

            if ((getEditorChanged() || debugModeChanged) && getCompiled()) {
                // Construir el mensaje según lo que ha cambiado
                let warningMessage = "Has realizado cambios";

                if (debugModeChanged) {
                    warningMessage += " en el modo de depuración";
                    if (getEditorChanged()) {
                        warningMessage +=
                            " y en el código o los puntos de interrupción";
                    }
                } else {
                    warningMessage +=
                        " en el código o en los puntos de interrupción";
                }

                warningMessage +=
                    " desde la última compilación. Para ver estos cambios reflejados en el depurador, debes compilar primero. ¿Deseas continuar sin compilar?";

                // Mostrar advertencia al usuario
                showModal(
                    "Cambios no compilados",
                    warningMessage,
                    // Función para confirmar
                    () => {
                        // Continuar con el cambio al modo depurador
                        activateDebuggerMode();
                    },
                    // Función para cancelar
                    () => {
                        // Revertir el estado del slicer
                        $("#slicerToggle").prop("checked", false);
                    }
                );
            } else {
                // No hay cambios o no está compilado, continuar normalmente
                activateDebuggerMode();
            }
        } else {
            // Cambiar a modo editor
            activateEditorMode();
        }
    });

    // Función para activar el modo depurador
    function activateDebuggerMode() {
        // Mostrar Debugger, ocultar Coder
        $("#Coder").hide();
        $("#Debugger").show();
        $(".Slicer-label").text("Debugger");

        // Cambiar el color de los elementos C
        $(".large-letter").css("color", "var(--primary-color-debugger)");

        // Actualizar los controles de depuración según el modo actual
        if (typeof updateDebuggerControls === "function") {
            updateDebuggerControls();
        }

        // Si hay cambios en el editor, colorear el encabezado del modal para indicar modo depuración
        if ($(".modal-overlay").length > 0) {
            $(".modal-header").css(
                "background-color",
                "var(--primary-color-debugger)"
            );
            $(".modal-confirm").css(
                "background-color",
                "var(--primary-color-debugger)"
            );
            $(".modal-confirm").hover(
                function () {
                    $(this).css(
                        "background-color",
                        "var(--hover-button-color-debugger)"
                    );
                },
                function () {
                    $(this).css(
                        "background-color",
                        "var(--primary-color-debugger)"
                    );
                }
            );
        }
    }

    // Función para activar el modo editor
    function activateEditorMode() {
        // Mostrar Coder, ocultar Debugger
        $("#Debugger").hide();
        $("#Coder").show();
        $(".Slicer-label").text("Coder");

        // Restaurar el color de los elementos C
        $(".large-letter").css("color", "var(--primary-color-coder)");
    }
}
