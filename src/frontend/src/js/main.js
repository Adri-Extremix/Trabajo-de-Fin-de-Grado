import $ from "jquery";
import {initializeSocket, bindingComunicactions} from "./utils/webSocket.js"
import { crearEditor } from "./editor/editor.js";
import "../css/variables.css";
import { setupButtonEvents } from "./editor/buttons.js";
import { updateSlicer, RunColorManager } from "./utils/uiManager.js";


$(function () {
    crearEditor();
    RunColorManager();
    updateSlicer();

    // Inicializar el WebSocket
    initializeSocket();
    bindingComunicactions();
    setupButtonEvents();
});



