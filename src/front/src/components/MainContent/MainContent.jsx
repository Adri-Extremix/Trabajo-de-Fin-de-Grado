import React from "react";
import "./MainContent.css";
import Editor from "./Editor/Editor";
import Terminal from "./Terminal/Terminal";
import Button from "./Button/Button";
function MainContent() {
    const Compilar = () => {
        console.log("Compilando");
    };

    const Ejecutar = () => {
        console.log("Ejecutando");
    };

    return (
        <div className="MainContent">
            <div className="Code">
                <Editor />
                <div className="Buttons">
                    <Button text="Compilar" onClick={Compilar} />
                    <Button text="Ejecutar" onClick={Ejecutar} />
                </div>
            </div>
            <Terminal />
        </div>
    );
}

export default MainContent;
