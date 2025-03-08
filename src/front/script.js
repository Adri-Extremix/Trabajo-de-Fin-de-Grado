import $ from "jquery";
import { updateTerminal } from "./outputTerminal";
import { crearEditor,getBreakpoints } from "./codeMirror";
import "./debuggerManager";
import './variables.css';

/* import { updateTerminal } from './outputTerminal'; */

let compiled = false;

function RunColorManager() {
    if (compiled) {
        $("#Ejecutar").prop("disabled", false);
    } else {
        $("#Ejecutar").prop("disabled", true);
    }
}

// Button click event handlers
$(function () {
    crearEditor();
    RunColorManager();
    
    $("#Debugger").hide();
    // Inicialmente deshabilitar el slicer si no se ha compilado
    $("#slicerToggle").prop("disabled", !compiled);

    // Eventos de los botones de compilar y ejecutar
    $("#Compilar").on("click", function () {
        Compile();
        console.log(compiled)
        $("#slicerToggle").prop("disabled", !compiled);
    });
    $("#Ejecutar").on("click", function () {
        Run();
    });

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


    // Eventos de los botones del Debugger
    $("#Debug-Run").on("click", runExecution);
    $("#Debug-Continue").on("click", continueExecution);
    $("#Debug-Reverse-Continue").on("click", reverseContinueExecution);
    $("#Debug-Step-Over").on("click", stepOverExecution);
    $("#Debug-Reverse-Step-Over").on("click", reverseStepOverExecution);
    $("#Debug-Step-Into").on("click", stepIntoExecution);
    $("#Debug-Reverse-Step-Into").on("click", reverseStepIntoExecution);
    $("#Debug-Step-Out").on("click", stepOutExecution);
    $("#Debug-Reverse-Step-Out").on("click", reverseStepOutExecution);
});

function Compile() {
    const data = { code: window.editor.state.doc.toString() };
    console.log(data);
    $.ajax({
        url: "http://localhost:8080/CC/compile",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify(data),
        success: function (response) {
            console.log("Respuesta obtenida:", response);
            updateTerminal(response.output);
            compiled = true;
            $("#Ejecutar").css("backgroundColor", "");
            $("#Ejecutar").css("border-color", "#007bff");

            // Actualizamos botones y slicer solo cuando se reciba la respuesta
            RunColorManager();
            $("#slicerToggle").prop("disabled", !compiled);
            addBreakpoints();
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
            updateTerminal("Error de red o servidor no disponible");
            compiled = false;

            // Actualizamos botones y slicer en caso de error
            RunColorManager();
            $("#slicerToggle").prop("disabled", !compiled);
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

function addBreakpoints() {
    const breakpoints = getBreakpoints(window.editor);
    console.log("Se envían los siguientes Breakpoints:", breakpoints);
    $.ajax({
        url: "http://localhost:8080/CC/debug/add_breakpoint",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ breakpoints }),
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}

function runExecution() {
    console.log("Ejecutando...");
    $.ajax({
        url: "http://localhost:8080/CC/debug/run",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}

function continueExecution(){
    $.ajax({
        url: "http://localhost:8080/CC/debug/continue",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}

function reverseContinueExecution(){
    $.ajax({
        url: "http://localhost:8080/CC/debug/reverse_continue",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}

function stepOverExecution(){
    $.ajax({
        url: "http://localhost:8080/CC/debug/step_over",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}

function reverseStepOverExecution(){
    $.ajax({
        url: "http://localhost:8080/CC/debug/reverse_step_over",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}

function stepIntoExecution(){
    $.ajax({
        url: "http://localhost:8080/CC/debug/step_into",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}

function reverseStepIntoExecution(){
    $.ajax({
        url: "http://localhost:8080/CC/debug/reverse_step_into",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}

function stepOutExecution(){
    $.ajax({
        url: "http://localhost:8080/CC/debug/step_out",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}

function reverseStepOutExecution(){
    $.ajax({
        url: "http://localhost:8080/CC/debug/reverse_step_out",
        method: "GET",
        contentType: "application/json",
        success: function (response) {
            console.log("Respuesta obtenida:", response);
        },
        error: function (xhr, status, error) {
            console.error("Error creating data:", error);
        },
    });
}