package compiler

import "fmt"

func CompileC(code string) (output string, err error){
	fmt.Print("Compilando")
	return "Compilado con éxito", nil
}