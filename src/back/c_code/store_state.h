#ifndef STORE_STATE_H
#define STORE_STATE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <cjson/cJSON.h>

// Enumeración para identificar los tipos de variables
typedef enum {
    TYPE_INT,
    TYPE_FLOAT,
    TYPE_DOUBLE,
    TYPE_CHAR,
    TYPE_STRING,  // char*
    TYPE_BOOL,
    TYPE_POINTER,
    TYPE_ARRAY_INT,
    TYPE_ARRAY_FLOAT,
    TYPE_ARRAY_DOUBLE,
    TYPE_UNKNOWN
} VariableType;


// Función para agregar una variable al JSON
void addVariableToJson(cJSON* root, const char* varName, void* value, VariableType type, size_t arraySize);

#define ADD_VARIABLE_TO_JSON(root, varName, value, type) addVariableToJson(root, varName, &value, type, 0)

void writeJsonToFile(const char* filename, cJSON* root);

#endif