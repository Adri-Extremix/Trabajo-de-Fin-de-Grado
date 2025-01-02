package compiler

import (
	"fmt"
	"regexp"
	"strings"
)

func StoreVariables(code string) string {
	// Define a regular expression to find variable declarations
	varDeclarationRegex := regexp.MustCompile(`(?m)(int|float|double|char|bool|void|char\*|int\[\d*\]|float\[\d*\]|double\[\d*\])\s+([a-zA-Z_][a-zA-Z0-9_]*)(\s*=\s*[^;]*)?;`)

	// This will hold the modified code
	var modifiedCode string

	// Define the constant parts that will be injected for each variable
	// Add the function call for variable registration
	const addVarToJsonTemplate = `    addVariableToJson(root, "%s", &%s, TYPE_%s, 0);`

	// Loop through all matches (variable declarations)
	matches := varDeclarationRegex.FindAllStringSubmatch(code, -1)

	for _, match := range matches {
		varType := match[1]
		varName := match[2]
		modifiedCode = match[0]
		// Determine the correct type constant for the variable (in uppercase)
		varTypeConstant := ""
		switch varType {
		case "int":
			varTypeConstant = "INT"
		case "float":
			varTypeConstant = "FLOAT"
		case "double":
			varTypeConstant = "DOUBLE"
		case "char":
			varTypeConstant = "CHAR"
		case "bool":
			varTypeConstant = "BOOL"
		case "char*":
			varTypeConstant = "STRING"
		case "int[]":
			varTypeConstant = "ARRAY_INT"
		case "float[]":
			varTypeConstant = "ARRAY_FLOAT"
		case "double[]":
			varTypeConstant = "ARRAY_DOUBLE"
		default:
			varTypeConstant = "UNKNOWN"
		}

		// Create the addVariableToJson call
		addVarCall := fmt.Sprintf(addVarToJsonTemplate, varName, varName, varTypeConstant)

		// Append the new variable declaration and addVariableToJson call to the modified code
		modifiedCode += addVarCall + "\n"
		fmt.Println("Este es el código modificado", modifiedCode)
	}

	// Return the modified code with the injections
	return modifiedCode + code
}

func JsonManagement(code string) string {
	const (
		// Código para generar el objeto JSON al inicio del main
		GenerateObjectJSON = `const char* filename = "variables.json";

cJSON* root = cJSON_CreateObject();
if (!root) {
	fprintf(stderr, "Error: No se pudo crear el objeto JSON raíz.\n");
	return EXIT_FAILURE;
	}
	`

		// Código para escribir y eliminar el JSON al final del main
		WriteDeleteJSON = `
	writeJsonToFile(filename, root);
	cJSON_Delete(root);
	`
	)

	// Expresión regular para identificar el cuerpo del main
	mainBodyRegex := regexp.MustCompile(`(?s)int\s+main\s*\([^)]*\)\s*{(.*)}`)

	// Buscar el cuerpo del main
	matches := mainBodyRegex.FindStringSubmatch(code)
	if len(matches) != 2 {
		fmt.Println("Error: No se encontró el cuerpo del main.")
		return code
	}

	// Extraer el código dentro del main
	mainBody := matches[1]

	// Modificar el código del main
	modifiedMainBody := strings.TrimSpace(GenerateObjectJSON) + "\n" +
		strings.TrimSpace(mainBody) + "\n" +
		strings.TrimSpace(WriteDeleteJSON)

	// Reemplazar el cuerpo del main en el código original
	code = mainBodyRegex.ReplaceAllString(code, fmt.Sprintf("int main() {\n%s\n}", modifiedMainBody))

	return code
}

func InyectCode(code string) string {

	// Agregar el header al código
	code = "#include \"store_state.h\"\n" + code

	// Inyectar almacenamiento de variables en el código
	code = StoreVariables(code)

	// Manejar la gestión del JSON
	code = JsonManagement(code)

	fmt.Println(code)

	return code
}
