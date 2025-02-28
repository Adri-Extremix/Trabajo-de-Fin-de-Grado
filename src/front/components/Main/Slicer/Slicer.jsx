"use client";
import React from "react";
import "./Slicer.css";
function Slicer({ onToggle }) {
    const [value, setValue] = React.useState(0); // Estado para el valor del slicer (0 o 1)

    const handleChange = () => {
        let newValue;
        if (value === 0) {
            newValue = 1;
        } else {
            newValue = 0;
        }
        setValue(newValue);
        onToggle(newValue); // Llama a la función onToggle con el nuevo valor
    };

    let label;
    if (value === 0) {
        label = "Coder";
    } else {
        label = "Debugger";
    }

    return (
        <div className="Slicer">
            <input
                type="checkbox"
                checked={value === 1}
                onChange={handleChange}
                className="Slicer-toggle"
            />
            <label className="Slicer-label">{label}</label>
        </div>
    );
}

export default Slicer;
