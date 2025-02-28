"use client";
import React from "react";
import "./Main.css";
import Slicer from "./Slicer/Slicer";
import Debugger from "../Debugger/Debugger";
import Coder from "../Coder/Coder";
import "../../global.css";
function Main() {
    const [showCoder, setShowCoder] = React.useState(true);
    const [color, setColor] = React.useState("var(--primary-color-coder)");
    const handleToggle = (value) => {
        setShowCoder(value === 0);
        if (value === 0) {
            setColor("--primary-color-coder"); // Cambia el color a primary
        } else {
            setColor("--primary-color-debugger"); // Cambia el color a secondary
        }
    };

    let componentToShow;
    if (showCoder) {
        componentToShow = <Coder />;
    } else {
        componentToShow = <Debugger />;
    }

    return (
        <div className="Screen">
            <header className="Header">
                <h1>
                    <span className="large-letter" style={{ color: `var(${color})` }}>
                        C
                    </span>
                    oncurrent{" "}
                    <span className="large-letter" style={{ color: `var(${color})` }}>
                        C
                    </span>
                    ode
                </h1>
                <Slicer onToggle={handleToggle} />
            </header>
            {componentToShow}
        </div>
    );
}

export default Main;
