import  $  from "jquery";
import { updateTerminal } from "./outputTerminal.js";
import { getBreakpoints } from "./editor.js";
import { getSocket, getCompiled } from "../utils/webSocket.js";


function Compile() {
    const code = window.editor.state.doc.toString();
    const breakpoints = getBreakpoints(window.editor);
    console.log("Código a compilar:", code);
    console.log("Puntos de interrupción:", breakpoints);
    getSocket().emit("compile", { code: code, breakpoints: breakpoints });
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
    $(document).on("click", "#Compilar", function() {
      console.log("Botón compilar clickeado");
      Compile();
    });
    
    $(document).on("click", "#Ejecutar", function() {
      console.log("Botón ejecutar clickeado");
      Run();
    });
  }
