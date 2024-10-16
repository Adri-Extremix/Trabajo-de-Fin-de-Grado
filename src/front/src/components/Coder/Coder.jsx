import React from "react";
import "./Coder.css";
import Editor from "./Editor/Editor";
import Terminal from "./Terminal/Terminal";
import Button from "./Button/Button";
import axios from "axios";

function Coder() {
    const [code, setCode] = React.useState(`//Este es un Código de Ejemplo

#include <stdio.h>
const int M = 3;
const int N = 3;
    
void print(int arr[M][N])
{
    int i, j;
    for (i = 0; i < M; i++)
        for (j = 0; j < N; j++)
        printf("%d ", arr[i][j]);
}
    
int main()
{
    int arr[][3] = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
    print(arr);
    return 0;
}`);

    const [outTerminal, setOutTerminal] = React.useState("");
    const [isCompiled, setIsCompiled] = React.useState(false);

    const Compilar = async () => {
        try {
            const response = await axios.post("http://localhost:8080/CC/compile", {
                code,
            });
            setOutTerminal(response.data.output);
            setIsCompiled(true);
        } catch (error) {
            console.error("Error al compilar:", error);
            setIsCompiled(false);
        }
    };

    const Ejecutar = async () => {
        if (!isCompiled) return;
        try {
            const response = await axios.post("http://localhost:8080/CC/run", {
                code,
            });
            setOutTerminal(response.data.output);
        } catch (error) {
            console.error("Error al ejecutar:", error);
        }
        console.log("Ejecutando");
    };

    return (
        <div className="Coder">
            <div className="Code">
                <Editor value={code} setValue={setCode} />
                <div className="Buttons">
                    <Button text="Compilar" onClick={Compilar} />
                    <Button text="Ejecutar" onClick={Ejecutar} />
                </div>
            </div>
            <Terminal output={outTerminal} />
        </div>
    );
}

export default Coder;
