import  $  from "jquery";
import { updateTerminal } from "./outputTerminal.js";
import { getBreakpoints } from "./editor.js";
import {
    getSocket,
    getCompiled,
    setEditorChanged,
    getLastCompiledDebugMode,
} from "../utils/webSocket.js";

function Compile() {
    const code = window.editor.state.doc.toString();
    const breakpoints = getBreakpoints(window.editor);
    // Obtener el modo de depuración seleccionado
    const debugMode = document.getElementById("debugMode").value;
    console.log("Código a compilar:", code);
    console.log("Puntos de interrupción:", breakpoints);
    console.log("Modo de depuración:", debugMode);

    // Indicar que estamos compilando, por lo que no hay cambios pendientes
    setEditorChanged(false);

    getSocket().emit("compile", {
        code: code,
        breakpoints: breakpoints,
        debugMode: debugMode,
    });
    console.log("Enviando código para compilación...");
}

function Run() {
    if (!getCompiled()) {
        updateTerminal("No se ha compilado previamente");
        return;
    }
    getSocket().emit("run");
    console.log("Enviando solicitud de ejecución...");
}

export function setupButtonEvents() {
    $(document).on("click", "#Compilar", function () {
        console.log("Botón compilar clickeado");
        Compile();
    });

    $(document).on("click", "#Ejecutar", function () {
        console.log("Botón ejecutar clickeado");
        Run();
    });

    // Detector de cambios en el selector de modo de depuración
    $(document).on("change", "#debugMode", function () {
        const newMode = $(this).val();
        const lastMode = getLastCompiledDebugMode();
        console.log(
            "Modo de depuración cambiado a:",
            newMode,
            "(anterior:",
            lastMode + ")"
        );

        // Marcamos como cambiado si hay una compilación previa y el modo ha cambiado
        if (getCompiled() && newMode !== lastMode) {
            setEditorChanged(true);
            console.log(
                "Se ha marcado el editor como modificado debido al cambio de modo de depuración"
            );
        }
    });
}
