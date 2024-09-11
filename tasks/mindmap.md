# Diseño de Herramienta

## Editor de código

### Escribir Y Borrar Código

### Shortcuts (Copiar, Pegar, Cortar,...)

### Lenguajes

#### En un principio solo C

##### Resaltado de sintaxis

### Botón Compilación

### Botón Ejecución

## Planificación de Procesos

### Selección del Tipo de Planificación

#### ¿Elegir a través de un Desplegable?

#### Cambiar argumentos de la Planificación si es necesario (quantum)

### Mostrar de forma visual cuál es el tipo de planificación actual

## Ejecución

### Ejecutar todo el código de forma directa

### Ejecución paso a paso

#### Propuestas de ejecución paso a paso

##### Condiciones de Parada

Permite visualizar el estado de todos los hilos dada una condición (un hilo accede a un lock, cierto hilo toma un valor en una variable)

##### Parada por Intervalos

Las pausas para ver el estado de los hilos ocurre cada un cierto interavalo de tiempo personalizable

##### Líneas temporales

Permite visualizar en líneas temporales qué ha hecho cada hilo en su propia memoria y cómo ha interactuado con la memoria compartida

##### Planificación Personalizada (Secuencialización del Código por el Usuario)

Esta planificación permite a través de la ejecución paso a paso decidir qué hilo avanza, es decir tener una previsualización de cuál será la siguiente sentencia a ejecutar y decidir qué hilo será el que se ejecute.

## Análisis de Condiciones de Carrera y Secciones Críticas

> Faltan cosas en este apartado y el código ensamblador no me convence

### Compilación/Traducción del código a código ensamblador

#### Durante Ejecución Paso a Paso

##### Resaltado de sentencia ejecutando en el momento y sentencia a ejecutar

Esto permite ver y comprender a bajo nivel qué es lo que puede estar generando la condición de carrera

## Visualización del estado del sistema

### Propuestas de visualización

#### Visualización de la memoria del sistema en forma de pila de memoria y enfoque en la memoria de cada pila de memoria de cada hilo

#### Visualización por pestañas de variables globales y cada uno de los hilos

##### Modificación del valor de cada variable
