import React from "react";
import "./Terminal.css";

function Terminal({ output }) {
    return (
        <div className="Terminal">
            <pre>{output}</pre>
        </div>
    );
}

export default Terminal;
