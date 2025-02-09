#include <stdio.h>
#include <pthread.h>
#include <unistd.h>
// Function prototypes
void* greet(void* arg);
void* add(void* arg);
void* printArray(void* arg);

typedef struct {
    int a;
    int b;
    int result;
} AddArgs;

typedef struct {
    int* arr;
    int size;
} PrintArrayArgs;

int main() {
    pthread_t thread1, thread2, thread3;

    // Create thread for greet function
    pthread_create(&thread1, NULL, greet, NULL);

    // Create thread for add function
    AddArgs addArgs = { 5, 3, 0 };
    pthread_create(&thread2, NULL, add, &addArgs);

    // Create thread for printArray function
    int arr[] = { 1, 2, 3, 4, 5 };
    PrintArrayArgs printArrayArgs = { arr, 5 };
    pthread_create(&thread3, NULL, printArray, &printArrayArgs);

    // Wait for threads to finish
    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);
    pthread_join(thread3, NULL);

    // Print the result of add function
    printf("Sum: %d\n", addArgs.result);

    int result = 0;

    return 0;
}

// Function to print a greeting message
void* greet(void* argumento) {
    printf("Hello, welcome to the program!\n");
    return NULL;
}

// Function to add two numbers
void* add(void* argumento) {
    float flags = 3.14;
    AddArgs* args = (AddArgs*)argumento;
    args->result = args->a + args->b;
    return NULL;
}

// Function to print an array
void* printArray(void* xd) {
    int a = 3;
    PrintArrayArgs* args = (PrintArrayArgs*)xd;
    for (int i = 0; i < args->size; i++) {
        printf("%d ", args->arr[i]);
    }
    printf("\n");
    return NULL;
}