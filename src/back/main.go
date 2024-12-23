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

var exeFilePath string

// Middleware para manejar CORS
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		// Manejar solicitudes OPTIONS
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func compileHandler(res http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodPost {
		http.Error(res, "Esté método no está soportado", http.StatusMethodNotAllowed)
		return
	}
	var reqBody RequestBody
	err := json.NewDecoder(req.Body).Decode(&reqBody)
	if err != nil {
		http.Error(res, err.Error(), http.StatusBadRequest)
		return
	}
	exePath, output, err := compiler.CompileC(reqBody.Code)

	var resBody ResponseBody
	if err != nil {
		resBody.Error = err.Error()
	} else {
		resBody.Output = output
		exeFilePath = exePath // Almacenar el nombre del archivo ejecutable temporal
	}

	resBody.Output = output

	res.Header().Set("Content-Type", "application/json")
	json.NewEncoder(res).Encode(resBody)
}

func runHandler(res http.ResponseWriter, req *http.Request) {
	if req.Method != http.MethodPost {
		http.Error(res, "Esté método no está soportado", http.StatusMethodNotAllowed)
		return
	}

	if exeFilePath == "" {
		fmt.Print("No hay ejecutable")
		http.Error(res, "No hay archivo ejecutable disponible. Compila el código primero.", http.StatusBadRequest)
		return
	}
	var reqBody RequestBody
	err := json.NewDecoder(req.Body).Decode(&reqBody)
	if err != nil {
		http.Error(res, err.Error(), http.StatusBadRequest)
		return
	}

	output, err := compiler.RunC(exeFilePath)
	var resBody ResponseBody
	if err != nil {
		resBody.Error = err.Error()
	} else {
		resBody.Output = output
	}
	res.Header().Set("Content-Type", "application/json")
	json.NewEncoder(res).Encode(resBody)
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/CC/compile", compileHandler)
	mux.HandleFunc("/CC/run", runHandler)

	// Aplicar el middleware CORS
	handler := corsMiddleware(mux)

	fmt.Println("Servidor corriendo en http://localhost:8080")
	http.ListenAndServe(":8080", handler)
}
