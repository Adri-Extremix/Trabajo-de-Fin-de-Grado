import $ from "jquery";
import {initializeSocket, bindingComunicactions} from "./utils/webSocket.js"
import { crearEditor } from "./editor/editor.js";
import "../css/variables.css";
import { setupButtonEvents } from "./editor/buttons.js";
import { updateSlicer, RunColorManager } from "./utils/uiManager.js";
import {
    updateDebuggerControls,
    setupThreadControlEvents,
} from "./debugger/debugControllers.js";

$(function () {
    crearEditor();
    RunColorManager();
    updateSlicer();

    // Inicializar el WebSocket
    initializeSocket();
    bindingComunicactions();
    setupButtonEvents();

    // Inicializar controladores de depuración
    setupThreadControlEvents();

    // Actualizar los controles de depuración cuando se cambia el modo
    $(document).on("change", "#debugMode", function () {
        console.log("Modo de depuración cambiado, actualizando controles...");
        setTimeout(updateDebuggerControls, 100); // Actualizar después del cambio
    });

    // Ejecutar la primera vez para configurar los controles según el modo inicial
    setTimeout(updateDebuggerControls, 200);
});



