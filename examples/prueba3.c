#include <stdio.h>
#include <pthread.h>
#include <unistd.h>

void funcion1() {
    printf("Entrando en funcion1\n");
    sleep(0.5);
    printf("Saliendo de funcion1\n");
}

void funcion2() {
    printf("Entrando en funcion2\n");
    sleep(0.5);
    printf("Saliendo de funcion2\n");
}

void * hilo_funcion(void *arg) {
    printf("Hilo secundario ejecutándose\n");
    int a = 12;
    printf("Hilo secundario finalizado\n");
    return NULL;
}

int main() {
    pthread_t hilo;
    
    printf("Creando hilo secundario\n");
    pthread_create(&hilo, NULL, hilo_funcion, NULL);
    
    funcion1();
    funcion2();
    
    pthread_join(hilo, NULL);
    printf("Hilo secundario terminado\n");
    
    return 0;
}
