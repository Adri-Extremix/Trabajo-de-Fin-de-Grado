import React from "react";
import "./Button.css";

function Button({ text, onClick }) {
    return (
        <div className="Button" onClick={onClick}>
            {text}
        </div>
    );
}

export default Button;
