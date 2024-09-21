import React from "react";
import "./MainContent.css";
import Editor from "./Editor/Editor";
import Terminal from "./Terminal/Terminal";
import Button from "./Button/Button";
function MainContent() {
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

    const Compilar = () => {
        console.log("Compilando");
    };

    const Ejecutar = () => {
        console.log("Ejecutando");
    };

    return (
        <div className="MainContent">
            <div className="Code">
                <Editor value={code} setValue={setCode} />
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
