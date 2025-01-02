#include "store_state.h"

void addVariableToJson(cJSON* root, const char* varName, void* value, VariableType type, size_t arraySize) {
    switch (type) {
    case TYPE_INT:
        cJSON_AddNumberToObject(root, varName, *(int*)value);
        break;
    case TYPE_FLOAT:
        cJSON_AddNumberToObject(root, varName, *(float*)value);
        break;
    case TYPE_DOUBLE:
        cJSON_AddNumberToObject(root, varName, *(double*)value);
        break;
    case TYPE_CHAR:
        cJSON_AddStringToObject(root, varName, (char[]) { *(char*)value, '\0' });
        break;
    case TYPE_STRING:
        if (value != NULL) {
            cJSON_AddStringToObject(root, varName, (char*)value);
        }
        else {
            cJSON_AddNullToObject(root, varName);
        }
        break;
    case TYPE_BOOL:
        cJSON_AddBoolToObject(root, varName, *(int*)value);
        break;
    case TYPE_POINTER:
        if (value != NULL) {
            char pointerStr[20];
            snprintf(pointerStr, sizeof(pointerStr), "%p", value);
            cJSON_AddStringToObject(root, varName, pointerStr);
        }
        else {
            cJSON_AddNullToObject(root, varName);
        }
        break;
    case TYPE_ARRAY_INT: {
        cJSON* array = cJSON_CreateArray();
        if (!array) break;
        int* intArray = (int*)value;
        for (size_t i = 0; i < arraySize; i++) {
            cJSON_AddItemToArray(array, cJSON_CreateNumber(intArray[i]));
        }
        cJSON_AddItemToObject(root, varName, array);
        break;
    }
    case TYPE_ARRAY_FLOAT: {
        cJSON* array = cJSON_CreateArray();
        if (!array) break;
        float* floatArray = (float*)value;
        for (size_t i = 0; i < arraySize; i++) {
            cJSON_AddItemToArray(array, cJSON_CreateNumber(floatArray[i]));
        }
        cJSON_AddItemToObject(root, varName, array);
        break;
    }
    case TYPE_ARRAY_DOUBLE: {
        cJSON* array = cJSON_CreateArray();
        if (!array) break;
        double* doubleArray = (double*)value;
        for (size_t i = 0; i < arraySize; i++) {
            cJSON_AddItemToArray(array, cJSON_CreateNumber(doubleArray[i]));
        }
        cJSON_AddItemToObject(root, varName, array);
        break;
    }
    default:
        cJSON_AddStringToObject(root, varName, "Unsupported type");
        break;
    }
}

// Función para escribir el JSON en un archivo
void writeJsonToFile(const char* filename, cJSON* root) {
    char* jsonString = cJSON_Print(root);
    if (!jsonString) {
        fprintf(stderr, "Error: No se pudo generar el JSON.\n");
        return;
    }

    FILE* file = fopen(filename, "w");
    if (!file) {
        fprintf(stderr, "Error: No se pudo abrir el archivo %s.\n", filename);
        free(jsonString);
        return;
    }

    fprintf(file, "%s\n", jsonString);
    fclose(file);
    free(jsonString);
}