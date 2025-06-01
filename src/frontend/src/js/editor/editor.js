import $ from "jquery";
import { EditorState, StateEffect, StateField } from "@codemirror/state";
import { cpp } from "@codemirror/lang-cpp";
import { oneDark } from "@codemirror/theme-one-dark";
import { EditorView, basicSetup } from "codemirror";
import { Decoration, gutter } from "@codemirror/view";

// Definir los efectos de estado para añadir y eliminar breakpoints
const addBreakpoint = StateEffect.define();
const removeBreakpoint = StateEffect.define();

// Campo de estado para mantener los breakpoints
const breakpointState = StateField.define({
    create() {
      return Decoration.none;
    },
    update(decorations, tr) {
      let deco = decorations.map(tr.changes);
      for (let e of tr.effects) {
        if (e.is(addBreakpoint)) {
          const line = tr.state.doc.lineAt(e.value);
          const bpDeco = Decoration.line({ class: "cm-breakpoint" });
          deco = deco.update({
            add: [bpDeco.range(line.from)]
          });
        } else if (e.is(removeBreakpoint)) {
          const line = tr.state.doc.lineAt(e.value);
          deco = deco.update({
            filter: (from, to, value) => from !== line.from
          });
        }
      }
      return deco;
    },
    provide: f => EditorView.decorations.from(f)
  });
  

// Función para obtener los breakpoints actuales como array de números de línea
export function getBreakpoints(view) {
    const breakpoints = [];
    try {
        const markers = view.state.field(breakpointState);

        // Usar un conjunto para evitar duplicados
        const lineSet = new Set();

        markers.between(0, view.state.doc.length, (from, to, deco) => {
            const lineNumber = view.state.doc.lineAt(from).number;
            lineSet.add(lineNumber);
        });

        // Convertir el conjunto a array y ordenar
        breakpoints.push(...Array.from(lineSet).sort((a, b) => a - b));
    } catch (e) {
        console.error("Error al obtener breakpoints:", e);
    }

    return breakpoints;
}

export function crearEditor() {
    const code = `//Este es un Código de Ejemplo

#include <stdio.h>
#include <pthread.h>

#define M 6
#define N 3


int arr[M][N] = {
    {1, 2, 3},
    {4, 5, 6},
    {7, 8, 9},
    {10, 11, 12},
    {13, 14, 15},
    {16, 17, 18}
};

// Función que será ejecutada por cada hilo
void* print_row(void* arg) {
    int row = *(int*)arg; // Índice de la fila a imprimir
    printf("Row %d: ", row);
    for (int j = 0; j < N; j++) {
        printf("%d ", arr[row][j]);
    }
    printf("\\n");
    return NULL;
}

int main() {
    pthread_t threads[M]; // Array para almacenar identificadores de los hilos
    int row_indices[M];   // Array para pasar índices de las filas a los hilos

    // Crear un hilo para cada fila
    for (int i = 0; i < M; i++) {
        row_indices[i] = i; // Asignar el índice de la fila
        if (pthread_create(&threads[i], NULL, print_row, &row_indices[i]) != 0) {
            perror("Error creando hilo");
            return 1;
        }
    }

    // Esperar a que todos los hilos terminen
    for (int i = 0; i < M; i++) {
        if (pthread_join(threads[i], NULL) != 0) {
            perror("Error esperando hilo");
            return 1;
        }
    }

    printf("Todos los hilos han terminado.\\n");
    printf("¿Han términado en orden?");
    return 0;
}
`;
    const editorContainer = $("#Editor")[0];

    // Configuración del gutter para breakpoints
    const breakpointGutter = gutter({
        class: "cm-breakpoint-gutter",
        renderEmptyElements: true,
        /*lineMarker: (view, line) => {
            const lineNumber = view.state.doc.lineAt(line.from).number;
            const lineBreakpoints = getBreakpoints(view);
            // Cambiar el uso de "in" por "includes" para verificar correctamente
            if (lineBreakpoints.includes(lineNumber)) {
                const marker = document.createElement("div");
                marker.className = "cm-breakpoint-marker";
                marker.textContent = "●";
                return marker;
            }
            return null;
        }, */
        domEventHandlers: {
            click: (view, line) => {
                try {
                    const lineNumber = view.state.doc.lineAt(line.from).number;
                    const linePos = line.from;
                    const lineBreakpoints = getBreakpoints(view);
                    const hasBreakpoint = lineBreakpoints.includes(lineNumber);
    
                    view.dispatch({
                        effects: hasBreakpoint
                            ? removeBreakpoint.of(linePos)
                            : addBreakpoint.of(linePos)
                    });
    
                    console.log("Breakpoints:", getBreakpoints(view));
                    return true;
                } catch (e) {
                    console.error("Error al manejar clic en gutter:", e);
                    return false;
                }
            }
        }
    });
    

    // Crear el estado del editor
    const startState = EditorState.create({
        doc: code,
        extensions: [
            basicSetup,
            cpp(),
            oneDark,
            breakpointState,
            breakpointGutter,
            EditorView.lineWrapping,
            EditorView.theme({
                ".cm-breakpoint-gutter": {
                    width: "25px",
                    cursor: "pointer"
                },
                ".cm-breakpoint-marker": {
                    color: "red",
                    fontSize: "18px",
                    lineHeight: "18px",
                    margin: "0 auto",
                    textAlign: "center"
                }
            }),
        ],
    });

    // Inicializar el editor
    const view = new EditorView({
        state: startState,
        parent: editorContainer,
    });

    window.editor = view;
    // window.editor.breakpointState = breakpointState;
}
