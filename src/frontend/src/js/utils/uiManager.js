import { getCompiled } from "./webSocket.js";
import  $  from "jquery";

export function RunColorManager() {
    if (getCompiled()) {
        $("#Ejecutar").prop("disabled", false);
    } else {
        $("#Ejecutar").prop("disabled", true);
    }
}

export function updateSlicer() {
    $("#Debugger").hide();
    // Inicialmente deshabilitar el slicer si no se ha compilado
    $("#slicerToggle").prop("disabled", !getCompiled());

    // Evento del slicer para cambiar entre Coder y Debugger
    $("#slicerToggle").on("change", function () {
        const isChecked = $(this).is(":checked");

        if (isChecked) {
            // Mostrar Debugger, ocultar Coder
            $("#Coder").hide();
            $("#Debugger").show();
            $(".Slicer-label").text("Debugger");

            // Cambiar el color de los elementos C
            $(".large-letter").css("color", "var(--primary-color-debugger)");
        } else {
            // Mostrar Coder, ocultar Debugger
            $("#Debugger").hide();
            $("#Coder").show();
            $(".Slicer-label").text("Coder");

            // Restaurar el color de los elementos C
            $(".large-letter").css("color", "var(--primary-color-coder)");
        }
    });
}