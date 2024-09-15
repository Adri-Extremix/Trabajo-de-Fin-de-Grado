import React from "react";
import "./MainContent.css";
import Editor from "./Editor/Editor";
import Terminal from "./Terminal/Terminal";
function MainContent() {
    return (
        <div className="MainContent">
            <Editor />
            <Terminal />
        </div>
    );
}

export default MainContent;
