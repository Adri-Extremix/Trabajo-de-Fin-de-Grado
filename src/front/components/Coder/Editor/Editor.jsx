"use client";
import React, { useState, useEffect } from "react";
import "./Editor.css";
import CodeMirror from "@uiw/react-codemirror";
import { javascript } from "@codemirror/lang-javascript";
import { cpp } from "@codemirror/lang-cpp";
import { vscodeDark } from "@uiw/codemirror-theme-vscode";
import { tokyoNight } from "@uiw/codemirror-theme-tokyo-night";
import { gutter } from "@codemirror/view";
import { EditorView, Decoration } from "@codemirror/view";
import { StateField, StateEffect } from "@codemirror/state";

function Editor({ value, setValue, onBreakpointsChange }) {

    const [breakpoints, setBreakpoints] = useState(new Set());

    // Efecto para transmitir los breakpoints al componente padre
    useEffect(() => {
        if (onBreakpointsChange) {
            onBreakpointsChange(Array.from(breakpoints));
        }
    }, [breakpoints, onBreakpointsChange]);

    const addBreakpoint = StateEffect.define();
    const removeBreakpoint = StateEffect.define();

    const breakpointState = StateField.define({
        create() {
            return Decoration.set([]);
        },
        update(breakpoints, transaction) {
            breakpoints = breakpoints.map(transaction.changes);
            for (let effect of transaction.effects) {
                if (effect.is(addBreakpoint)) {
                    const breakpointMark = Decoration.widget({
                        widget: new BreakpointWidget(),
                        side: -1
                    });
                    breakpoints = breakpoints.update({
                        add: [breakpointMark.range(effect.value, effect.value)]
                    });
                } else if (effect.is(removeBreakpoint)) {
                    breakpoints = breakpoints.update({
                        filter: from => from !== effect.value
                    });
                }
            }
            return breakpoints;
        },
        provide: field => EditorView.decorations.from(field)
    });

    // Widget para el círculo rojo del breakpoint
    class BreakpointWidget {
        toDOM() {
            const dom = document.createElement("div");
            dom.className = "cm-breakpoint";
            return dom;
        }
    }

     // Función para manejar el clic en el gutter
     const handleGutterClick = (view, line) => {
        const lineNumber = line + 1;
        if (breakpoints.has(lineNumber)) {
            setBreakpoints(prev => {
                const newBreakpoints = new Set(prev);
                newBreakpoints.delete(lineNumber);
                return newBreakpoints;
            });
            view.dispatch({
                effects: removeBreakpoint.of(line)
            });
        } else {
            setBreakpoints(prev => {
                const newBreakpoints = new Set(prev);
                newBreakpoints.add(lineNumber);
                return newBreakpoints;
            });
            view.dispatch({
                effects: addBreakpoint.of(line)
            });
        }
    };

    // Configuración del gutter personalizado para breakpoints
    const breakpointGutter = gutter({
        class: "cm-breakpoint-gutter",
        markers: view => {
            const markers = [];
            // Aquí podríamos agregar marcadores según el estado
            return markers;
        },
        handleClick: handleGutterClick
    });

    const onChange = React.useCallback((val, viewUpdate) => {
        console.log("val:", val);
        setValue(val);
    }, []);

    return (
        <div className="Editor">
            <CodeMirror
                value={value}
                extensions={[cpp(),
                    breakpointState,
                    breakpointGutter,
                    EditorView.theme({
                        ".cm-breakpoint-gutter": {
                            width: "15px",
                            cursor: "pointer"
                        },
                        ".cm-breakpoint": {
                            width: "10px",
                            height: "10px",
                            backgroundColor: "red",
                            borderRadius: "50%",
                            display: "inline-block",
                            marginRight: "5px"
                        }
                    })
                ]}
                onChange={onChange}
                theme={tokyoNight}
                className="cm-editor"
            />
        </div>
    );
}

export default Editor;