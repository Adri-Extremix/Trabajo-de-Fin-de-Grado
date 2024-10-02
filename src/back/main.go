package main

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/Adri-Extremix/Trabajo-de-Fin-de-Grado/src/back/compiler"
)

// RequestBody define la estructura de la solicitud JSON
type RequestBody struct {
    Code string `json:"code"`
}

// ResponseBody define la estructura de la respuesta JSON
type ResponseBody struct {
    Output string `json:"output,omitempty"`
    Error  string `json:"error,omitempty"`
}

func handleCode(res http.ResponseWriter, req *http.Request, processFunc func(string) (string,error)){
	if req.Method != http.MethodPost {
		http.Error(res,"Esté método no está soportado",http.StatusMethodNotAllowed)
		return
	}
	var reqBody RequestBody
	err := json.NewDecoder(req.Body).Decode(&reqBody)
	if err != nil{
		http.Error(res, err.Error(), http.StatusBadRequest)
	}
	output, err := processFunc(reqBody.Code)

	var resBody ResponseBody

	if err != nil{
		resBody.Error = err.Error()
	} else {
		resBody.Output = output
	}

	res.Header().Set("Content-Type", "application/json")
	json.NewEncoder(res).Encode(resBody)

}

func compileHandler(res http.ResponseWriter, req *http.Request){
	handleCode(res,req,compiler.CompileC)
}

/* func runHandler(res http.ResponseWriter, req *http.Request){
	handleCode(res,req,compiler.RunC)
} */



func main(){
	http.HandleFunc("/api/compile", compileHandler)
	//http.HandleFunc("/api/run",runHandler)
    fmt.Println("Servidor corriendo en http://localhost:8080")
    http.ListenAndServe(":8080", nil)
}
