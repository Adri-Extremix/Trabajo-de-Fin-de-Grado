import React from "react";
import "./App.css"; // Importación de los estilos específicos para este componente
import Header from "./components/Header/Header";
import MainContent from "./components/MainContent/MainContent";

function App() {
    return (
        <div className="App">
            <Header />
            <MainContent />
        </div>
    );
}

export default App;
