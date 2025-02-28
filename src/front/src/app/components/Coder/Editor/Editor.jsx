"use client";
import React from "react";
import CodeMirror from "@uiw/react-codemirror";
import { javascript } from "@codemirror/lang-javascript";
import { cpp } from "@codemirror/lang-cpp";
import { vscodeDark } from "@uiw/codemirror-theme-vscode";
import { tokyoNight } from "@uiw/codemirror-theme-tokyo-night";
import "./Editor.css";

function Editor({ value, setValue }) {
    const onChange = React.useCallback((val, viewUpdate) => {
        console.log("val:", val);
        setValue(val);
    }, []);

    return (
        <div className="Editor">
            <CodeMirror
                value={value}
                extensions={[cpp()]}
                onChange={onChange}
                theme={tokyoNight}
                className="cm-editor"
            />
        </div>
    );
}

export default Editor;