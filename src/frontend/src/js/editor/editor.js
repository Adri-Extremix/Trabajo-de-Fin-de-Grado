import $ from "jquery";
import { EditorState, StateEffect, StateField } from "@codemirror/state";
import { cpp } from "@codemirror/lang-cpp";
import { oneDark } from "@codemirror/theme-one-dark";
import { EditorView, basicSetup } from "codemirror";
import { Decoration, gutter } from "@codemirror/view";
import { setEditorChanged } from "../utils/webSocket.js";

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
    const code = `#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

int global_counter = 0;

pthread_mutex_t shared_resource_mutex;

typedef struct {
    int a;
    int b;
    int result;
} AddArgs;

typedef struct {
    int* arr;
    int size;
} PrintArrayArgs;

void* greet(void* argumento) {
    pthread_mutex_lock(&shared_resource_mutex);
    printf("¡Hola, bienvenido al programa!\\n");
    global_counter++;
    printf("[Hilo Greet] Contador global: %d\\n", global_counter);
    pthread_mutex_unlock(&shared_resource_mutex);

    usleep(100000);
    return NULL;
}

void* add(void* argumento) {
    AddArgs* args = (AddArgs*)argumento;
    args->result = args->a + args->b;

    pthread_mutex_lock(&shared_resource_mutex);
    printf("[Hilo Add] Realizando suma: %d + %d = %d\\n", args->a, args->b, args->result);
    global_counter += args->result;
    printf("[Hilo Add] Contador global: %d\\n", global_counter);
    pthread_mutex_unlock(&shared_resource_mutex);

    usleep(150000);
    return NULL;
}

void* printArray(void* xd) {
    PrintArrayArgs* args = (PrintArrayArgs*)xd;

    pthread_mutex_lock(&shared_resource_mutex);
    printf("[Hilo PrintArray] Array: ");
    for (int i = 0; i < args->size; i++) {
        printf("%d ", args->arr[i]);
    }
    printf("\\n");
    for (int i = 0; i < args->size; i++) {
        global_counter += args->arr[i];
    }
    printf("[Hilo PrintArray] Contador global: %d\\n", global_counter);
    pthread_mutex_unlock(&shared_resource_mutex);

    usleep(200000);
    return NULL;
}

int main() {
    pthread_t thread1, thread2, thread3;

    if (pthread_mutex_init(&shared_resource_mutex, NULL) != 0) {
        fprintf(stderr, "Error al inicializar el mutex compartido.\\n");
        return 1;
    }

    pthread_create(&thread1, NULL, greet, NULL);
    
    AddArgs addArgs = { 5, 3, 0 };
    pthread_create(&thread2, NULL, add, &addArgs);
    
    int arr[] = { 10, 20, 30, 40, 50 };
    PrintArrayArgs printArrayArgs = { arr, 5 };
    pthread_create(&thread3, NULL, printArray, &printArrayArgs);

    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);
    pthread_join(thread3, NULL);

    pthread_mutex_destroy(&shared_resource_mutex);

    printf("\\nSuma total del hilo 'add': %d\\n", addArgs.result);
    printf("Valor final del contador global: %d\\n", global_counter);

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
                            : addBreakpoint.of(linePos),
                    });

                    console.log("Breakpoints:", getBreakpoints(view));
                    // Marcar que se han modificado los breakpoints
                    setEditorChanged(true);
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
            EditorView.updateListener.of((update) => {
                if (update.docChanged || update.viewportChanged) {
                    // Marcar que el editor ha cambiado desde la última compilación
                    setEditorChanged(true);
                }
            }),
            EditorView.theme({
                ".cm-breakpoint-gutter": {
                    width: "25px",
                    cursor: "pointer",
                },
                ".cm-breakpoint-marker": {
                    color: "red",
                    fontSize: "18px",
                    lineHeight: "18px",
                    margin: "0 auto",
                    textAlign: "center",
                },
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
