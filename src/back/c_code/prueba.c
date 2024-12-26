#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <cjson/cJSON.h>
#include "store_state.h"

int main() {
    const char* filename = "variables.json";

    // Crear el objeto JSON raíz
    cJSON* root = cJSON_CreateObject();
    if (!root) {
        fprintf(stderr, "Error: No se pudo crear el objeto JSON raíz.\n");
        return EXIT_FAILURE;
    }

    // Variables de ejemplo
    int myInt = 42;
    float myFloat = 3.14f;
    double myDouble = 2.7182818284;
    char myChar = 'A';
    char* myString = "Hola, mundo";
    int myBool = 1;  // true
    int* myPointer = &myInt;
    int myIntArray[] = { 1, 2, 3, 4, 5 };
    float myFloatArray[] = { 1.1, 2.2, 3.3 };
    double myDoubleArray[] = { 1.11, 2.22, 3.33 };

    // Agregar variables al JSON
    addVariableToJson(root, "mi_entero", &myInt, TYPE_INT, 0);
    addVariableToJson(root, "mi_flotante", &myFloat, TYPE_FLOAT, 0);
    addVariableToJson(root, "mi_doble", &myDouble, TYPE_DOUBLE, 0);
    addVariableToJson(root, "mi_caracter", &myChar, TYPE_CHAR, 0);
    addVariableToJson(root, "mi_cadena", myString, TYPE_STRING, 0);
    addVariableToJson(root, "mi_booleano", &myBool, TYPE_BOOL, 0);
    addVariableToJson(root, "mi_puntero", myPointer, TYPE_POINTER, 0);
    addVariableToJson(root, "mi_arreglo_entero", myIntArray, TYPE_ARRAY_INT, sizeof(myIntArray) / sizeof(myIntArray[0]));
    addVariableToJson(root, "mi_arreglo_flotante", myFloatArray, TYPE_ARRAY_FLOAT, sizeof(myFloatArray) / sizeof(myFloatArray[0]));
    addVariableToJson(root, "mi_arreglo_doble", myDoubleArray, TYPE_ARRAY_DOUBLE, sizeof(myDoubleArray) / sizeof(myDoubleArray[0]));

    // Escribir el JSON en un archivo
    writeJsonToFile(filename, root);

    // Limpiar la memoria
    cJSON_Delete(root);

    printf("Variables guardadas en %s\n", filename);

    return 0;
}
