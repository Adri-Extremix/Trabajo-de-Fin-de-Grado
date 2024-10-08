package compiler

import (
	"fmt"
	"os"
	"os/exec"
)

func CompileC(code string) (output string, err error) {

	tmpFile, err := os.CreateTemp("/tmp", "code-*.c")
	if err != nil {
		return "Error: Ha ocurrido un error en el backend", fmt.Errorf("no se pudo crear el archivo temporal: %v", err)
	}
	defer os.Remove(tmpFile.Name()) // Eliminar el archivo temporal al final

	if _, err := tmpFile.Write([]byte(code)); err != nil {
		return "Error: Ha ocurrido un error en el backend", fmt.Errorf("no se pudo escribir en el archivo temporal: %v", err)
	}

	if err := tmpFile.Close(); err != nil {
		return "Error: Ha ocurrido un error en el backend", fmt.Errorf("no se pudo cerrar el fichero temporal: %v", err)
	}

	exeFile, err := os.CreateTemp("/tmp", "exe.o")
	if err != nil {
		return "Error: Ha ocurrido un error en el backend", fmt.Errorf("no se pudo crear el archivo temporal: %v", err)
	}
	exeFile.Close()

	exe := exec.Command("gcc", tmpFile.Name(), "-o", exeFile.Name())
	outputBytes, err := exe.CombinedOutput()
	fmt.Println(string(outputBytes))
	if err != nil {
		return string(outputBytes), fmt.Errorf("error al compilar: %v", err)
	}

	return "Compilación terminada \n" + string(outputBytes), nil
}
