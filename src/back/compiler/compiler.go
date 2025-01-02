package compiler

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const exeFileName = "exe-*.o"

func CompileC(code string) (exePath string, output string, err error) {

	projDir, err := os.Getwd()
	if err != nil {
		fmt.Println("Error obteniendo el directorio del proyecto:", err)
		return
	}

	// Construir la ruta relativa a los archivos de encabezado
	headersDir := filepath.Join(projDir, "c_code")

	tmpFile, err := os.CreateTemp("/tmp", "code-*.c")
	if err != nil {
		return "", "Error: Ha ocurrido un error en el backend", fmt.Errorf("no se pudo crear el archivo temporal: %v", err)
	}
	defer os.Remove(tmpFile.Name())

	if _, err := tmpFile.Write([]byte(code)); err != nil {
		return "", "Error: Ha ocurrido un error en el backend", fmt.Errorf("no se pudo escribir en el archivo temporal: %v", err)
	}

	if err := tmpFile.Close(); err != nil {
		return "", "Error: Ha ocurrido un error en el backend", fmt.Errorf("no se pudo cerrar el fichero temporal: %v", err)
	}

	exeFile, err := os.CreateTemp("/tmp", exeFileName)
	if err != nil {
		return "", "Error: Ha ocurrido un error en el backend", fmt.Errorf("no se pudo crear el archivo temporal: %v", err)
	}
	exeFile.Close()

	exe := exec.Command("gcc", "-I", headersDir, tmpFile.Name(), "./c_code/store_state.c", "-o", exeFile.Name(), "-pthread", "-lcjson")
	outputBytes, err := exe.CombinedOutput()
	outputStr := string(outputBytes)
	outputStr = strings.ReplaceAll(outputStr, tmpFile.Name(), "code.c")
	if err != nil {
		return "", "Error: La compilación ha fallado \n" + outputStr, err
	}
	return exeFile.Name(), "Compilación terminada con éxito \n" + outputStr, nil
}

func RunC(exePath string) (output string, err error) {

	exe := exec.Command(exePath)
	fmt.Print(exePath)
	outputBytes, err := exe.CombinedOutput()
	outputStr := string(outputBytes)
	if err != nil {
		return outputStr, fmt.Errorf("error al ejecutar: %v", err)
	}
	return outputStr, err
}
