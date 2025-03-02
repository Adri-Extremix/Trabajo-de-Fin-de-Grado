import $ from "jquery";
import { updateTerminal } from "./outputTerminal";
import { crearEditor } from "./codeMirror";
/* import { updateTerminal } from './outputTerminal'; */

let compiled = false;

// Button click event handlers
$(function () {
  crearEditor();

  $("#Compilar").on("click", function () {
    Compile();
  });
  $("#Ejecutar").on("click", function () {
    Run();
  });
});

function Compile() {
  /* const data = { code: window.editor.state.doc.toString() , breakpoint: Array.from(window.editor.state.breakpointState.breakpoints) }; */
  const data = { code: window.editor.state.doc.toString() };
  console.log(data);
  $.ajax({
    url: "http://localhost:8080/CC/compile",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify(data),
    success: function (response) {
      console.log("Respuesta obtenida:", response);
      // Handle successful creation
      updateTerminal(response.output);
      compiled = true;
    },
    error: function (xhr, status, error) {
      console.error("Error creating data:", error);
      // Handle error
      updateTerminal("Error de red o servidor no disponible");
      compiled = false;
    },
  });
}

function Run() {
  if (!compiled) {
    updateTerminal("No se ha compilado previamente");
    return;
  }

  /* const data = { code: window.editor.state.doc.toString() , breakpoint: Array.from(window.editor.state.breakpointState.breakpoints) }; */
  const data = { code: window.editor.state.doc.toString() };
  console.log(data);
  $.ajax({
    url: "http://localhost:8080/CC/run",
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify(data),
    success: function (response) {
      console.log("Respuesta Obtenida:", response);
      // Handle successful creation
      updateTerminal(response.output);
    },
    error: function (xhr, status, error) {
      console.error("Error creating data:", error);
      // Handle error
      updateTerminal("Error de red o servidor no disponible");
    },
  });
}
