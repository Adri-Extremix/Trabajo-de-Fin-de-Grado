"use client";
import React from "react";
import "./Debugger.css";
const Debugger = () => {
    return (
        <div className="Debugger">
            <div className="Debugg">
                <div className="Title">Depurador de Código</div>
                <div className="VerticalContainer">
                    <div className="CodeShard">AA</div>
                    <div className="CodeShard">BB</div>
                    <div className="CodeShard">BB</div>
                    <div className="CodeShard">BB</div>
                    <div className="CodeShard">BB</div>
                    <div className="CodeShard">BB</div>
                    <div className="CodeShard">BB</div>
                    <div className="CodeShard">BB</div>
                </div>
            </div>
            <div className="Visual">
                <h3 className="Title">Contenido de Hilos</h3>
            </div>
        </div>
    );
};

export default Debugger;
