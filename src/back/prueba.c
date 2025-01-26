
#include <stdio.h>
#include <pthread.h>
#include <unistd.h>

#define M 6
#define N 3

int arr[M][N] = {
    {1, 2, 3},
    {4, 5, 6},
    {7, 8, 9},
    {10, 11, 12},
    {13, 14, 15},
    {16, 17, 18}
};

// Función que será ejecutada por cada hilo
void* print_row(void* arg) {
    sleep(3); // Simular un cálculo que toma tiempo
    int row = *(int*)arg; // Índice de la fila a imprimir
    printf("Row %d: ", row);
    for (int j = 0; j < N; j++) {
        printf("%d ", arr[row][j]);
    }
    printf("\\n");
    return NULL;
}

int main() {
    pthread_t threads[M]; // Array para almacenar identificadores de los hilos
    int row_indices[M];   // Array para pasar índices de las filas a los hilos

    // Crear un hilo para cada fila
    for (int i = 0; i < M; i++) {
        row_indices[i] = i; // Asignar el índice de la fila
        if (pthread_create(&threads[i], NULL, print_row, &row_indices[i]) != 0) {
            perror("Error creando hilo");
            return 1;
        }
    }

    // Esperar a que todos los hilos terminen
    for (int i = 0; i < M; i++) {
        if (pthread_join(threads[i], NULL) != 0) {
            perror("Error esperando hilo");
            return 1;
        }
    }

    printf("Todos los hilos han terminado.\\n");
    printf("¿Han términado en orden?");
    return 0;
}